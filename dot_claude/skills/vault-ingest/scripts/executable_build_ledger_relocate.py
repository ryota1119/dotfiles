#!/usr/bin/env python3
"""退避後の `origin.locator` を `inbox/` から `.raw/` へ書き換える bundle を組む（Tx-B）。

`inbox/` から消したファイルを指す `locator` は死ぬ。ledger の存在意義は出所が追える
ことなので、実在しないパスを残さない。

**`origin.kind` が `file` のものだけを書き換える。** `url` のエントリは inbox に依存して
いないので触らない。

**`locator` 以外のキーを1つも変えない。** `content_sha256` / `retrieved_at` /
`refresh_due` / `pages` / `title` / `authority` / `content_kind` / `review_status` は
既存値をそのまま維持する。差分キー集合が `{origin.locator}`（と `generated_at`）だけに
なることを、このスクリプト自身が検算する。

Tx-B を Tx-C（削除）より前に置くこと。Tx-B が失敗しても inbox に原本が残っていれば
状況を元に戻せる。逆順だと「原本を消したが locator が古いまま」という中途半端な状態が残る。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

BUNDLE_SCHEMA = "vaultctl.bundle.v1"
QUEUE_SCHEMA = "vault-ingest.queue.v1"
LEDGER_RELPATH = "wiki/meta/ledgers/source-ledger.json"


def _fail(message: str) -> None:
    sys.exit(f"error: {message}")


def plan_relocations(queue: dict[str, Any], ledger: dict[str, Any],
                     classifications: set[str]) -> dict[str, str]:
    """書き換える {source_id: 新 locator} を決める。"""
    sources = ledger["sources"]
    out: dict[str, str] = {}
    for item in queue["items"]:
        if item["classification"] not in classifications:
            continue
        for source_id in item["ledger_source_ids"]:
            entry = sources.get(source_id)
            if entry is None:
                _fail(f"ledger に source_id がありません: {source_id}")
            origin = entry.get("origin") or {}
            if origin.get("kind") != "file":
                continue  # url 由来は inbox に依存していないので触らない
            locator = str(origin.get("locator", ""))
            if not locator.startswith("inbox/"):
                continue  # 既に .raw/ を指している、または別形式
            out[source_id] = item["raw_target"]
    return out


def rewrite(ledger: dict[str, Any], relocations: dict[str, str],
            generated_at: str | None) -> dict[str, Any]:
    """locator だけを差し替えた新しい ledger を返す。他のキーは触らない。"""
    new = json.loads(json.dumps(ledger))  # 深いコピー
    for source_id, locator in relocations.items():
        new["sources"][source_id]["origin"]["locator"] = locator
    if generated_at:
        new["generated_at"] = generated_at
    return new


def diff_keys(old: dict[str, Any], new: dict[str, Any]) -> list[str]:
    """変わったキーを `sources.<id>.origin.locator` の形で列挙する。"""
    changed: list[str] = []
    for key in sorted(set(old) | set(new)):
        if key == "sources":
            continue
        if old.get(key) != new.get(key):
            changed.append(key)
    old_sources, new_sources = old.get("sources", {}), new.get("sources", {})
    for source_id in sorted(set(old_sources) | set(new_sources)):
        o, n = old_sources.get(source_id), new_sources.get(source_id)
        if o == n:
            continue
        if not isinstance(o, dict) or not isinstance(n, dict):
            changed.append(f"sources.{source_id}")
            continue
        for key in sorted(set(o) | set(n)):
            if o.get(key) == n.get(key):
                continue
            if key == "origin" and isinstance(o.get(key), dict) and isinstance(n.get(key), dict):
                for sub in sorted(set(o[key]) | set(n[key])):
                    if o[key].get(sub) != n[key].get(sub):
                        changed.append(f"sources.{source_id}.origin.{sub}")
            else:
                changed.append(f"sources.{source_id}.{key}")
    return changed


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--queue", required=True)
    ap.add_argument("--out", required=True, help="bundle.json の出力先（絶対パス）")
    ap.add_argument("--staging", required=True, help="新しい ledger を置く staging ディレクトリ（絶対パス）")
    ap.add_argument("--operation-id", required=True)
    ap.add_argument("--classification", default="reconcile")
    ap.add_argument("--generated-at", help="ledger の generated_at を更新する場合の値（YYYY-MM-DD）")
    args = ap.parse_args(argv)

    out, staging = Path(args.out), Path(args.staging)
    if not out.is_absolute() or not staging.is_absolute():
        _fail("--out と --staging は絶対パスで指定してください")

    queue = json.loads(Path(args.queue).read_text(encoding="utf-8"))
    if queue.get("schema") != QUEUE_SCHEMA:
        _fail("queue.json の schema が違います")
    if queue["counts"]["inconsistent"]:
        _fail(f"不整合が {queue['counts']['inconsistent']} 件あります。解決してから実行してください")

    vault = Path(queue["vault"])
    ledger_path = vault / LEDGER_RELPATH
    old = json.loads(ledger_path.read_text(encoding="utf-8"))

    wanted = {c.strip() for c in args.classification.split(",") if c.strip()}
    relocations = plan_relocations(queue, old, wanted)
    if not relocations:
        print("書き換える locator がありません（すべて .raw/ を指しているか、url 由来です）")
        return 0

    new = rewrite(old, relocations, args.generated_at)

    changed = diff_keys(old, new)
    expected = {f"sources.{sid}.origin.locator" for sid in relocations}
    if args.generated_at:
        expected.add("generated_at")
    unexpected = sorted(set(changed) - expected)
    if unexpected:
        _fail(f"意図しないキーが変わっています: {unexpected}")

    staging.mkdir(parents=True, exist_ok=True)
    staged = staging / "source-ledger.json"
    # 元ファイルと同じ書式で書く（sort_keys=False, indent=2）。差分を locator だけに保つ。
    staged.write_text(json.dumps(new, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
                      encoding="utf-8")

    bundle = {
        "schema": BUNDLE_SCHEMA,
        "operation_id": args.operation_id,
        "operation_type": "ingest",
        "writes": [{"path": LEDGER_RELPATH, "mode": "replace",
                    "content_file": str(staged.resolve())}],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f"locator の書き換え: {len(relocations)} 件（writes は ledger の replace 1件）")
    for source_id, locator in sorted(relocations.items()):
        print(f"  {source_id}")
        print(f"    {old['sources'][source_id]['origin']['locator']}")
        print(f"    → {locator}")
    print(f"変更されたキー: {sorted(changed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
