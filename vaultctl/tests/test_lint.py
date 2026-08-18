"""lint の集約・出力形式・終了コードのテスト。"""

import json
from datetime import date
from pathlib import Path

import pytest

from vaultctl import cli
from vaultctl.lint import (
    EXIT_OK,
    EXIT_REVIEW,
    EXIT_USAGE,
    EXIT_VIOLATION,
    LINT_REPORT_SCHEMA,
    format_json,
    format_text,
    run_lint,
)
from vaultctl.vault import resolve_vault

TODAY = date(2026, 8, 17)


def page_text(fm_lines, body):
    return "---\n" + "\n".join(fm_lines) + "\n---\n\n" + body


def base_fm(type_, title, *, status="evergreen", created="2026-08-01", updated="2026-08-10"):
    return [
        f"type: {type_}",
        f"title: {title}",
        f"status: {status}",
        f"created: {created}",
        f"updated: {updated}",
        "tags: []",
    ]


def write(root: Path, relpath: str, text: str) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_clean_vault(tmp_path: Path) -> Path:
    """violation を1件も含まず、規則9-a だけが発火する vault。"""
    root = tmp_path / "clean"
    (root / "inbox").mkdir(parents=True)
    write(
        root,
        "wiki/index.md",
        page_text(base_fm("meta", "索引"), "## 索引\n\n- [[a]]\n- [[b]]\n"),
    )
    write(
        root,
        "wiki/concepts/a.md",
        page_text(
            base_fm("concept", "A", status="developing", updated="2026-08-16"),
            "## 概要\n\n[[b]] を参照する。\n",
        ),
    )
    write(
        root,
        "wiki/concepts/b.md",
        page_text(
            base_fm("concept", "B", status="developing", updated="2026-08-16"),
            "## 概要\n\n[[a]] を参照する。\n",
        ),
    )
    return root


def build_empty_vault(tmp_path: Path) -> Path:
    """知識ページを1件も持たない vault。指摘は0件になる。"""
    root = tmp_path / "empty"
    (root / "inbox").mkdir(parents=True)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "## 索引\n\n（未登録）\n"))
    return root


