from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SCRIPT = ROOT / "scripts" / "make-fixture-vault.sh"

EXPECTED_BEFORE_VIOLATIONS = 8
EXPECTED_AFTER_VIOLATIONS = 5
EXPECTED_BEFORE_RULE_COUNTS = {"2": 1, "3": 1, "4": 1, "5": 2, "6": 1, "7": 2}
EXPECTED_AFTER_RULE_COUNTS = {"2": 1, "3": 1, "5": 2, "6": 1}


def _vaultctl_command() -> list[str]:
    installed = Path("/Users/r-shinohara/.local/bin/vaultctl")
    if installed.is_file() and os.access(installed, os.X_OK):
        return [str(installed)]
    uv = shutil.which("uv")
    if uv:
        return [uv, "run", "--project", str(ROOT / "vaultctl"), "vaultctl"]
    pytest.fail("vaultctl が /Users/r-shinohara/.local/bin に無く、uv も利用できません")


def _run_vaultctl(
    vault: Path, env: dict[str, str], *args: str, expected_returncode: int = 0
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [*_vaultctl_command(), "--vault", str(vault), *args],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )
    assert result.returncode == expected_returncode, result.stderr
    return result


def _lint(vault: Path, env: dict[str, str]) -> dict:
    result = _run_vaultctl(
        vault, env, "lint", "--json", "--today", "2026-08-18", expected_returncode=1
    )
    return json.loads(result.stdout)


def _rule_counts(payload: dict) -> dict[str, int]:
    counts: dict[str, int] = {}
    for finding in payload["findings"]:
        if finding["level"] == "violation":
            rule = finding["rule"]
            counts[rule] = counts.get(rule, 0) + 1
    return counts


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _frontmatter_value(page: Path, key: str) -> str:
    for line in page.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    pytest.fail(f"frontmatter に {key} がありません: {page}")


def _rule7_slug(payload: dict, message_prefix: str) -> str:
    findings = [
        finding
        for finding in payload["findings"]
        if finding["rule"] == "7" and finding["message"].startswith(message_prefix)
    ]
    assert len(findings) == 1
    match = re.search(r"\[\[([^]]+)\]\]", findings[0]["message"])
    assert match is not None
    return match.group(1)


def _stage_rule7_index(
    original: bytes, *, ghost_slug: str, unlisted_slug: str, unlisted_title: str
) -> tuple[bytes, bytes, bytes]:
    lines = original.splitlines(keepends=True)
    headings = [line.decode("utf-8").rstrip("\n") for line in lines if line.startswith(b"## ")]
    assert headings == ["## Sources", "## Entities", "## Concepts"]

    ghost_indexes = [
        index for index, line in enumerate(lines) if f"[[{ghost_slug}]]".encode() in line
    ]
    assert len(ghost_indexes) == 1
    ghost_line = lines.pop(ghost_indexes[0])
    assert ghost_line.startswith(f"- [[{ghost_slug}]] — ".encode())

    sources_index = lines.index(b"## Sources\n")
    next_heading = next(
        index
        for index in range(sources_index + 1, len(lines))
        if lines[index].startswith(b"## ")
    )
    insert_at = next_heading
    while insert_at > sources_index + 1 and lines[insert_at - 1].strip() == b"":
        insert_at -= 1
    unlisted_line = f"- [[{unlisted_slug}]] — {unlisted_title}\n".encode()
    assert unlisted_line not in lines
    lines.insert(insert_at, unlisted_line)
    return b"".join(lines), ghost_line, unlisted_line


