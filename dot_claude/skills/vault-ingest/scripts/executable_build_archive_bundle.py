#!/usr/bin/env python3
"""queue.json から `.raw/` への原本退避 bundle を組む（T14-2）。

**create しか出さない。** delete は別トランザクション（T14-3）で扱う。退避が完全に
信用できる状態を作ってから削除するため、ここで両者を混ぜない。

`content_file` は inbox の実ファイルそのものの絶対パスを指す。コピーを作らない。
規約4.1 は「絶対パスかつ実在するファイル」しか要求せず、vault 内のファイルを読むだけ
なので規約5.1（vault 内に作業ファイルを置かない）にも反しない。

`.raw/` の名前は inbox の名前をそのまま使う。**リネームしない。** 同名衝突は
`plan` の時点で「create 対象が既に存在する」で落ちる。これは「同じ原本を二度退避
しようとしている」という事実なので、連番を付けて回避しない。
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

EXIT_OK = 0
EXIT_ERROR = 1


def _fail(message: str) -> None:
    sys.exit(f"error: {message}")


def _load_queue(path: Path) -> dict[str, Any]:
    try:
        queue = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        _fail(f"queue.json を読めません: {exc}")
    except json.JSONDecodeError as exc:
        _fail(f"queue.json の JSON を解析できません: {exc.msg}")
    if queue.get("schema") != QUEUE_SCHEMA:
        _fail(f"queue.json の schema が {QUEUE_SCHEMA} ではありません: {queue.get('schema')!r}")
    return queue


def select_items(queue: dict[str, Any], classifications: set[str]) -> list[dict[str, Any]]:
    """退避対象を選ぶ。inconsistent が1件でもあれば止める。"""
    if queue["counts"]["inconsistent"]:
        _fail(
            f"不整合が {queue['counts']['inconsistent']} 件あります。"
            "分類を解決してから退避してください（不整合を自動で吸収しない）"
        )
    return [i for i in queue["items"] if i["classification"] in classifications]


def build(queue: dict[str, Any], items: list[dict[str, Any]], operation_id: str) -> dict[str, Any]:
    vault = Path(queue["vault"])
    writes = []
    for item in items:
        source = Path(item["abs_path"])
        if not source.is_file():
            _fail(f"退避元が実在しません: {source}")
        target = vault / item["raw_target"]
        if target.exists():
            _fail(
                f"退避先が既に存在します: {item['raw_target']}\n"
                "  同じ原本を二度退避しようとしています。連番を付けて回避せず、"
                "なぜ二度目なのかを確認してください"
            )
        writes.append({
            "path": item["raw_target"],
            "mode": "create",
            "content_file": str(source.resolve()),
        })
    if not writes:
        _fail("退避対象が0件です")
    return {
        "schema": BUNDLE_SCHEMA,
        "operation_id": operation_id,
        "operation_type": "ingest",
        "writes": writes,
    }


def snapshot(items: list[dict[str, Any]]) -> dict[str, str]:
    """plan と apply の間に inbox が変わっていないかを見るための実測ハッシュ。

    queue.json に記録した値ではなく、その場でファイルを読み直して計算する。
    """
    out: dict[str, str] = {}
    for item in items:
        path = Path(item["abs_path"])
        out[item["inbox_path"]] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queue", required=True, help="scan_inbox.py が書いた queue.json")
    ap.add_argument("--out", required=True, help="bundle.json の出力先（絶対パス）")
    ap.add_argument("--operation-id", required=True,
                    help="ingest-<YYYYMMDDTHHMMSS>-<slug>")
    ap.add_argument("--classification", default="reconcile",
                    help="退避対象の分類。カンマ区切り（既定: reconcile）")
    ap.add_argument("--snapshot", help="退避元の実測ハッシュの出力先（apply 直前の再照合用）")
    args = ap.parse_args(argv)

    out = Path(args.out)
    if not out.is_absolute():
        _fail("--out は絶対パスで指定してください")

    queue = _load_queue(Path(args.queue))
    wanted = {c.strip() for c in args.classification.split(",") if c.strip()}
    items = select_items(queue, wanted)
    bundle = build(queue, items, args.operation_id)

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.snapshot:
        snap = Path(args.snapshot)
        if not snap.is_absolute():
            _fail("--snapshot は絶対パスで指定してください")
        snap.write_text(
            json.dumps(snapshot(items), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8")

    print(f"退避 bundle: create {len(bundle['writes'])} 件（delete 0 件）")
    for write in bundle["writes"]:
        print(f"  {write['path']}")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
