from __future__ import annotations

import builtins
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SCRIPT = ROOT / "scripts" / "make-fixture-vault.sh"
# chezmoi は `executable_` 接頭辞が無いと実行ビットを展開先に保存しない。
# 接頭辞を外した名前（review-report.py）が ~/.claude/ 側の実際のファイル名になる。
REPORT_SCRIPT = ROOT / "dot_claude/skills/vault-review/scripts/executable_review-report.py"
EXPECTED_RULE_COUNTS = {"2": 1, "3": 1, "4": 1, "5": 2, "6": 1, "7": 2}
EXPECTED_VIOLATIONS = 8


def _load_report_module():
    spec = importlib.util.spec_from_file_location("vault_review_report", REPORT_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def report():
    return _load_report_module()


def _vaultctl_command() -> list[str]:
    installed = Path("/Users/r-shinohara/.local/bin/vaultctl")
    if installed.is_file() and os.access(installed, os.X_OK):
        return [str(installed)]
    uv = shutil.which("uv")
    if uv:
        return [uv, "run", "--project", str(ROOT / "vaultctl"), "vaultctl"]
    pytest.fail("vaultctl が /Users/r-shinohara/.local/bin に無く、uv も利用できません")


@pytest.fixture()
def lint_payload(tmp_path: Path) -> dict:
    vault = tmp_path / "fixture-vault"
    subprocess.run(["bash", str(FIXTURE_SCRIPT), str(vault)], check=True)
    env = os.environ.copy()
    env["XDG_STATE_HOME"] = str(tmp_path / "state")
    result = subprocess.run(
        [*_vaultctl_command(), "--vault", str(vault), "lint", "--json"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == 1, result.stderr
    return json.loads(result.stdout)


def _finding(rule: str, path: str = "wiki/example.md") -> dict[str, str]:
    return {"rule": rule, "level": "violation", "path": path, "message": f"rule {rule}"}


def test_fixture_vault_has_only_expected_violations(lint_payload: dict) -> None:
    counts = lint_payload["counts"]
    actual = {}
    for finding in lint_payload["findings"]:
        if finding["level"] == "violation":
            actual[finding["rule"]] = actual.get(finding["rule"], 0) + 1
    assert counts["violation"] == EXPECTED_VIOLATIONS
    assert actual == EXPECTED_RULE_COUNTS


def test_report_has_ordered_sections_and_preserves_total(report, lint_payload: dict) -> None:
    """区分合計は、lint/ledgerの重複除去後finding総数と比較する。"""
    lint_findings = report.parse_lint_json(json.dumps(lint_payload))
    shared = _finding("10-c")
    findings, preamble = report.reconcile_findings([*lint_findings, shared], [shared])
    output = report.render_report(findings, preamble)
    headings = [title for _, title in report.SECTION_TITLES]
    positions = [output.index(title) for title in headings]
    assert positions == sorted(positions)
    section_counts = [int(value) for value in re.findall(r"^[A-D]\. .* — (\d+)件$", output, re.M)]
    assert sum(section_counts) == len(findings)
    assert f"入力{len(lint_findings) + 2}件 → 重複除去後{len(findings)}件" in output


def test_empty_findings_prints_one_line(report) -> None:
    payload = {"counts": {"violation": 0, "review": 0}, "findings": []}
    assert report.render_report(report.parse_lint_json(json.dumps(payload))) == "指摘なし\n"


def test_ledger_accepts_bare_array(report) -> None:
    assert report.parse_ledger_json(json.dumps([_finding("10-a")]))[0]["rule"] == "10-a"


def test_identical_lint_rule10_and_ledger_are_counted_once(
    report, tmp_path: Path, capsys
) -> None:
    shared = _finding("10-c", "wiki/sources/shared.md")
    lint_path = tmp_path / "lint.json"
    ledger_path = tmp_path / "ledger.json"
    lint_path.write_text(
        json.dumps({"counts": {"violation": 0, "review": 1}, "findings": [shared]}),
        encoding="utf-8",
    )
    ledger_path.write_text(json.dumps([shared]), encoding="utf-8")

    assert report.main(["--lint-json", str(lint_path), "--ledger-json", str(ledger_path)]) == 0
    output = capsys.readouterr().out
    assert output.startswith("照合: lintの規則10とledger verifyが一致（1件、重複を除去）\n")
    assert "入力2件 → 重複除去後1件" in output
    assert "C. 要レビュー・出所 — 1件" in output
    assert output.count("wiki/sources/shared.md") == 1


def test_lint_and_ledger_mismatch_lists_every_difference(report, tmp_path: Path, capsys) -> None:
    lint_only = _finding("10-a", "wiki/sources/lint-only.md")
    ledger_only = _finding("10-d", "wiki/sources/ledger-only.md")
    lint_path = tmp_path / "lint.json"
    ledger_path = tmp_path / "ledger.json"
    lint_path.write_text(
        json.dumps({"counts": {"violation": 0, "review": 1}, "findings": [lint_only]}),
        encoding="utf-8",
    )
    ledger_path.write_text(json.dumps([ledger_only]), encoding="utf-8")

    assert report.main(["--lint-json", str(lint_path), "--ledger-json", str(ledger_path)]) == 0
    output = capsys.readouterr().out
    assert output.startswith(
        "警告: lintとledger verifyが食い違う（lintのみ1件 / ledgerのみ1件）\n"
    )
    assert "- lintのみ [規則10-a] wiki/sources/lint-only.md: rule 10-a" in output
    assert "- ledgerのみ [規則10-d] wiki/sources/ledger-only.md: rule 10-d" in output
    assert "入力2件 → 重複除去後2件" in output
    assert "C. 要レビュー・出所 — 2件" in output


def test_parsers_reject_the_other_shape(report) -> None:
    wrapper = {"counts": {"violation": 0, "review": 0}, "findings": []}
    with pytest.raises(SystemExit, match="lint JSON は裸の配列ではなく"):
        report.parse_lint_json("[]")
    with pytest.raises(SystemExit, match="ledger JSON はラッパー付き object ではなく"):
        report.parse_ledger_json(json.dumps(wrapper))


def test_unknown_rule_goes_to_b_with_warning(report) -> None:
    output = report.render_report([_finding("99")])
    assert "B. 判断が要る違反 — 1件" in output
    assert "警告: 未分類の規則 99 が 1 件" in output
    assert "[規則99]" in output


def test_report_is_byte_deterministic(report, lint_payload: dict) -> None:
    lint_findings = [*report.parse_lint_json(json.dumps(lint_payload)), _finding("10-a")]
    ledger_findings = [_finding("10-a")]
    first, first_preamble = report.reconcile_findings(lint_findings, ledger_findings)
    second, second_preamble = report.reconcile_findings(
        list(reversed(lint_findings)), list(reversed(ledger_findings))
    )
    assert report.render_report(first, first_preamble) == report.render_report(
        second, second_preamble
    )


def test_main_never_opens_real_vault(report, lint_payload: dict, tmp_path: Path, monkeypatch, capsys) -> None:
    lint_path = tmp_path / "lint.json"
    lint_path.write_text(json.dumps(lint_payload), encoding="utf-8")
    real_open = builtins.open
    real_path_open = Path.open

    def reject_real_vault(path, *args, **kwargs):
        if "Workspace/exocortex" in os.fspath(path):
            raise AssertionError(f"実 vault へのアクセス: {path}")
        return real_open(path, *args, **kwargs)

    def reject_real_vault_path(path, *args, **kwargs):
        if "Workspace/exocortex" in os.fspath(path):
            raise AssertionError(f"実 vault へのアクセス: {path}")
        return real_path_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", reject_real_vault)
    monkeypatch.setattr(Path, "open", reject_real_vault_path)
    assert report.main(["--lint-json", str(lint_path)], stdin=io.StringIO("")) == 0
    assert "A. 機械的に直せる違反" in capsys.readouterr().out


def test_cli_reads_stdin_and_ledger_file(tmp_path: Path) -> None:
    lint = {"counts": {"violation": 0, "review": 0}, "findings": []}
    ledger_path = tmp_path / "ledger.json"
    ledger_path.write_text(json.dumps([_finding("10-c")]), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(REPORT_SCRIPT), "--ledger-json", str(ledger_path)],
        input=json.dumps(lint),
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "警告: lintとledger verifyが食い違う（lintのみ0件 / ledgerのみ1件）" in result.stdout
    assert "C. 要レビュー・出所 — 1件" in result.stdout
