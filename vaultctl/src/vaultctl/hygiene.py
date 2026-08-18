"""空セクションと同期競合コピー、末尾改行の欠落の検出（lint 規則6・8・11）。"""

from __future__ import annotations

import re
from pathlib import Path

from .findings import Finding, sort_findings
from .frontmatter import Page

CONFLICT_PATTERNS = (r" \(\d+\)\.md$", r"のコピー", r"conflicted copy", r"- コピー")
SCAN_DIRS = ("wiki", "inbox", ".raw")
# 規則11 の走査範囲。lint の他の規則（collect_pages）と揃えて wiki/ のみとする。
TRAILING_NEWLINE_DIR = "wiki"

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")


def _sections(body: str) -> list[list]:
    """[レベル, 見出し文字列, 本文行数] の列を返す。コードブロック内は見出しにしない。"""
    sections: list[list] = []
    in_fence = False
    for line in body.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            if sections:
                sections[-1][2] += 1
            continue
        if in_fence:
            if line.strip() and sections:
                sections[-1][2] += 1
            continue
        heading = HEADING_RE.match(line)
        if heading:
            sections.append([len(heading.group(1)), heading.group(2).strip(), 0])
            continue
        if line.strip() and sections:
            sections[-1][2] += 1
    return sections


def check_empty_sections(page: Page) -> list[Finding]:
    """規則6: 見出しだけで本文がない節。直後により深い見出しが来る場合は対象外。"""
    sections = _sections(page.body)
    found: list[Finding] = []
    for i, (level, text, content) in enumerate(sections):
        if content:
            continue
        nxt = sections[i + 1] if i + 1 < len(sections) else None
        if nxt is not None and nxt[0] > level:
            continue
        found.append(Finding(
            rule="6", level="violation", path=page.relpath,
            message=f"見出しだけで本文がない節です: {text}"))
    return sort_findings(found)


def check_conflict_copies(root: Path) -> list[Finding]:
    """規則8: wiki/ inbox/ .raw/ を走査し、同期競合コピーらしいファイル名を報告する。"""
    patterns = [re.compile(p) for p in CONFLICT_PATTERNS]
    found: list[Finding] = []
    for name in SCAN_DIRS:
        base = root / name
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            if any(p.search(path.name) for p in patterns):
                found.append(Finding(
                    rule="8", level="violation",
                    path=path.relative_to(root).as_posix(),
                    message=f"同期の競合コピーと思われるファイル名です: {path.name}"))
    return sort_findings(found)


def check_trailing_newline(root: Path) -> list[Finding]:
    """規則11: wiki/**/*.md の末尾が改行で終わっていない。

    非原子的な追記でファイルが切断された破損は、例外なく「末尾が改行で
    終わっていない」という特徴を持つ。バイト列だけを見る検査なので、
    frontmatter が壊れていて `collect_pages` がパースできなかったページや、
    不正な UTF-8 を含むページに対しても等しく効く（デコードしない）。

    空ファイル（0バイト）は対象外とする。末尾改行を問う中身がないため。

    注: 規則番号は追記のみで振り直さない。番号の大小と level は対応せず、
    規則9〜10が review、規則1〜8と11が violation である。
    """
    base = root / TRAILING_NEWLINE_DIR
    if not base.is_dir():
        return []
    found: list[Finding] = []
    for path in base.rglob("*.md"):
        if not path.is_file():
            continue
        data = path.read_bytes()
        if not data:
            continue
        if data.endswith(b"\n"):
            continue
        found.append(Finding(
            rule="11", level="violation",
            path=path.relative_to(root).as_posix(),
            message="末尾が改行で終わっていません（追記の途中で切断された可能性があります）"))
    return sort_findings(found)
