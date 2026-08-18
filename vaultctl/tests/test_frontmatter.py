import pytest

from vaultctl.frontmatter import (
    FrontmatterError,
    dump_frontmatter,
    iter_pages,
    parse_page,
    render_page,
    split_frontmatter,
)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_split_frontmatter_returns_yaml_text_and_body():
    text = "---\ntype: concept\ntitle: \"あ\"\n---\n\n# 見出し\n\n本文\n"
    fm_text, body = split_frontmatter(text)

    assert fm_text == "type: concept\ntitle: \"あ\""
    assert body == "# 見出し\n\n本文\n"


def test_split_frontmatter_without_opening_delimiter_raises():
    with pytest.raises(FrontmatterError) as exc:
        split_frontmatter("# 見出しだけのファイル\n\n本文\n")

    assert "開始区切り" in str(exc.value)


def test_split_frontmatter_without_closing_delimiter_raises():
    with pytest.raises(FrontmatterError) as exc:
        split_frontmatter("---\ntype: concept\n\n# 見出し\n")

    assert "終了区切り" in str(exc.value)


def test_parse_page_normalizes_yaml_dates_to_iso_strings(tmp_path):
    path = write(
        tmp_path / "wiki" / "concepts" / "foo.md",
        "---\ntype: concept\ncreated: 2026-08-05\ntags:\n  - 2026-08-06\n---\n\n本文\n",
    )
    page = parse_page(tmp_path, path)

    assert page.frontmatter["created"] == "2026-08-05"
    assert isinstance(page.frontmatter["created"], str)
    assert page.frontmatter["tags"] == ["2026-08-06"]
    assert isinstance(page.frontmatter["tags"][0], str)
    assert page.relpath == "wiki/concepts/foo.md"
    assert page.slug == "foo"
    assert page.body == "本文\n"


def test_parse_page_keeps_slash_separated_date_as_raw_string(tmp_path):
    path = write(
        tmp_path / "wiki" / "concepts" / "bar.md",
        "---\ntype: concept\ncreated: 2026/08/05\n---\n\n本文\n",
    )
    page = parse_page(tmp_path, path)

    assert page.frontmatter["created"] == "2026/08/05"


def test_parse_page_without_frontmatter_raises(tmp_path):
    path = write(tmp_path / "wiki" / "concepts" / "plain.md", "# 見出しのみ\n")

    with pytest.raises(FrontmatterError):
        parse_page(tmp_path, path)


def test_iter_pages_yields_wiki_markdown_sorted_by_relpath(tmp_path):
    for rel in ("wiki/sources/b.md", "wiki/concepts/a.md", "wiki/index.md"):
        write(tmp_path / rel, "---\ntype: concept\n---\n\n本文\n")
    write(tmp_path / "inbox" / "z.md", "---\ntype: concept\n---\n\n本文\n")
    write(tmp_path / "wiki" / "concepts" / "note.txt", "テキスト")

    assert [p.relpath for p in iter_pages(tmp_path)] == [
        "wiki/concepts/a.md",
        "wiki/index.md",
        "wiki/sources/b.md",
    ]


def test_dump_frontmatter_uses_key_order_and_bare_dates():
    fm = {
        "tags": ["source", "2026-08"],
        "address": "c-000002",
        "title": "見出し: テスト",
        "type": "source",
        "created": "2026-08-05",
        "updated": "2026-08-06",
        "status": "evergreen",
        "related": ["[[foo]]"],
    }

    assert dump_frontmatter(fm) == (
        "type: source\n"
        "title: \"見出し: テスト\"\n"
        "status: evergreen\n"
        "created: 2026-08-05\n"
        "updated: 2026-08-06\n"
        "tags:\n"
        "  - source\n"
        "  - 2026-08\n"
        "related:\n"
        "  - \"[[foo]]\"\n"
        "address: c-000002\n"
    )


def test_dump_frontmatter_emits_empty_list_inline():
    assert dump_frontmatter({"tags": []}) == "tags: []\n"


def test_render_page_round_trips_through_parse_page(tmp_path):
    fm = {
        "type": "concept",
        "title": "AIビジネス・エコシステムの動向",
        "status": "developing",
        "created": "2026-08-05",
        "updated": "2026-08-05",
        "tags": ["concept", "2026-08"],
        "domain": "AI業界動向",
        "related": ["[[ai-model-releases-pricing-2026-08]]"],
    }
    body = "# 見出し\n\n## 内容\n\n- 箇条書き\n"
    path = write(tmp_path / "wiki" / "concepts" / "rt.md", render_page(fm, body))

    page = parse_page(tmp_path, path)

    assert page.frontmatter == fm
    assert page.body == body
    assert render_page(page.frontmatter, page.body) == path.read_text(encoding="utf-8")


def test_collect_pages_reports_unreadable_page_and_keeps_going(tmp_path):
    from vaultctl.frontmatter import collect_pages

    root = tmp_path / "vault"
    (root / "wiki").mkdir(parents=True)
    (root / "wiki" / "broken.md").write_text("# frontmatter なし\n", encoding="utf-8")
    (root / "wiki" / "ok.md").write_text(
        "---\ntype: meta\ntitle: ok\nstatus: evergreen\n"
        "created: 2026-08-01\nupdated: 2026-08-01\ntags:\n  - meta\n---\n\n# ok\n",
        encoding="utf-8",
    )

    pages, findings = collect_pages(root)

    assert [p.relpath for p in pages] == ["wiki/ok.md"]
    assert [(f.rule, f.level, f.path) for f in findings] == [
        ("1", "violation", "wiki/broken.md")
    ]
