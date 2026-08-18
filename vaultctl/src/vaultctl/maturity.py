"""ページ成熟度の検査（lint 規則9-a・9-b）。

設計書 6.2 節に対応する。9-a は日数によらず常時出力し、9-b は30日以上
`developing` のまま更新が止まっているページを催促する。
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

from .findings import Finding
from .frontmatter import Page
from .schema import KNOWLEDGE_TYPES

STALE_DAYS = 30
PROMOTION_QUEUE_LIMIT = 5


def _as_date(value: object) -> date | None:
    """frontmatter の日付値を `date` に正規化する。解釈できなければ None。"""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _knowledge_pages(pages: Iterable[Page]) -> list[Page]:
    return [p for p in pages if p.frontmatter.get("type") in KNOWLEDGE_TYPES]


def check_promotion_queue(pages: Iterable[Page]) -> list[Finding]:
    """規則9-a: type別の developing/evergreen 比率と、最も古い developing を最大5件。"""
    targets = _knowledge_pages(pages)
    findings: list[Finding] = []

    for page_type in sorted(KNOWLEDGE_TYPES):
        same = [p for p in targets if p.frontmatter.get("type") == page_type]
        developing = [p for p in same if p.frontmatter.get("status") == "developing"]
        evergreen = [p for p in same if p.frontmatter.get("status") == "evergreen"]
        total = len(developing) + len(evergreen)
        if total == 0:
            continue
        ratio = len(developing) * 100.0 / total
        findings.append(
            Finding(
                rule="9-a",
                level="review",
                path="",
                message=(
                    f"昇格待ちキュー: type={page_type} developing={len(developing)} "
                    f"evergreen={len(evergreen)} (developing率 {ratio:.1f}%)"
                ),
            )
        )

    developing_all = [p for p in targets if p.frontmatter.get("status") == "developing"]
    developing_all.sort(key=lambda p: (_as_date(p.frontmatter.get("updated")) or date.max, p.relpath))
    for page in developing_all[:PROMOTION_QUEUE_LIMIT]:
        updated = _as_date(page.frontmatter.get("updated"))
        shown = updated.isoformat() if updated is not None else "不明"
        findings.append(
            Finding(
                rule="9-a",
                level="review",
                path=page.relpath,
                message=(
                    f"昇格待ち: developing のまま更新が古い"
                    f"（type={page.frontmatter.get('type')}, updated={shown}）"
                ),
            )
        )

    return findings


def check_stale_developing(pages: Iterable[Page], today: date) -> list[Finding]:
    """規則9-b: `developing` のまま STALE_DAYS 日以上更新が止まっているページ。

    `sources` の provisional（裏取り未了）も status が `developing` なので、
    特別扱いせずそのまま対象に入る（設計書 6.2 節）。
    """
    findings: list[Finding] = []
    for page in _knowledge_pages(pages):
        if page.frontmatter.get("status") != "developing":
            continue
        updated = _as_date(page.frontmatter.get("updated"))
        if updated is None:
            continue
        elapsed = (today - updated).days
        if elapsed < STALE_DAYS:
            continue
        findings.append(
            Finding(
                rule="9-b",
                level="review",
                path=page.relpath,
                message=(
                    f"長期滞留: developing のまま{STALE_DAYS}日以上更新なし"
                    f"（updated={updated.isoformat()}, 経過{elapsed}日）"
                ),
            )
        )
    findings.sort(key=lambda f: f.path)
    return findings
