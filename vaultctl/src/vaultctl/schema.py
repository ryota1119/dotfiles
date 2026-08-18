"""frontmatter schema の検証（T7、lint 規則1〜3）。"""

from __future__ import annotations

import re
from datetime import date
from typing import Iterable

from .findings import Finding, sort_findings
from .frontmatter import KEY_ORDER, Page

REQUIRED_KEYS = ("type", "title", "status", "created", "updated", "tags")
KNOWLEDGE_TYPES = {"concept", "source", "entity"}
EXTRA_KEYS = {
    "source": {"related", "claim_ids"},
    "concept": {"domain", "related", "sources", "assessment", "risk"},
    "entity": {"aliases", "related"},
    "meta": set(),
}
STATUSES = {"developing", "evergreen"}
DIR_BY_TYPE = {"concept": "wiki/concepts", "source": "wiki/sources", "entity": "wiki/entities"}
META_TYPE = "meta"

ALL_TYPES = KNOWLEDGE_TYPES | {META_TYPE}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_meta_page(relpath: str) -> bool:
    """wiki 直下の *.md と wiki/meta/** を meta ページとみなす。"""
    if not relpath.startswith("wiki/") or not relpath.endswith(".md"):
        return False
    rest = relpath[len("wiki/"):]
    return "/" not in rest or rest.startswith("meta/")


def _violation(page: Page, rule: str, message: str) -> Finding:
    return Finding(rule=rule, level="violation", path=page.relpath, message=message)


def _check_keys(page: Page) -> list[Finding]:
    fm = page.frontmatter
    found: list[Finding] = []

    for key in REQUIRED_KEYS:
        if key not in fm:
            found.append(_violation(page, "1", f"必須キーがありません: {key}"))

    if "title" in fm:
        title = fm["title"]
        if not isinstance(title, str) or not title.strip():
            found.append(_violation(page, "1", "title が空です"))

    if "tags" in fm:
        tags = fm["tags"]
        if not isinstance(tags, list) or any(not isinstance(t, str) for t in tags):
            found.append(_violation(page, "1", "tags は文字列リストである必要があります"))

    if "status" in fm and fm["status"] not in STATUSES:
        found.append(_violation(page, "1", f"status の値が不正です: {fm['status']}"))

    ptype = fm.get("type")
    if "type" in fm and ptype not in ALL_TYPES:
        found.append(_violation(page, "1", f"type の値が不正です: {ptype}"))

    known = set(KEY_ORDER)
    typed = ptype in ALL_TYPES
    allowed = set(REQUIRED_KEYS) | (EXTRA_KEYS[ptype] if typed else set())
    for key in sorted(fm):
        if key in allowed:
            continue
        if key in known:
            if not typed:
                # type が不正なので拡張キーの可否は判定しない
                continue
            found.append(_violation(page, "1", f"type={ptype} では使えないキーです: {key}"))
        else:
            found.append(_violation(page, "1", f"未定義のキーです: {key}"))
    return found


def _check_dates(page: Page) -> list[Finding]:
    fm = page.frontmatter
    found: list[Finding] = []
    parsed: dict[str, date] = {}

    for key in ("created", "updated"):
        if key not in fm:
            continue
        raw = fm[key]
        if not isinstance(raw, str) or not DATE_RE.match(raw):
            found.append(_violation(page, "2", f"{key} の日付形式が不正です: {raw}"))
            continue
        try:
            parsed[key] = date.fromisoformat(raw)
        except ValueError:
            found.append(_violation(page, "2", f"{key} を日付として解釈できません: {raw}"))

    if "created" in parsed and "updated" in parsed and parsed["updated"] < parsed["created"]:
        found.append(_violation(
            page, "2",
            f"updated が created より前です: {fm['updated']} < {fm['created']}"))
    return found


def _check_location(page: Page) -> list[Finding]:
    ptype = page.frontmatter.get("type")
    if ptype not in ALL_TYPES:
        return []
    if is_meta_page(page.relpath):
        if ptype != META_TYPE:
            return [_violation(page, "3", f"meta の配置ですが type={ptype} です")]
        return []
    if ptype == META_TYPE:
        return [_violation(page, "3", "type=meta ですが meta の配置ではありません")]
    expected = DIR_BY_TYPE[ptype]
    if not page.relpath.startswith(expected + "/"):
        return [_violation(page, "3", f"type={ptype} は {expected}/ に置く必要があります")]
    return []


def check_page(page: Page) -> list[Finding]:
    """規則1〜3を1ページに適用する。"""
    return sort_findings(_check_keys(page) + _check_dates(page) + _check_location(page))


def check_pages(pages: Iterable[Page]) -> list[Finding]:
    found: list[Finding] = []
    for page in pages:
        found.extend(check_page(page))
    return sort_findings(found)