def build_full_vault(tmp_path: Path) -> Path:
    """規則1〜10をそれぞれ最低1件ずつ含む合成 vault。"""
    root = tmp_path / "full"
    (root / "inbox").mkdir(parents=True)

    write(
        root,
        "wiki/index.md",
        page_text(
            base_fm("meta", "索引"),
            "## 索引\n\n"
            "- [[ok]]\n- [[missing-tags]]\n- [[bad-dates]]\n- [[wrong-dir]]\n"
            "- [[broken-link]]\n- [[empty-section]]\n- [[stale]]\n"
            "- [[ledgered]]\n- [[unledgered]]\n- [[phantom]]\n",
        ),
    )
    # 規則4・5・7の材料を兼ねる正常ページ
    write(
        root,
        "wiki/concepts/ok.md",
        page_text(base_fm("concept", "正常"), "## 概要\n\n[[stale]] を参照する。\n"),
    )
    # 規則1: 必須キー tags の欠落
    write(
        root,
        "wiki/concepts/missing-tags.md",
        page_text(
            [
                "type: concept",
                "title: tags欠落",
                "status: evergreen",
                "created: 2026-08-01",
                "updated: 2026-08-10",
            ],
            "## 概要\n\n本文\n",
        ),
    )
    # 規則2: updated < created
    write(
        root,
        "wiki/concepts/bad-dates.md",
        page_text(
            base_fm("concept", "日付逆転", created="2026-08-10", updated="2026-08-01"),
            "## 概要\n\n本文\n",
        ),
    )
    # 規則3: type とディレクトリの不一致
    write(
        root,
        "wiki/concepts/wrong-dir.md",
        page_text(base_fm("entity", "置き場所違い"), "## 概要\n\n本文\n"),
    )
    # 規則4: 切れた wikilink
    write(
        root,
        "wiki/concepts/broken-link.md",
        page_text(base_fm("concept", "リンク切れ"), "## 概要\n\n[[does-not-exist]] を参照する。\n"),
    )
    # 規則5・7: どこからもリンクされず index にも載っていない
    write(
        root,
        "wiki/concepts/orphan.md",
        page_text(base_fm("concept", "孤立"), "## 概要\n\n本文\n"),
    )
    # 規則6: 空セクション
    write(
        root,
        "wiki/concepts/empty-section.md",
        page_text(base_fm("concept", "空セクション"), "## 空\n\n## 次\n\n本文\n"),
    )
    # 規則8: Drive 競合コピー
    write(
        root,
        "wiki/concepts/ok (1).md",
        page_text(base_fm("concept", "競合コピー"), "## 概要\n\n本文\n"),
    )
    # 規則9-b: developing のまま30日以上停止
    write(
        root,
        "wiki/concepts/stale.md",
        page_text(
            base_fm("concept", "滞留", status="developing", created="2026-05-01", updated="2026-05-01"),
            "## 概要\n\n[[ok]] を参照する。\n",
        ),
    )
    # 規則10-b・10-c・10-d の材料
    write(
        root,
        "wiki/sources/ledgered.md",
        page_text(
            base_fm("source", "台帳登録済み") + ["claim_ids:", "  - clm-missing"],
            "## 概要\n\n本文\n\n## 出典\n\nhttps://example.com/\n",
        ),
    )
    # 規則10-a: ledger から参照されていない source ページ
    write(
        root,
        "wiki/sources/unledgered.md",
        page_text(base_fm("source", "台帳未登録"), "## 概要\n\n本文\n\n## 出典\n\nhttps://example.com/\n"),
    )

    write(
        root,
        "wiki/meta/ledgers/source-ledger.json",
        json.dumps(
            {
                "generated_at": "2026-08-16T02:49:49Z",
                "schema": "claude-obsidian.source-ledger.v1",
                "sources": {
                    "src-overdue": {
                        "pages": ["wiki/sources/ledgered.md"],
                        "refresh_due": "2026-08-01",
                        "retrieved_at": "2026-08-01",
                        "review_status": "active",
                    },
                    "src-unreviewed": {
                        "pages": ["wiki/sources/ledgered.md"],
                        "refresh_due": "2027-08-01",
                        "retrieved_at": "2026-08-01",
                        "review_status": "unreviewed",
                    },
                    "src-ghost": {
                        "pages": ["wiki/concepts/gone.md"],
                        "refresh_due": "2027-08-01",
                        "retrieved_at": "2026-08-01",
                        "review_status": "active",
                    },
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    write(
        root,
        "wiki/meta/ledgers/claim-ledger.json",
        json.dumps(
            {
                "claims": {
                    "clm-orphan": {
                        "assessment": "provisional",
                        "location": {"anchor": "抽出した事実", "path": "wiki/sources/vanished.md"},
                        "reviewed_at": "2026-08-01",
                        "risk": "normal",
                        "text": "孤児 claim",
                    }
                },
                "generated_at": "2026-08-16T02:49:49Z",
                "schema": "vaultctl.claim-ledger.v1",
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
    )
    return root


def test_run_lint_invokes_every_rule_checker(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    root = build_full_vault(tmp_path)
    vault = resolve_vault(str(root))

    report = run_lint(vault, today=TODAY)

    rules = {f.rule for f in report.findings}
    expected = {
        "1", "2", "3", "4", "5", "6", "7", "8",
        "9-a", "9-b",
        "10-a", "10-b", "10-c", "10-d",
    }
    assert expected <= rules, f"未検出の規則: {sorted(expected - rules)}"


def test_run_lint_splits_violations_and_reviews(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    vault = resolve_vault(str(build_full_vault(tmp_path)))

    report = run_lint(vault, today=TODAY)

    assert {f.rule for f in report.violations} <= {"1", "2", "3", "4", "5", "6", "7", "8", "11"}
    assert {f.rule for f in report.reviews} <= {"9-a", "9-b", "10-a", "10-b", "10-c", "10-d"}
    assert len(report.violations) + len(report.reviews) == len(report.findings)


def test_run_lint_sorts_findings(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    vault = resolve_vault(str(build_full_vault(tmp_path)))

    report = run_lint(vault, today=TODAY)

    keys = [(f.rule, f.path, f.message) for f in report.findings]
    assert keys == sorted(keys)


def test_format_text_lists_every_finding(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    vault = resolve_vault(str(build_full_vault(tmp_path)))
    report = run_lint(vault, today=TODAY)

    text = format_text(report)

    lines = text.rstrip("\n").split("\n")
    assert lines[0] == f"violation {len(report.violations)} 件 / review {len(report.reviews)} 件"
    assert len(lines) == 1 + len(report.findings)
    assert "\t" in lines[1]


def test_format_text_reports_no_findings(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    vault = resolve_vault(str(build_empty_vault(tmp_path)))
    report = run_lint(vault, today=TODAY)

    assert report.findings == []
    assert format_text(report).rstrip("\n").split("\n")[-1] == "指摘なし"


def test_format_json_is_machine_readable(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    vault = resolve_vault(str(build_full_vault(tmp_path)))
    report = run_lint(vault, today=TODAY)

    payload = json.loads(format_json(report))

    assert payload["schema"] == LINT_REPORT_SCHEMA
    assert payload["counts"] == {
        "violation": len(report.violations),
        "review": len(report.reviews),
    }
    assert len(payload["findings"]) == len(report.findings)
    assert set(payload["findings"][0]) == {"rule", "level", "path", "message"}


def test_cli_lint_returns_1_when_violations_exist(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    root = build_full_vault(tmp_path)

    code = cli.main(["--vault", str(root), "lint", "--today", "2026-08-17"])

    assert code == EXIT_VIOLATION
    assert "violation" in capsys.readouterr().out


def test_cli_lint_returns_2_when_only_reviews_exist(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    root = build_clean_vault(tmp_path)

    code = cli.main(["--vault", str(root), "lint", "--today", "2026-08-17"])

    out = capsys.readouterr().out
    assert code == EXIT_REVIEW, out
    assert "violation 0 件" in out


def test_cli_lint_returns_0_when_nothing_is_reported(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    root = build_empty_vault(tmp_path)

    code = cli.main(["--vault", str(root), "lint", "--today", "2026-08-17"])

    out = capsys.readouterr().out
    assert code == EXIT_OK, out
    assert "指摘なし" in out


def test_cli_lint_returns_64_for_invalid_today(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    root = build_empty_vault(tmp_path)

    code = cli.main(["--vault", str(root), "lint", "--today", "2026/08/17"])

    assert code == EXIT_USAGE
    assert "YYYY-MM-DD" in capsys.readouterr().err


def test_cli_lint_json_output_is_parseable(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    root = build_full_vault(tmp_path)

    code = cli.main(["--vault", str(root), "lint", "--json", "--today", "2026-08-17"])

    payload = json.loads(capsys.readouterr().out)
    assert code == EXIT_VIOLATION
    assert payload["schema"] == LINT_REPORT_SCHEMA
    assert payload["counts"]["violation"] >= 1


def test_run_lint_reports_missing_trailing_newline(tmp_path, monkeypatch):
    """規則11: 末尾改行の欠落。frontmatter を読めないページでも検出できること。"""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    root = tmp_path / "cut"
    (root / "inbox").mkdir(parents=True)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "## 索引\n\n- [[cut]]\n"))
    # 末尾が改行で終わらない正常な frontmatter のページ
    write(root, "wiki/concepts/cut.md",
          page_text(base_fm("concept", "切断"), "## 概要\n\n本文が途中で切れ"))
    # frontmatter が壊れており、かつ末尾が改行で終わらないページ
    (root / "wiki" / "concepts" / "broken.md").write_bytes(
        "---\ntype: concept\n\n本文が途中で切れ".encode("utf-8")[:-1])
    vault = resolve_vault(str(root))

    report = run_lint(vault, today=TODAY)

    rule11 = sorted(f.path for f in report.findings if f.rule == "11")
    assert rule11 == ["wiki/concepts/broken.md", "wiki/concepts/cut.md"]
    assert all(f.level == "violation" for f in report.findings if f.rule == "11")
    # 規則1（frontmatter を読めない）と規則11は両立する
    assert "wiki/concepts/broken.md" in [f.path for f in report.findings if f.rule == "1"]
