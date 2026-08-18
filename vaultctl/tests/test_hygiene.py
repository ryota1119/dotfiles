from conftest import make_page

from vaultctl.frontmatter import parse_page
from vaultctl.hygiene import (
    check_conflict_copies,
    check_empty_sections,
    check_trailing_newline,
)


def page(tmp_path, relpath, body):
    return parse_page(tmp_path, make_page(tmp_path, relpath, body=body))


def test_check_empty_sections_detects_heading_without_body(tmp_path):
    body = "# タイトル\n\n## 内容\n\n本文がある\n\n## 出典\n\n## 関連\n\n本文がある\n"
    found = check_empty_sections(page(tmp_path, "wiki/concepts/a.md", body))

    assert [(f.rule, f.level, f.path, f.message) for f in found] == [
        ("6", "violation", "wiki/concepts/a.md", "見出しだけで本文がない節です: 出典"),
    ]


def test_check_empty_sections_allows_heading_followed_by_subheading(tmp_path):
    body = "# タイトル\n\n## 内容\n\n### 詳細\n\n本文がある\n"
    assert check_empty_sections(page(tmp_path, "wiki/concepts/a.md", body)) == []


def test_check_empty_sections_allows_last_section_with_body(tmp_path):
    body = "# タイトル\n\n## 内容\n\n最後の節の本文\n"
    assert check_empty_sections(page(tmp_path, "wiki/concepts/a.md", body)) == []


def test_check_empty_sections_detects_empty_last_section(tmp_path):
    body = "# タイトル\n\n## 内容\n\n本文\n\n## 未記入\n"
    found = check_empty_sections(page(tmp_path, "wiki/concepts/a.md", body))

    assert [f.message for f in found] == ["見出しだけで本文がない節です: 未記入"]


def test_check_empty_sections_ignores_hash_inside_code_block(tmp_path):
    body = (
        "# タイトル\n\n"
        "## 内容\n\n"
        "```bash\n"
        "# これはコメントであって見出しではない\n"
        "ls -la\n"
        "```\n"
    )
    assert check_empty_sections(page(tmp_path, "wiki/concepts/a.md", body)) == []


def touch(root, relpath, text="ダミー\n"):
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def test_check_conflict_copies_detects_known_patterns(tmp_path):
    touch(tmp_path, "wiki/concepts/foo (1).md")
    touch(tmp_path, "inbox/レポート のコピー.pdf")
    touch(tmp_path, ".raw/note (conflicted copy 2026-08-05).md")
    touch(tmp_path, "wiki/concepts/foo.md")
    touch(tmp_path, "inbox/report.pdf")

    found = check_conflict_copies(tmp_path)

    assert [(f.rule, f.level, f.path) for f in found] == [
        ("8", "violation", ".raw/note (conflicted copy 2026-08-05).md"),
        ("8", "violation", "inbox/レポート のコピー.pdf"),
        ("8", "violation", "wiki/concepts/foo (1).md"),
    ]
    assert found[2].message == "同期の競合コピーと思われるファイル名です: foo (1).md"


def test_check_conflict_copies_ignores_directories_outside_scan_dirs(tmp_path):
    touch(tmp_path, "wiki/concepts/ok.md")
    touch(tmp_path, "archive/old のコピー.md")

    assert check_conflict_copies(tmp_path) == []


def test_check_conflict_copies_on_empty_vault(tmp_path):
    assert check_conflict_copies(tmp_path) == []


# --- 規則11: 末尾改行の欠落（非原子的な追記による切断の検出） ---


def test_check_trailing_newline_detects_missing_newline(tmp_path):
    touch(tmp_path, "wiki/concepts/cut.md", text="---\ntype: concept\n---\n\n本文が途中で切れ")

    found = check_trailing_newline(tmp_path)

    assert [(f.rule, f.level, f.path) for f in found] == [
        ("11", "violation", "wiki/concepts/cut.md"),
    ]
    assert "末尾が改行で終わっていません" in found[0].message


def test_check_trailing_newline_allows_normal_page(tmp_path):
    touch(tmp_path, "wiki/concepts/ok.md", text="---\ntype: concept\n---\n\n本文です。\n")

    assert check_trailing_newline(tmp_path) == []


def test_check_trailing_newline_ignores_empty_file(tmp_path):
    path = tmp_path / "wiki" / "concepts" / "empty.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"")

    assert check_trailing_newline(tmp_path) == []


def test_check_trailing_newline_detects_unparsable_file(tmp_path):
    """frontmatter が壊れていても不正な UTF-8 を含んでいても、バイト列で判定する。"""
    path = tmp_path / "wiki" / "concepts" / "broken.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    # frontmatter の終了区切りが無く、末尾は不完全な UTF-8 バイト列で切断されている
    path.write_bytes("---\ntype: concept\n\n本文が途中で切れ".encode("utf-8")[:-1])

    found = check_trailing_newline(tmp_path)

    assert [(f.rule, f.level, f.path) for f in found] == [
        ("11", "violation", "wiki/concepts/broken.md"),
    ]


def test_check_trailing_newline_ignores_non_wiki_dirs(tmp_path):
    touch(tmp_path, "inbox/memo.md", text="末尾改行なし")
    touch(tmp_path, ".raw/note.md", text="末尾改行なし")

    assert check_trailing_newline(tmp_path) == []


def test_check_trailing_newline_on_empty_vault(tmp_path):
    assert check_trailing_newline(tmp_path) == []
