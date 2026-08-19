#!/usr/bin/env python3
"""ingest トランザクション（Tx-2）を apply の前に機械検証する（T14-5〜T14-7）。

規約6.2 の検証に加えて、T14 固有の項目を見る。特に効くのは次の3つ。

1. **被リンク先がハブでないこと。** `check_orphans` はハブ5枚からのリンクを被リンクに
   数えないので、ハブに載せても規則5 は消えない。ハブを指定するのは「解消したつもりで
   解消していない」という最も気づきにくい失敗である。
2. **`content_file` が全件で絶対パスであること。** `ledger stage --staging-dir` に相対パスを
   渡すと `content_file` が相対になり、後続の `plan` が落ちる。規約10節が挙げる唯一の
   既知の罠なので、コードで確認する。
3. **ledger の `schema` 文字列が書き換わっていないこと。** 実 vault は
   `claude-obsidian.source-ledger.v1`、合成 vault は `vaultctl.source-ledger.v1` と値が違うので、
   固定値と比べずに**既存ファイルの値と一致するか**を見る。変わっていたら ledger のパスか
   経路が違う。
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

HUB_RELPATHS = {"wiki/index.md", "wiki/hot.md", "wiki/log.md",
                "wiki/dashboard.md", "wiki/overview.md"}
LEDGER_RELPATH = "wiki/meta/ledgers/source-ledger.json"
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-\d{4}-\d{2}$")
GENERATED_AT_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")


class Report:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.failed = False

    def check(self, ok: bool, label: str, detail: str = "") -> bool:
        self.lines.append(f"[{'OK' if ok else 'NG'}] {label}" + (f": {detail}" if detail else ""))
        if not ok:
            self.failed = True
        return ok

    def render(self) -> str:
        return "\n".join(self.lines) + "\n"


def _split(text: str) -> tuple[str, str]:
    m = re.match(r"^---\n(.*?\n)---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("frontmatter を解析できません")
    return m.group(1), m.group(2)


def _fm_value(fm: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}:\s*(.*)$", fm, re.M)
    return m.group(1).strip().strip('"') if m else None


def _fm_keys(fm: str) -> set[str]:
    return set(re.findall(r"^([A-Za-z_][A-Za-z0-9_]*):", fm, re.M))


def _slugs(vault: Path) -> set[str]:
    return {p.stem for p in (vault / "wiki").rglob("*.md")}


def _insert_only(old_body: str, new_body: str) -> tuple[bool, list[str], str]:
    ops = [o for o in difflib.SequenceMatcher(a=old_body.split("\n"), b=new_body.split("\n"),
                                              autojunk=False).get_opcodes() if o[0] != "equal"]
    if len(ops) != 1 or ops[0][0] != "insert":
        return False, [], f"差分が挿入1箇所でない（{[o[0] for o in ops] or '差分なし'}）"
    _t, _i1, _i2, j1, j2 = ops[0]
    return True, new_body.split("\n")[j1:j2], ""


def verify(vault: Path, plan: dict[str, Any]) -> Report:
    report = Report()
    writes = plan["writes"]
    creates = [w for w in writes if w["mode"] == "create"]
    replaces = [w for w in writes if w["mode"] == "replace"]
    deletes = [w for w in writes if w["mode"] == "delete"]

    report.check(not deletes, "delete が含まれていない",
                 "ingest の Tx-2 に delete は入らない（inbox の削除は Tx-3）")
    report.check(len(creates) == 1, "create が1件", f"{len(creates)} 件")
    readable = report.check(
        all(Path(w["content_file"]).is_absolute() for w in writes if w["mode"] != "delete"),
        "content_file が全件で絶対パス",
        "ledger stage --staging-dir に相対を渡すとここが落ちる（規約10節の既知の罠）")
    readable = report.check(
        all(Path(w["content_file"]).is_file() for w in writes if w["mode"] != "delete"),
        "content_file が全件で実在") and readable
    if not readable:
        # 内容を読めない以上、以降の検査は意味を持たない。ここで打ち切る。
        report.check(False, "以降の検査", "content_file を読めないため実施しない")
        return report

    paths = {w["path"] for w in writes}
    report.check("wiki/index.md" in paths, "index.md の replace がある（規則7 の先回り）")
    report.check(LEDGER_RELPATH in paths, "source-ledger の replace がある（規則10-a の先回り）")

    backlinks = sorted(paths - HUB_RELPATHS - {LEDGER_RELPATH} - {w["path"] for w in creates})
    report.check(len(backlinks) >= 1, "被リンク先の replace が1件以上ある（D-S1）", f"{backlinks}")
    report.check(all(b not in HUB_RELPATHS for b in backlinks),
                 "被リンク先にハブが含まれていない",
                 "ハブからのリンクは被リンクに数えられず、規則5 は解消しない")

    if not creates:
        return report
    create = creates[0]
    relpath = create["path"]
    text = Path(create["content_file"]).read_text(encoding="utf-8")
    try:
        fm, body = _split(text)
    except ValueError as exc:
        report.check(False, f"新規ページの frontmatter: {relpath}", str(exc))
        return report

    slug = Path(relpath).stem
    report.check(relpath.startswith("wiki/sources/"), "新規ページが wiki/sources/ 配下（規則3）", relpath)
    report.check(bool(SLUG_RE.match(slug)), "slug が <英数ハイフン>-<YYYY-MM> の形", slug)
    report.check(slug not in _slugs(vault), "slug が既存と衝突しない", slug)
    report.check(_fm_value(fm, "type") == "source", "type が source")
    report.check(_fm_value(fm, "status") == "developing",
                 "status が developing", "evergreen を skill が自分で付けない")
    report.check("## 出典" in body, "本文に ## 出典 がある", "取得日と原本の所在をここに書く")
    report.check(text.endswith("\n"), "末尾が改行で終わる（規則11）")

    existing = _slugs(vault) | {slug}
    unresolved = sorted({m.group(1).strip() for m in WIKILINK_RE.finditer(body)} - existing)
    report.check(not unresolved, "本文の wikilink がすべて実在（規則4 の先回り）", f"{unresolved}")

    empty = []
    heads: list[list[Any]] = []
    for line in body.split("\n"):
        m = HEADING_RE.match(line)
        if m:
            heads.append([len(m.group(1)), m.group(2).strip(), 0])
        elif line.strip() and heads:
            heads[-1][2] += 1
    for i, (level, title, count) in enumerate(heads):
        nxt = heads[i + 1] if i + 1 < len(heads) else None
        if count == 0 and not (nxt and nxt[0] > level):
            empty.append(title)
    report.check(not empty, "見出しだけの節が無い（規則6 の先回り）", f"{empty}")

    for write in replaces:
        rel = write["path"]
        old_text = (vault / rel).read_text(encoding="utf-8")
        new_text = Path(write["content_file"]).read_text(encoding="utf-8")
        if rel == LEDGER_RELPATH:
            old, new = json.loads(old_text), json.loads(new_text)
            report.check(new.get("schema") == old.get("schema"),
                         "ledger の schema が書き換わっていない",
                         f"{old.get('schema')!r} → {new.get('schema')!r}")
            report.check(set(old["sources"]) <= set(new["sources"]),
                         "既存の source エントリが1件も欠けていない",
                         f"{len(old['sources'])} → {len(new['sources'])}")
            added = sorted(set(new["sources"]) - set(old["sources"]))
            report.check(len(added) == 1, "追加された source_id が1件", f"{added}")
            report.check(bool(GENERATED_AT_RE.match(str(new.get("generated_at", "")))),
                         "generated_at が UTC・Z 終端で更新されている（D-S5）",
                         f"{old.get('generated_at')} → {new.get('generated_at')}")
            for sid in added:
                entry = new["sources"][sid]
                report.check(entry.get("pages") == [relpath],
                             f"{sid} の pages が新規ページを指す", f"{entry.get('pages')}")
                report.check(str(entry.get("origin", {}).get("locator", "")).startswith((".raw/", "http")),
                             f"{sid} の locator が .raw/ か URL",
                             "inbox/ を指すと清掃後に死ぬ")
                report.check(entry.get("review_status") == "active",
                             f"{sid} の review_status が active", "unreviewed だと規則10-c が増える")
            continue

        old_fm, old_body = _split(old_text)
        new_fm, new_body = _split(new_text)
        diff_keys = {k for k in _fm_keys(old_fm) | _fm_keys(new_fm)
                     if _fm_value(old_fm, k) != _fm_value(new_fm, k)}
        report.check(diff_keys <= {"updated"}, f"{rel}: frontmatter の差分が updated のみ",
                     f"{sorted(diff_keys)}")
        ok, inserted, why = _insert_only(old_body, new_body)
        report.check(ok, f"{rel}: 本文の差分が1箇所の挿入のみ", why)
        if ok and rel == "wiki/index.md":
            report.check(any(f"[[{slug}]]" in line for line in inserted),
                         "index.md の追加行が新規 slug を含む（規則7 の先回り）",
                         f"{inserted}")
        elif ok:
            report.check(any(f"[[{slug}]]" in line for line in inserted),
                         f"{rel}: 追加行が新規 slug を含む（規則5 の先回り）", f"{inserted}")
    return report


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--vault", required=True, type=Path)
    ap.add_argument("--plan", required=True, type=Path)
    args = ap.parse_args(argv)
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    report = verify(args.vault, plan)
    sys.stdout.write(report.render())
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