def test_rule7_bundle_plan_apply_and_lint_prediction(tmp_path: Path) -> None:
    vault = tmp_path / "fixture-vault"
    subprocess.run(["bash", str(FIXTURE_SCRIPT), str(vault)], check=True)
    env = os.environ.copy()
    env["XDG_STATE_HOME"] = str(tmp_path / "state")

    index_path = vault / "wiki/index.md"
    before_bytes = index_path.read_bytes()
    before = _lint(vault, env)
    assert before["counts"]["violation"] == EXPECTED_BEFORE_VIOLATIONS
    assert _rule_counts(before) == EXPECTED_BEFORE_RULE_COUNTS

    ghost_slug = _rule7_slug(
        before, "wiki/index.md に載っているページが存在しません:"
    )
    unlisted_page = vault / "wiki/sources/fixture-unlisted.md"
    after_bytes, ghost_line, unlisted_line = _stage_rule7_index(
        before_bytes,
        ghost_slug=ghost_slug,
        unlisted_slug=unlisted_page.stem,
        unlisted_title=_frontmatter_value(unlisted_page, "title"),
    )

    staging = tmp_path / "rule7" / "staging"
    staging.mkdir(parents=True)
    staged_index = staging / "index.md"
    staged_index.write_bytes(after_bytes)

    bundle_path = tmp_path / "rule7" / "bundle.json"
    plan_path = tmp_path / "rule7" / "plan.json"
    _write_json(
        bundle_path,
        {
            "schema": "vaultctl.bundle.v1",
            "operation_id": "review-20260818T000001-rule7-index",
            "operation_type": "review",
            "writes": [
                {
                    "path": "wiki/index.md",
                    "mode": "replace",
                    "content_file": str(staged_index.resolve()),
                }
            ],
        },
    )
    _run_vaultctl(
        vault, env, "plan", "--bundle", str(bundle_path), "--out", str(plan_path)
    )
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert [(write["mode"], write["path"]) for write in plan["writes"]] == [
        ("replace", "wiki/index.md")
    ]

    _run_vaultctl(
        vault,
        env,
        "apply",
        "--plan",
        str(plan_path),
        "--approved-plan-sha256",
        plan["approval_sha256"],
    )
    after = _lint(vault, env)
    assert after["counts"]["violation"] == EXPECTED_AFTER_VIOLATIONS
    assert _rule_counts(after) == EXPECTED_AFTER_RULE_COUNTS

    before_lines = before_bytes.splitlines(keepends=True)
    applied_lines = index_path.read_bytes().splitlines(keepends=True)
    assert [line for line in before_lines if line != ghost_line] == [
        line for line in applied_lines if line != unlisted_line
    ]
    assert before_lines.count(ghost_line) == 1
    assert applied_lines.count(ghost_line) == 0
    assert before_lines.count(unlisted_line) == 0
    assert applied_lines.count(unlisted_line) == 1


def test_rule3_move_plan_has_create_and_delete_without_apply(tmp_path: Path) -> None:
    vault = tmp_path / "fixture-vault"
    subprocess.run(["bash", str(FIXTURE_SCRIPT), str(vault)], check=True)
    env = os.environ.copy()
    env["XDG_STATE_HOME"] = str(tmp_path / "state")

    source = vault / "wiki/concepts/fixture-badtype.md"
    staging = tmp_path / "rule3" / "staging"
    staging.mkdir(parents=True)
    staged_page = staging / "fixture-badtype.md"
    staged_page.write_bytes(source.read_bytes())

    bundle_path = tmp_path / "rule3" / "bundle.json"
    plan_path = tmp_path / "rule3" / "plan.json"
    _write_json(
        bundle_path,
        {
            "schema": "vaultctl.bundle.v1",
            "operation_id": "review-20260818T000002-rule3-move",
            "operation_type": "review",
            "writes": [
                {
                    "path": "wiki/sources/fixture-badtype.md",
                    "mode": "create",
                    "content_file": str(staged_page.resolve()),
                },
                {"path": "wiki/concepts/fixture-badtype.md", "mode": "delete"},
            ],
        },
    )
    _run_vaultctl(
        vault, env, "plan", "--bundle", str(bundle_path), "--out", str(plan_path)
    )
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert [(write["mode"], write["path"]) for write in plan["writes"]] == [
        ("create", "wiki/sources/fixture-badtype.md"),
        ("delete", "wiki/concepts/fixture-badtype.md"),
    ]
    assert source.exists()
    assert not (vault / "wiki/sources/fixture-badtype.md").exists()
