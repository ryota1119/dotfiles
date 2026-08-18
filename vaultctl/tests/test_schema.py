from conftest import make_page

from vaultctl.frontmatter import parse_page
from vaultctl.schema import check_page, check_pages, is_meta_page


def page(tmp_path, relpath, **kwargs):
    return parse_page(tmp_path, make_page(tmp_path, relpath, **kwargs))


def messages(findings, rule):
    return [f.message for f in findings if f.rule == rule]


def test_valid_concept_page_has_no_findings(tmp_path):
    p = page(tmp_path, "wiki/concepts/a.md", domain="AI", related=["[[b]]"],
             assessment="provisional", risk="normal")
    assert check_page(p) == []


def test_rule1_reports_missing_required_keys(tmp_path):
    p = page(tmp_path, "wiki/concepts/a.md", tags=None, status=None)
    assert messages(check_page(p), "1") == [
        "必須キーがありません: status",
        "必須キーがありません: tags",
    ]


def test_rule1_reports_extra_key_not_allowed_for_type(tmp_path):
    # domain は concept 専用の拡張キー。source では許されない
    p = page(tmp_path, "wiki/sources/a.md", type="source", domain="AI")
    assert messages(check_page(p), "1") == ["type=source では使えないキーです: domain"]


def test_rule1_reports_undefined_key(tmp_path):
    p = page(tmp_path, "wiki/concepts/a.md", address="c-000002")
    assert messages(check_page(p), "1") == ["未定義のキーです: address"]


def test_rule1_reports_invalid_status_and_empty_title(tmp_path):
    p = page(tmp_path, "wiki/concepts/a.md", status="decision", title="   ")
    assert messages(check_page(p), "1") == [
        "status の値が不正です: decision",
        "title が空です",
    ]


def test_rule1_does_not_fire_on_meta_page(tmp_path):
    p = page(tmp_path, "wiki/index.md", type="meta", status="evergreen",
             tags=["meta", "index"], body="# Wiki Index\n\n- [[a]]\n")
    assert check_page(p) == []


def test_rule1_reports_extra_key_on_meta_page(tmp_path):
    p = page(tmp_path, "wiki/index.md", type="meta", status="evergreen", related=["[[a]]"])
    assert messages(check_page(p), "1") == ["type=meta では使えないキーです: related"]


def test_rule2_reports_slash_separated_date(tmp_path):
    p = page(tmp_path, "wiki/concepts/a.md", created="2026/08/05")
    assert messages(check_page(p), "2") == ["created の日付形式が不正です: 2026/08/05"]


def test_rule2_reports_updated_before_created(tmp_path):
    p = page(tmp_path, "wiki/concepts/a.md", created="2026-08-05", updated="2026-08-01")
    assert messages(check_page(p), "2") == [
        "updated が created より前です: 2026-08-01 < 2026-08-05",
    ]


def test_rule3_reports_type_directory_mismatch(tmp_path):
    p = page(tmp_path, "wiki/sources/a.md", type="concept")
    assert messages(check_page(p), "3") == [
        "type=concept は wiki/concepts/ に置く必要があります",
    ]


def test_rule3_reports_meta_type_outside_meta_location(tmp_path):
    p = page(tmp_path, "wiki/concepts/a.md", type="meta", status="evergreen")
    assert messages(check_page(p), "3") == ["type=meta ですが meta の配置ではありません"]


def test_is_meta_page_covers_wiki_root_and_meta_dir():
    assert is_meta_page("wiki/index.md") is True
    assert is_meta_page("wiki/meta/policy.md") is True
    assert is_meta_page("wiki/concepts/a.md") is False
    assert is_meta_page("inbox/a.md") is False


def test_check_pages_sorts_findings_across_pages(tmp_path):
    pages = [
        page(tmp_path, "wiki/sources/z.md", type="source", created="2026/08/05"),
        page(tmp_path, "wiki/concepts/a.md", tags=None),
    ]
    findings = check_pages(pages)

    assert [(f.rule, f.path) for f in findings] == [
        ("1", "wiki/concepts/a.md"),
        ("2", "wiki/sources/z.md"),
    ]
    assert {f.level for f in findings} == {"violation"}


def test_overview_type_at_wiki_root_has_no_findings(tmp_path):
    p = page(tmp_path, "wiki/overview.md", type="overview", status="evergreen")
    assert check_page(p) == []


def test_rule3_reports_overview_outside_meta_location(tmp_path):
    p = page(tmp_path, "wiki/concepts/foo.md", type="overview")
    assert messages(check_page(p), "3") != []


def test_rule1_reports_extra_key_for_overview(tmp_path):
    p = page(tmp_path, "wiki/overview.md", type="overview", related=["[[a]]"])
    assert messages(check_page(p), "1") == ["type=overview では使えないキーです: related"]
