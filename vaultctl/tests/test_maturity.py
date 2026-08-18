"""lint 規則9-a・9-b（ページ成熟度）のテスト。"""

from datetime import date, timedelta

import pytest

from vaultctl.frontmatter import Page
from vaultctl.maturity import (
    PROMOTION_QUEUE_LIMIT,
    STALE_DAYS,
    check_promotion_queue,
    check_stale_developing,
)


def make_page(relpath, *, type_, status, updated):
    """テスト用の Page を組み立てる（ファイルシステムを使わない）。"""
    slug = relpath.rsplit("/", 1)[-1][: -len(".md")]
    return Page(
        relpath=relpath,
        slug=slug,
        frontmatter={
            "type": type_,
            "title": slug,
            "status": status,
            "created": date(2026, 1, 1),
            "updated": updated,
            "tags": [],
        },
        body="## 概要\n\n本文\n",
    )


def test_check_promotion_queue_reports_ratio_per_type():
    pages = [
        make_page("wiki/concepts/a.md", type_="concept", status="developing", updated=date(2026, 8, 1)),
        make_page("wiki/concepts/b.md", type_="concept", status="developing", updated=date(2026, 8, 2)),
        make_page("wiki/sources/c.md", type_="source", status="evergreen", updated=date(2026, 8, 3)),
    ]

    findings = check_promotion_queue(pages)

    assert all(f.rule == "9-a" for f in findings)
    assert all(f.level == "review" for f in findings)
    aggregates = [f for f in findings if f.path == ""]
    assert len(aggregates) == 2
    assert "type=concept developing=2 evergreen=0 (developing率 100.0%)" in aggregates[0].message
    assert "type=source developing=0 evergreen=1 (developing率 0.0%)" in aggregates[1].message


def test_check_promotion_queue_always_outputs_even_without_developing():
    pages = [
        make_page("wiki/sources/c.md", type_="source", status="evergreen", updated=date(2026, 8, 3)),
    ]

    findings = check_promotion_queue(pages)

    assert [f.path for f in findings] == [""]
    assert "developing=0 evergreen=1" in findings[0].message


def test_check_promotion_queue_lists_oldest_developing_up_to_limit():
    pages = [
        make_page(f"wiki/concepts/p{i}.md", type_="concept", status="developing", updated=date(2026, 8, i))
        for i in range(1, 8)
    ]

    findings = check_promotion_queue(pages)

    page_findings = [f for f in findings if f.path != ""]
    assert len(page_findings) == PROMOTION_QUEUE_LIMIT
    assert [f.path for f in page_findings] == [
        "wiki/concepts/p1.md",
        "wiki/concepts/p2.md",
        "wiki/concepts/p3.md",
        "wiki/concepts/p4.md",
        "wiki/concepts/p5.md",
    ]
    assert "updated=2026-08-01" in page_findings[0].message


def test_check_promotion_queue_ignores_meta_pages():
    pages = [
        make_page("wiki/index.md", type_="meta", status="developing", updated=date(2026, 8, 1)),
    ]

    assert check_promotion_queue(pages) == []


@pytest.mark.parametrize("elapsed,expected", [(29, 0), (30, 1), (31, 1)])
def test_check_stale_developing_boundary(elapsed, expected):
    today = date(2026, 8, 17)
    page = make_page(
        "wiki/concepts/a.md",
        type_="concept",
        status="developing",
        updated=today - timedelta(days=elapsed),
    )

    findings = check_stale_developing([page], today)

    assert len(findings) == expected
    if expected:
        assert findings[0].rule == "9-b"
        assert findings[0].level == "review"
        assert findings[0].path == "wiki/concepts/a.md"
        assert f"{STALE_DAYS}日以上" in findings[0].message
        assert f"経過{elapsed}日" in findings[0].message


def test_check_stale_developing_includes_source_provisional():
    today = date(2026, 8, 17)
    pages = [
        make_page("wiki/sources/s.md", type_="source", status="developing", updated=date(2026, 6, 1)),
        make_page("wiki/sources/t.md", type_="source", status="evergreen", updated=date(2026, 6, 1)),
    ]

    findings = check_stale_developing(pages, today)

    assert [f.path for f in findings] == ["wiki/sources/s.md"]


def test_check_stale_developing_accepts_string_dates():
    today = date(2026, 8, 17)
    pages = [
        make_page("wiki/concepts/a.md", type_="concept", status="developing", updated="2026-06-01"),
        make_page("wiki/concepts/b.md", type_="concept", status="developing", updated="不正な値"),
    ]

    findings = check_stale_developing(pages, today)

    assert [f.path for f in findings] == ["wiki/concepts/a.md"]


def test_check_stale_developing_sorted_by_path():
    today = date(2026, 8, 17)
    pages = [
        make_page("wiki/concepts/z.md", type_="concept", status="developing", updated=date(2026, 6, 1)),
        make_page("wiki/concepts/a.md", type_="concept", status="developing", updated=date(2026, 5, 1)),
    ]

    findings = check_stale_developing(pages, today)

    assert [f.path for f in findings] == ["wiki/concepts/a.md", "wiki/concepts/z.md"]
