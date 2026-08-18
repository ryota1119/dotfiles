from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess

import pytest
import yaml


ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SCRIPT = ROOT / "scripts" / "make-fixture-vault.sh"

EXPECTED_BEFORE_VIOLATIONS = 8
EXPECTED_AFTER_VIOLATIONS = 5
EXPECTED_BEFORE_RULE_COUNTS = {"2": 1, "3": 1, "4": 1, "5": 2, "6": 1, "7": 2}
EXPECTED_AFTER_RULE_COUNTS = {"2": 1, "3": 1, "5": 2, "6": 1}
EXPECTED_R9A_BEFORE_SUMMARY = {
    "concept": {"developing": 1, "evergreen": 3},
    "source": {"developing": 0, "evergreen": 2},
}
EXPECTED_R9A_AFTER_SUMMARY = {
    "concept": {"developing": 0, "evergreen": 4},
    "source": {"developing": 0, "evergreen": 2},
}


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


def _rule9a_summary(payload: dict) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {}
    pattern = re.compile(
        r"type=(?P<type>\w+) developing=(?P<developing>\d+) "
        r"evergreen=(?P<evergreen>\d+)"
    )
    for finding in payload["findings"]:
        if finding["rule"] != "9-a" or not finding["message"].startswith("昇格待ちキュー:"):
            continue
        match = pattern.search(finding["message"])
        assert match is not None
        summary[match.group("type")] = {
            "developing": int(match.group("developing")),
            "evergreen": int(match.group("evergreen")),
        }
    return summary


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _frontmatter_value(page: Path, key: str) -> str:
    for line in page.read_text(encoding="utf-8").splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip()
    pytest.fail(f"frontmatter に {key} がありません: {page}")


def _split_frontmatter_bytes(content: bytes) -> tuple[bytes, bytes]:
    assert content.startswith(b"---\n")
    closing = content.find(b"\n---\n", len(b"---\n"))
    assert closing != -1
    return content[len(b"---\n") : closing], content[closing + len(b"\n---\n") :]


def _frontmatter_dict(content: bytes) -> dict:
    frontmatter, _ = _split_frontmatter_bytes(content)
    parsed = yaml.safe_load(frontmatter.decode("utf-8"))
    assert isinstance(parsed, dict)
    return parsed


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


def test_rule9a_bundle_plan_apply_preserves_body_and_updates_summary(tmp_path: Path) -> None:
    vault = tmp_path / "fixture-vault"
    subprocess.run(["bash", str(FIXTURE_SCRIPT), str(vault)], check=True)
    env = os.environ.copy()
    env["XDG_STATE_HOME"] = str(tmp_path / "state")

    page = vault / "wiki/concepts/fixture-connector.md"
    evergreen_bytes = page.read_bytes()
    developing_bytes = evergreen_bytes.replace(
        b"status: evergreen\n", b"status: developing\n", 1
    )
    assert developing_bytes != evergreen_bytes
    page.write_bytes(developing_bytes)

    before = _lint(vault, env)
    assert before["counts"]["violation"] == EXPECTED_BEFORE_VIOLATIONS
    assert _rule_counts(before) == EXPECTED_BEFORE_RULE_COUNTS
    assert _rule9a_summary(before) == EXPECTED_R9A_BEFORE_SUMMARY

    staged_bytes = developing_bytes.replace(
        b"status: developing\n", b"status: evergreen\n", 1
    )
    staging = tmp_path / "rule9a" / "staging"
    staging.mkdir(parents=True)
    staged_page = staging / page.name
    staged_page.write_bytes(staged_bytes)

    bundle_path = tmp_path / "rule9a" / "bundle.json"
    plan_path = tmp_path / "rule9a" / "plan.json"
    _write_json(
        bundle_path,
        {
            "schema": "vaultctl.bundle.v1",
            "operation_id": "review-20260818T000003-rule9a-promote",
            "operation_type": "review",
            "writes": [
                {
                    "path": "wiki/concepts/fixture-connector.md",
                    "mode": "replace",
                    "content_file": str(staged_page.resolve()),
                }
            ],
        },
    )
    _run_vaultctl(
        vault, env, "plan", "--bundle", str(bundle_path), "--out", str(plan_path)
    )
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    assert [(write["mode"], write["path"]) for write in plan["writes"]] == [
        ("replace", "wiki/concepts/fixture-connector.md")
    ]

    before_frontmatter = _frontmatter_dict(developing_bytes)
    staged_frontmatter = _frontmatter_dict(staged_bytes)
    diff_keys = {
        key
        for key in before_frontmatter.keys() | staged_frontmatter.keys()
        if before_frontmatter.get(key) != staged_frontmatter.get(key)
    }
    assert diff_keys == {"status"}

    _, before_body = _split_frontmatter_bytes(developing_bytes)
    _, staged_body = _split_frontmatter_bytes(staged_bytes)
    before_body_sha256 = hashlib.sha256(before_body).hexdigest()
    staged_body_sha256 = hashlib.sha256(staged_body).hexdigest()
    assert before_body_sha256 == staged_body_sha256

    _run_vaultctl(
        vault,
        env,
        "apply",
        "--plan",
        str(plan_path),
        "--approved-plan-sha256",
        plan["approval_sha256"],
    )
    applied_bytes = page.read_bytes()
    applied_frontmatter = _frontmatter_dict(applied_bytes)
    applied_diff_keys = {
        key
        for key in before_frontmatter.keys() | applied_frontmatter.keys()
        if before_frontmatter.get(key) != applied_frontmatter.get(key)
    }
    assert applied_diff_keys == {"status"}

    _, applied_body = _split_frontmatter_bytes(applied_bytes)
    applied_body_sha256 = hashlib.sha256(applied_body).hexdigest()
    assert applied_body_sha256 == before_body_sha256

    after = _lint(vault, env)
    assert after["counts"]["violation"] == EXPECTED_BEFORE_VIOLATIONS
    assert _rule_counts(after) == EXPECTED_BEFORE_RULE_COUNTS
    assert _rule9a_summary(after) == EXPECTED_R9A_AFTER_SUMMARY
