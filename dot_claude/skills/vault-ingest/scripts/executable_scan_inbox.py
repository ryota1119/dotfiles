#!/usr/bin/env python3
"""`inbox/` を走査して分類し、queue.json を書く（T14-1）。

読み取り専用。vault へ1バイトも書かない。分類規則は計画3.1 に従う。

**不整合は自動で吸収しない。** 「たぶんこうだろう」で ledger を書いたり原本を
消したりする経路を作らないため、hash 不一致・ページ欠落・ledger 未参照は
いずれも `inconsistent` にして非0で終了する。

macOS の Unicode 正規化に注意する。`.raw/.manifest.json` のキーは NFC、
`os.listdir` が返す名前は NFD になりうる。**突合は NFC で行い、bundle の
`path` にはファイルシステムから読んだ生の名前を使う。** 素朴に集合比較すると
処理済みを未処理と誤判定して二重にページを作る。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any

QUEUE_SCHEMA = "vault-ingest.queue.v1"
MANIFEST_RELPATH = ".raw/.manifest.json"
SOURCE_LEDGER_RELPATH = "wiki/meta/ledgers/source-ledger.json"

EXIT_OK = 0
EXIT_INCONSISTENT = 1
EXIT_USAGE = 64

MEDIA_TYPES = {".md": "markdown", ".markdown": "markdown", ".pdf": "pdf"}


def nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _load_json(path: Path, label: str) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except OSError as exc:
        sys.exit(f"error: {label} を読めません: {exc}")
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {label} の JSON を解析できません: {exc.msg}")


def _manifest_sources(vault: Path) -> dict[str, dict[str, Any]]:
    """manifest の sources を「NFC 正規化した inbox 相対名」で引けるようにする。

    キーは `inbox/<name>` の形で入っている。接頭辞を落として比較する。
    """
    data = _load_json(vault / MANIFEST_RELPATH, ".raw/.manifest.json")
    if data is None:
        return {}
    sources = data.get("sources")
    if not isinstance(sources, dict):
        sys.exit("error: .manifest.json に sources がありません")
    out: dict[str, dict[str, Any]] = {}
    for key, value in sources.items():
        name = key[len("inbox/"):] if key.startswith("inbox/") else key
        out[nfc(name)] = value if isinstance(value, dict) else {}
    return out


def _ledger_index(vault: Path) -> dict[str, list[tuple[str, dict[str, Any]]]]:
    """source-ledger を「ページ相対パス → [(source_id, entry)]」で引けるようにする。"""
    data = _load_json(vault / SOURCE_LEDGER_RELPATH, "source-ledger.json")
    if data is None:
        return {}
    sources = data.get("sources", data)
    index: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for source_id, entry in sources.items():
        if not isinstance(entry, dict):
            continue
        for page in entry.get("pages", []) or []:
            index.setdefault(nfc(str(page)), []).append((source_id, entry))
    return index


def _media_type(name: str) -> str:
    return MEDIA_TYPES.get(Path(name).suffix.lower(), "other")


def classify(vault: Path, raw_name: str, manifest: dict[str, dict[str, Any]],
             ledger: dict[str, list[tuple[str, dict[str, Any]]]]) -> dict[str, Any]:
    """1ファイルを計画3.1 の規則で分類する。"""
    path = vault / "inbox" / raw_name
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    name_nfc = nfc(raw_name)
    item: dict[str, Any] = {
        "inbox_path": f"inbox/{raw_name}",
        "inbox_path_nfc": f"inbox/{name_nfc}",
        "abs_path": str(path.resolve()),
        "bytes": len(data),
        "sha256": digest,
        "media_type": _media_type(raw_name),
        "classification": "ingest",
        "manifest_hash_match": None,
        "pages_created": [],
        "pages_exist": [],
        "ledger_source_ids": [],
        "ledger_origin": None,
        "raw_target": f".raw/{raw_name}",
        "notes": [],
    }

    entry = manifest.get(name_nfc)
    if entry is None:
        item["notes"].append("manifest に無い（未処理）")
        return item

    item["manifest_hash_match"] = entry.get("hash") == digest
    pages = [str(p) for p in (entry.get("pages_created") or [])]
    item["pages_created"] = pages
    item["pages_exist"] = [(vault / p).is_file() for p in pages]

    source_ids: list[str] = []
    origin: dict[str, Any] | None = None
    for page in pages:
        for source_id, ledger_entry in ledger.get(nfc(page), []):
            if source_id not in source_ids:
                source_ids.append(source_id)
            if origin is None and isinstance(ledger_entry.get("origin"), dict):
                origin = ledger_entry["origin"]
    item["ledger_source_ids"] = source_ids
    item["ledger_origin"] = origin

    if not item["manifest_hash_match"]:
        item["classification"] = "inconsistent"
        item["notes"].append(
            "不整合A: manifest の hash と現ファイルが一致しない（取り込み後に原本が書き換わった）")
        return item
    if not pages or not all(item["pages_exist"]):
        item["classification"] = "inconsistent"
        item["notes"].append("不整合B: pages_created のページが実在しない")
        return item
    if not source_ids:
        item["classification"] = "inconsistent"
        item["notes"].append(
            "不整合C: ページが source-ledger から参照されていない（規則10-a 相当）。"
            "ledger 登録は Phase 3 の担当であり、ここでは埋めない")
        return item

    item["classification"] = "reconcile"
    return item


def scan(vault: Path, scanned_at: str) -> dict[str, Any]:
    inbox = vault / "inbox"
    if not inbox.is_dir():
        sys.exit(f"error: inbox がありません: {inbox}")
    manifest = _manifest_sources(vault)
    ledger = _ledger_index(vault)
    names = sorted(
        (p.name for p in inbox.iterdir() if p.is_file() and not p.name.startswith(".")),
        key=nfc,
    )
    items = [classify(vault, name, manifest, ledger) for name in names]
    counts = {
        "ingest": sum(1 for i in items if i["classification"] == "ingest"),
        "reconcile": sum(1 for i in items if i["classification"] == "reconcile"),
        "inconsistent": sum(1 for i in items if i["classification"] == "inconsistent"),
    }
    return {
        "schema": QUEUE_SCHEMA,
        "vault": str(vault),
        "scanned_at": scanned_at,
        "items": items,
        "counts": counts,
    }


def render(queue: dict[str, Any]) -> str:
    counts = queue["counts"]
    lines = [
        f"inbox {len(queue['items'])} 件 — "
        f"ingest {counts['ingest']} / reconcile {counts['reconcile']} / "
        f"inconsistent {counts['inconsistent']}",
        "",
    ]
    for group, label in (("inconsistent", "不整合（停止して報告する）"),
                         ("ingest", "未処理（ingest モード）"),
                         ("reconcile", "処理済み・原本のみ残存（reconcile モード）")):
        picked = [i for i in queue["items"] if i["classification"] == group]
        lines.append(f"## {label} — {len(picked)}件")
        if not picked:
            lines.append("  （なし）")
        for item in picked:
            name = item["inbox_path"][len("inbox/"):]
            lines.append(f"  - {name}  [{item['media_type']}, {item['bytes']} bytes]")
            for page in item["pages_created"]:
                lines.append(f"      → {page}")
            for note in item["notes"]:
                lines.append(f"      ! {note}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", default=str(Path.home() / "Workspace/exocortex"),
                    help="vault のルート（既定: ~/Workspace/exocortex）")
    ap.add_argument("--out", help="queue.json の出力先（絶対パス）")
    ap.add_argument("--scanned-at", default="",
                    help="queue.json に記録する時刻。省略時は空文字（再現性のため既定で埋めない）")
    args = ap.parse_args(argv)

    vault = Path(args.vault).expanduser()
    if not (vault / "wiki").is_dir() or not (vault / "inbox").is_dir():
        sys.exit(EXIT_USAGE)

    queue = scan(vault, args.scanned_at)
    if args.out:
        out = Path(args.out)
        if not out.is_absolute():
            sys.exit("error: --out は絶対パスで指定してください")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(queue, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                       encoding="utf-8")
    sys.stdout.write(render(queue))
    return EXIT_INCONSISTENT if queue["counts"]["inconsistent"] else EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
