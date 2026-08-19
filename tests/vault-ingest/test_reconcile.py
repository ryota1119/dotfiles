"""T14-4 の受け入れテスト。reconcile モードを Tx-A → Tx-B → Tx-C で通す。"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SCRIPT = ROOT / "scripts" / "make-ingest-fixture.sh"
SCRIPTS = ROOT / "dot_claude/skills/vault-ingest/scripts"
SCAN = SCRIPTS / "executable_scan_inbox.py"
BUILD = SCRIPTS / "executable_build_archive_bundle.py"
RELOCATE = SCRIPTS / "executable_build_ledger_relocate.py"
VERIFY = SCRIPTS / "executable_verify_archived.py"
LEDGER = "wiki/meta/ledgers/source-ledger.json"


def _vaultctl() -> list[str]:
    installed = Path.home() / ".local/bin/vaultctl"
    if installed.is_file() and os.access(installed, os.X_OK):
        return [str(installed)]
    uv = shutil.which("uv")
    if uv:
        return [uv, "run", "--project", str(ROOT / "vaultctl"), "vaultctl"]
    pytest.fail("vaultctl が見つかりません")


def _run(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(list(args), capture_output=True, text=True, check=False)
    if check:
        assert result.returncode == 0, result.stdout + result.stderr
    return result


def _apply(vault: Path, bundle: Path, work: Path, tag: str) -> str:
    plan = work / f"{tag}.plan.json"
    _run(*_vaultctl(), "--vault", str(vault), "plan", "--bundle", str(bundle), "--out", str(plan))
    approval = json.loads(plan.read_text(encoding="utf-8"))["approval_sha256"]
    result = _run(*_vaultctl(), "--vault", str(vault), "apply", "--plan", str(plan),
                  "--approved-plan-sha256", approval)
    return result.stdout


def _lint(vault: Path) -> dict:
    result = _run(*_vaultctl(), "--vault", str(vault), "lint", "--json", "--today", "2026-08-19",
                  check=False)
    return json.loads(result.stdout)["counts"]


@pytest.fixture
def ready(tmp_path: Path) -> tuple[Path, Path]:
    vault = tmp_path / "vault"
    subprocess.run(["bash", str(FIXTURE_SCRIPT), str(vault)], check=True, capture_output=True)
    for name in ("drifted-source.md", "orphan-page-source.md", "unledgered-source.md"):
        (vault / "inbox" / name).unlink()
    work = tmp_path / "work"
    (work / "staging").mkdir(parents=True)
    _run(sys.executable, str(SCAN), "--vault", str(vault), "--out", str(work / "queue.json"))
    return vault, work


def test_reconcile_end_to_end(ready) -> None:
    vault, work = ready
    before_lint = _lint(vault)
    before_ledger = json.loads((vault / LEDGER).read_text(encoding="utf-8"))

    _run(sys.executable, str(BUILD), "--queue", str(work / "queue.json"),
         "--out", str(work / "a.json"), "--operation-id", "ingest-20260819T120000-a")
    assert "state=complete" in _apply(vault, work / "a.json", work, "a")

    _run(sys.executable, str(RELOCATE), "--queue", str(work / "queue.json"),
         "--out", str(work / "b.json"), "--staging", str(work / "staging"),
         "--operation-id", "ingest-20260819T120100-b")
    assert "state=complete" in _apply(vault, work / "b.json", work, "b")

    _run(sys.executable, str(VERIFY), "--queue", str(work / "queue.json"),
         "--out", str(work / "c.json"), "--operation-id", "ingest-20260819T120200-c")
    assert "state=complete" in _apply(vault, work / "c.json", work, "c")

    # 条件3: reconcile はページを増やさないので lint は動かない
    assert _lint(vault) == before_lint

    after_ledger = json.loads((vault / LEDGER).read_text(encoding="utf-8"))
    entry = after_ledger["sources"]["src-fixture-reconcile00"]
    assert entry["origin"]["locator"] == ".raw/reconcile-source.md"

    # 条件2: locator 以外のキーが1つも変わっていない
    old_entry = before_ledger["sources"]["src-fixture-reconcile00"]
    for key in set(old_entry) | set(entry):
        if key == "origin":
            continue
        assert old_entry.get(key) == entry.get(key), f"{key} が変わっている"
    assert {k: v for k, v in old_entry["origin"].items() if k != "locator"} == \
           {k: v for k, v in entry["origin"].items() if k != "locator"}

    assert not (vault / "inbox/reconcile-source.md").exists()
    assert (vault / ".raw/reconcile-source.md").is_file()


def test_relocate_reports_changed_keys(ready) -> None:
    """書き換えたキーを出力に列挙する。意図しないキーが動いたら止まる。"""
    vault, work = ready
    _run(sys.executable, str(BUILD), "--queue", str(work / "queue.json"),
         "--out", str(work / "a.json"), "--operation-id", "ingest-20260819T120000-a")
    _apply(vault, work / "a.json", work, "a")
    result = _run(sys.executable, str(RELOCATE), "--queue", str(work / "queue.json"),
                  "--out", str(work / "b.json"), "--staging", str(work / "staging"),
                  "--operation-id", "ingest-20260819T120100-b")
    assert "sources.src-fixture-reconcile00.origin.locator" in result.stdout
    assert "inbox/reconcile-source.md" in result.stdout
    assert ".raw/reconcile-source.md" in result.stdout


def test_relocate_skips_url_origins(ready) -> None:
    """origin.kind が url のエントリは inbox に依存しないので触らない。"""
    vault, work = ready
    ledger_path = vault / LEDGER
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["sources"]["src-fixture-reconcile00"]["origin"] = {
        "kind": "url", "locator": "https://example.com/article"}
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2), encoding="utf-8")

    result = _run(sys.executable, str(RELOCATE), "--queue", str(work / "queue.json"),
                  "--out", str(work / "b.json"), "--staging", str(work / "staging"),
                  "--operation-id", "ingest-20260819T120100-b")
    assert "書き換える locator がありません" in result.stdout
    assert not (work / "b.json").exists()


def test_relocate_refuses_when_inconsistent(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    subprocess.run(["bash", str(FIXTURE_SCRIPT), str(vault)], check=True, capture_output=True)
    work = tmp_path / "work"
    (work / "staging").mkdir(parents=True)
    subprocess.run([sys.executable, str(SCAN), "--vault", str(vault),
                    "--out", str(work / "queue.json")], capture_output=True, check=False)
    result = _run(sys.executable, str(RELOCATE), "--queue", str(work / "queue.json"),
                  "--out", str(work / "b.json"), "--staging", str(work / "staging"),
                  "--operation-id", "ingest-20260819T120100-b", check=False)
    assert result.returncode != 0
    assert "不整合" in result.stderr
