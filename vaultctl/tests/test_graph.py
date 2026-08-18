from conftest import make_page

from vaultctl.frontmatter import parse_page
from vaultctl.graph import (
    build_graph,
    check_broken_links,
    check_index,
    check_orphans,
    extract_links,
)


def page(tmp_path, relpath, **kwargs):
    return parse_page(tmp_path, make_page(tmp_path, relpath, **kwargs))


def index_page(tmp_path, links):
    body = "# Wiki Index\n\n" + "".join(f"- [[{s}]] — 説明\n" for s in links)
    return page(tmp_path, "wiki/index.md", type="meta", status="evergreen",
                tags=["meta", "index"], body=body)


def test_extract_links_normalizes_anchor_and_alias():
    body = "本文 [[foo#見出し]] と [[bar|表示名]] と [[baz]] と ![[foo]]\n"
    assert extract_links(body) == ["foo", "bar", "baz", "foo"]


def test_extract_links_returns_empty_list_without_links():
    assert extract_links("リンクの無い本文\n") == []


def test_build_graph_dedupes_targets_and_collects_backlinks(tmp_path):
    a = page(tmp_path, "wiki/concepts/a.md",
             body="[[b]] と [[b#節]] と [[c|しー]]\n", related=["[[d]]"])
    b = page(tmp_path, "wiki/concepts/b.md", body="本文\n")

    graph = build_graph([a, b])

    assert graph.targets["wiki/concepts/a.md"] == ["b", "c", "d"]
    assert graph.targets["wiki/concepts/b.md"] == []
    assert graph.by_relpath["wiki/concepts/b.md"] is b
    assert graph.pages["b"] is b
    assert graph.backlinks["b"] == {"wiki/concepts/a.md"}
    assert graph.backlinks["a"] == set()


def test_check_broken_links_reports_unresolved_targets(tmp_path):
    a = page(tmp_path, "wiki/concepts/a.md", body="[[b]] と [[missing#節]]\n")
    b = page(tmp_path, "wiki/concepts/b.md", body="本文\n")

    found = check_broken_links(build_graph([a, b]))

    assert [(f.rule, f.level, f.path, f.message) for f in found] == [
        ("4", "violation", "wiki/concepts/a.md", "リンク先が存在しません: [[missing]]"),
    ]


def test_check_broken_links_reports_unresolved_frontmatter_related(tmp_path):
    a = page(tmp_path, "wiki/concepts/a.md", body="本文\n", related=["[[missing]]"])

    found = check_broken_links(build_graph([a]))

    assert [f.message for f in found] == ["リンク先が存在しません: [[missing]]"]


def test_check_orphans_ignores_backlinks_from_hub_pages(tmp_path):
    idx = index_page(tmp_path, ["foo"])
    foo = page(tmp_path, "wiki/concepts/foo.md", body="本文\n")

    found = check_orphans(build_graph([idx, foo]))

    assert [(f.rule, f.path) for f in found] == [("5", "wiki/concepts/foo.md")]
    assert found[0].message == "どこからもリンクされていません（ハブページからのリンクは除く）"


def test_check_orphans_counts_backlink_from_normal_page(tmp_path):
    idx = index_page(tmp_path, ["foo", "bar"])
    foo = page(tmp_path, "wiki/concepts/foo.md", body="本文\n")
    bar = page(tmp_path, "wiki/concepts/bar.md", body="[[foo]] を参照\n")

    found = check_orphans(build_graph([idx, foo, bar]))

    assert [f.path for f in found] == ["wiki/concepts/bar.md"]


def test_check_orphans_ignores_self_link(tmp_path):
    idx = index_page(tmp_path, ["foo"])
    foo = page(tmp_path, "wiki/concepts/foo.md", body="[[foo]] 自己参照\n")

    assert [f.path for f in check_orphans(build_graph([idx, foo]))] == ["wiki/concepts/foo.md"]


def test_check_index_detects_both_directions(tmp_path):
    idx = index_page(tmp_path, ["listed", "ghost"])
    listed = page(tmp_path, "wiki/concepts/listed.md", body="本文\n")
    unlisted = page(tmp_path, "wiki/sources/unlisted.md", type="source", body="本文\n")

    found = check_index(build_graph([idx, listed, unlisted]))

    assert [(f.rule, f.level, f.path, f.message) for f in found] == [
        ("7", "violation", "wiki/index.md",
         "wiki/index.md に載っているページが存在しません: [[ghost]]"),
        ("7", "violation", "wiki/sources/unlisted.md", "wiki/index.md に載っていません"),
    ]


def test_check_index_ignores_meta_pages(tmp_path):
    idx = index_page(tmp_path, ["a"])
    a = page(tmp_path, "wiki/concepts/a.md", body="本文\n")
    log = page(tmp_path, "wiki/log.md", type="meta", status="evergreen", body="記録\n")

    assert check_index(build_graph([idx, a, log])) == []


def test_check_index_reports_missing_index_file(tmp_path):
    a = page(tmp_path, "wiki/concepts/a.md", body="本文\n")

    found = check_index(build_graph([a]))

    assert [(f.rule, f.path, f.message) for f in found] == [
        ("7", "wiki/index.md", "wiki/index.md が存在しません"),
    ]
