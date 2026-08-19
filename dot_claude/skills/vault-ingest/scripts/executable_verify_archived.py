#!/usr/bin/env python3
"""退避が完了していることを検証し、delete bundle を組む（T14-3）。

**この skill で最も危険な処理。** exocortex は git 管理下になく、`mode=delete` の復旧は
journal の `backups/NNNN.original` か Google Drive の版履歴しかない。

計画のゲート G1〜G5 を機械化する。要点は2つ。

1. **queue.json に記録したハッシュを信じない。** 記録から時間が経っており、その間に
   Google Drive の同期や Obsidian の保存が走りうる。`.raw/` と `inbox/` の両方を
   その場で全読みして SHA256 を計算し直す。
2. **1件でも不一致があれば全件中止する。** 「一致した分だけ消す」をしない。部分的に
   消すと、どこまで消えたかを後から追うのが難しくなる。

delete bundle は退避 bundle と必ず別トランザクションにする。同一にすると
(1) apply 直前の検証が原理的にできない（plan 時点では staging しか無い）、
(2) 失敗時の自動ロールバックで `.raw/` の create まで巻き戻り退避のやり直しになる、
(3) 「delete 以外が0件か」という単純な検査ができなくなる。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

BUNDLE_SCHEMA = "vaultctl.bundle.v1"
QUEUE_SCHEMA = "vault-ingest.queue.v1"
CONFLICT_MARKERS = (" (1)", " (2)", " (3)", "のコピー", "conflicted copy", "- コピー")

EXIT_OK = 0
EXIT_BLOCKED = 1


def _sha256(path: Path) -> str:
    """キャッシュを使わず、その場で全読みして計算する。"""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _load_queue(path: Path) -> dict[str, Any]:
    queue = json.loads(path.read_text(encoding="utf-8"))
    if queue.get("schema") != QUEUE_SCHEMA:
        sys.exit(f"error: queue.json の schema が {QUEUE_SCHEMA} ではありません")
    return queue


def check_conflict_copies(vault: Path) -> list[str]:
    """`.raw/` に Google Drive の競合コピーが無いか見る。あれば同期完了を待つ。"""
    raw = vault / ".raw"
    if not raw.is_dir():
        return []
    return sorted(
        p.name for p in raw.iterdir()
        if p.is_file() and any(marker in p.name for marker in CONFLICT_MARKERS)
    )


def verify(vault: Path, items: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """G2 を実測で確認する。戻り値は (検証を通った item, 失敗理由の一覧)。"""
    ok: list[dict[str, Any]] = []
    errors: list[str] = []
    for item in items:
        name = item["inbox_path"][len("inbox/"):]
        inbox_path = Path(item["abs_path"])
        raw_path = vault / item["raw_target"]

        if not raw_path.is_file():
            errors.append(f"{name}: 退避先が実在しません（{item['raw_target']}）")
            continue
        if not inbox_path.is_file():
            errors.append(f"{name}: 削除元が実在しません（既に消えている？）")
            continue

        raw_size = raw_path.stat().st_size
        inbox_size = inbox_path.stat().st_size
        raw_hash = _sha256(raw_path)
        inbox_hash = _sha256(inbox_path)

        if raw_hash != inbox_hash:
            errors.append(
                f"{name}: SHA256 が一致しません\n"
                f"    .raw : {raw_hash}\n"
                f"    inbox: {inbox_hash}")
            continue
        # 同一ハッシュでサイズ違いは起こり得ないが、読み取りバグを検出する冗長チェック。
        if raw_size != inbox_size:
            errors.append(f"{name}: ハッシュは一致するがサイズが違う（{raw_size} != {inbox_size}）")
            continue
        ok.append(item)
    return ok, errors


def build_delete_bundle(items: list[dict[str, Any]], operation_id: str) -> dict[str, Any]:
    writes = [{"path": item["inbox_path"], "mode": "delete"} for item in items]
    assert all(w["mode"] == "delete" for w in writes)
    assert all(w["path"].startswith("inbox/") for w in writes)
    return {
        "schema": BUNDLE_SCHEMA,
        "operation_id": operation_id,
        "operation_type": "ingest",
        "writes": writes,
    }


def render_presentation(vault: Path, items: list[dict[str, Any]], operation_id: str) -> str:
    """規約3.2の2 に従い、削除対象を1件ずつ全件列挙する。件数だけの要約にしない。"""
    lines = [
        f"### 削除対象（{len(items)}件） — **すべて mode=delete**",
        "",
        "| # | **削除する path** | 退避先 | SHA256 |",
        "| - | --- | --- | --- |",
    ]
    for index, item in enumerate(items, start=1):
        digest = _sha256(vault / item["raw_target"])
        lines.append(
            f"| {index} | **{item['inbox_path']}** | {item['raw_target']} | "
            f"`{digest[:12]}…` 一致確認済み |")
    lines += [
        "",
        "復旧手段: exocortex は git 管理下にないため `git checkout` では戻せない。",
        "原本は次に退避される。",
        "",
        "```",
        f"~/.local/state/vaultctl/<vault-id>/transactions/{operation_id}/backups/",
        "```",
        "",
        "加えて Google Drive の版履歴。",
    ]
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queue", required=True)
    ap.add_argument("--out", help="delete bundle の出力先（絶対パス）")
    ap.add_argument("--operation-id", help="--out を使うときは必須")
    ap.add_argument("--classification", default="reconcile")
    ap.add_argument("--presentation", help="承認提示ブロックの出力先（絶対パス）")
    args = ap.parse_args(argv)

    queue = _load_queue(Path(args.queue))
    vault = Path(queue["vault"])

    # G3: 不整合が残っていれば何も消さない。
    if queue["counts"]["inconsistent"]:
        print(f"[NG] G3 分類: 不整合が {queue['counts']['inconsistent']} 件残っています。"
              "削除しません")
        return EXIT_BLOCKED
    print("[OK] G3 分類: 不整合 0 件")

    wanted = {c.strip() for c in args.classification.split(",") if c.strip()}
    items = [i for i in queue["items"] if i["classification"] in wanted]
    if not items:
        print("[NG] 対象が0件です")
        return EXIT_BLOCKED

    conflicts = check_conflict_copies(vault)
    if conflicts:
        print(f"[NG] .raw/ に同期の競合コピーがあります: {conflicts}")
        print("     Google Drive の同期完了を待ってからやり直してください")
        return EXIT_BLOCKED
    print("[OK] .raw/ に競合コピーなし")

    ok, errors = verify(vault, items)
    if errors:
        print(f"[NG] G2 退避の検証: {len(errors)} 件が不一致。**全件について削除を中止します**")
        for message in errors:
            print(f"     - {message}")
        print("     一致した分だけ消す、はしません")
        return EXIT_BLOCKED
    print(f"[OK] G2 退避の検証: {len(ok)} 件すべてで .raw/ と inbox/ の SHA256 が一致")

    # G5: 件数が完全一致すること。
    if len(ok) != len(items):
        print(f"[NG] G5 件数照合: 対象 {len(items)} 件に対し検証通過 {len(ok)} 件")
        return EXIT_BLOCKED
    print(f"[OK] G5 件数照合: {len(items)} 件")

    if args.out:
        if not args.operation_id:
            sys.exit("error: --out を使うときは --operation-id が必要です")
        out = Path(args.out)
        if not out.is_absolute():
            sys.exit("error: --out は絶対パスで指定してください")
        bundle = build_delete_bundle(ok, args.operation_id)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[OK] delete bundle を書きました: {out}（delete {len(bundle['writes'])} 件）")

    if args.presentation:
        pres = Path(args.presentation)
        if not pres.is_absolute():
            sys.exit("error: --presentation は絶対パスで指定してください")
        pres.write_text(
            render_presentation(vault, ok, args.operation_id or "<operation_id>"),
            encoding="utf-8")
        print(f"[OK] 承認提示ブロックを書きました: {pres}")

    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
