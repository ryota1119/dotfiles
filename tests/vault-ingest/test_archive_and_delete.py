"""T14-2 / T14-3 の受け入れテスト。

退避（Tx-A）と削除（Tx-C）を別トランザクションとして扱い、削除の前に
「原本が `.raw/` に確実に入っている」ことを実測で確かめる。**1件でも不一致が
あれば全件中止する**という性質をテストで固定するのが主目的。
"""

from __future__ import annotations

import hashlib
import importlib.util
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
VERIFY = SCRIPTS / "executable_verify_archived.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def verify_mod():
    return _load(VERIFY, "verify_archived")


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


@pytest.fixture
def ready(tmp_path: Path) -> tuple[Path, Path]:
    """不整合を取り除き、reconcile 1件だけにした vault と作業ディレクトリを返す。"""
    vault = tmp_path / "vault"
    subprocess.run(["bash", str(FIXTURE_SCRIPT), str(vault)], check=True, capture_output=True)
    for name in ("drifted-source.md", "orphan-page-source.md", "unledgered-source.md"):
        (vault / "inbox" / name).unlink()
    work = tmp_path / "work"
    work.mkdir()
    _run(sys.executable, str(SCAN), "--vault", str(vault), "--out", str(work / "queue.json"))
    return vault, work


def _lint_counts(vault: Path) -> dict:
    result = subprocess.run(
        [*_vaultctl(), "--vault", str(vault), "lint", "--json", "--today", "2026-08-19"],
        capture_output=True, text=True, check=False,
    )
    return json.loads(result.stdout)["counts"]


def _apply(vault: Path, bundle: Path, work: Path, tag: str) -> subprocess.CompletedProcess[str]:
    plan = work / f"{tag}-plan.json"
    _run(*_vaultctl(), "--vault", str(vault), "plan", "--bundle", str(bundle), "--out", str(plan))
    approval = json.loads(plan.read_text(encoding="utf-8"))["approval_sha256"]
    return _run(*_vaultctl(), "--vault", str(vault), "apply", "--plan", str(plan),
                "--approved-plan-sha256", approval, check=False)


def _archive(vault: Path, work: Path, operation_id: str = "ingest-20260819T110000-archive") -> Path:
    bundle = work / "archive.json"
    _run(sys.executable, str(BUILD), "--queue", str(work / "queue.json"),
         "--out", str(bundle), "--operation-id", operation_id)
    return bundle


# --- T14-2: 退避 -------------------------------------------------------------


def test_archive_bundle_is_create_only(ready) -> None:
    vault, work = ready
    bundle = json.loads(_archive(vault, work).read_text(encoding="utf-8"))
    assert bundle["writes"], "退避対象が空"
    assert all(w["mode"] == "create" for w in bundle["writes"])
    assert all(w["path"].startswith(".raw/") for w in bundle["writes"])
    assert all(Path(w["content_file"]).is_absolute() for w in bundle["writes"])


def test_archive_refuses_when_inconsistent(tmp_path: Path) -> None:
    """不整合が残っているうちは退避 bundle を作らない。"""
    vault = tmp_path / "vault"
    subprocess.run(["bash", str(FIXTURE_SCRIPT), str(vault)], check=True, capture_output=True)
    work = tmp_path / "work"
    work.mkdir()
    subprocess.run([sys.executable, str(SCAN), "--vault", str(vault),
                    "--out", str(work / "queue.json")], capture_output=True, check=False)
    result = _run(sys.executable, str(BUILD), "--queue", str(work / "queue.json"),
                  "--out", str(work / "a.json"), "--operation-id", "ingest-20260819T110000-a",
                  check=False)
    assert result.returncode != 0
    assert "不整合" in result.stderr
    assert not (work / "a.json").exists()


def test_archive_preserves_bytes_and_lint(ready) -> None:
    vault, work = ready
    before = _lint_counts(vault)
    inbox_files = sorted(p.name for p in (vault / "inbox").iterdir())
    result = _apply(vault, _archive(vault, work), work, "archive")
    assert "state=complete" in result.stdout

    assert _lint_counts(vault) == before, ".raw/ への create が lint を動かしている"
    assert sorted(p.name for p in (vault / "inbox").iterdir()) == inbox_files, \
        "退避で inbox が消えている"
    raw = vault / ".raw/reconcile-source.md"
    inbox = vault / "inbox/reconcile-source.md"
    assert raw.read_bytes() == inbox.read_bytes()


def test_archiving_twice_stops(ready) -> None:
    """同名衝突は連番で回避せず停止する。"""
    vault, work = ready
    _apply(vault, _archive(vault, work), work, "archive")
    result = _run(sys.executable, str(BUILD), "--queue", str(work / "queue.json"),
                  "--out", str(work / "again.json"),
                  "--operation-id", "ingest-20260819T111000-archive", check=False)
    assert result.returncode != 0
    assert "既に存在します" in result.stderr
    assert "二度退避" in result.stderr


# --- T14-3: 削除 -------------------------------------------------------------


def test_delete_blocked_when_archive_is_modified(ready) -> None:
    """`.raw/` を1バイト変えたら全件中止。"""
    vault, work = ready
    _apply(vault, _archive(vault, work), work, "archive")
    with (vault / ".raw/reconcile-source.md").open("ab") as handle:
        handle.write(b"X")
    result = _run(sys.executable, str(VERIFY), "--queue", str(work / "queue.json"),
                  "--out", str(work / "del.json"),
                  "--operation-id", "ingest-20260819T112000-d", check=False)
    assert result.returncode == 1
    assert "全件について削除を中止" in result.stdout
    assert not (work / "del.json").exists()


def test_delete_blocked_when_archive_is_missing(ready) -> None:
    vault, work = ready
    _apply(vault, _archive(vault, work), work, "archive")
    (vault / ".raw/reconcile-source.md").unlink()
    result = _run(sys.executable, str(VERIFY), "--queue", str(work / "queue.json"), check=False)
    assert result.returncode == 1
    assert "退避先が実在しません" in result.stdout


def test_delete_blocked_on_drive_conflict_copy(ready) -> None:
    vault, work = ready
    _apply(vault, _archive(vault, work), work, "archive")
    (vault / ".raw/reconcile-source (1).md").write_text("conflict", encoding="utf-8")
    result = _run(sys.executable, str(VERIFY), "--queue", str(work / "queue.json"), check=False)
    assert result.returncode == 1
    assert "競合コピー" in result.stdout


def test_verify_recomputes_hashes_instead_of_trusting_queue(ready) -> None:
    """queue.json に書かれたハッシュを信じない。

    queue の値を改竄しても検証結果が変わらないことで、実読みしていることを示す。
    """
    vault, work = ready
    _apply(vault, _archive(vault, work), work, "archive")
    queue_path = work / "queue.json"
    queue = json.loads(queue_path.read_text(encoding="utf-8"))
    for item in queue["items"]:
        item["sha256"] = "0" * 64
    queue_path.write_text(json.dumps(queue, ensure_ascii=False), encoding="utf-8")
    result = _run(sys.executable, str(VERIFY), "--queue", str(queue_path), check=False)
    assert result.returncode == 0, result.stdout
    assert "SHA256 が一致" in result.stdout


def test_delete_bundle_is_delete_only_and_applies(ready) -> None:
    vault, work = ready
    _apply(vault, _archive(vault, work), work, "archive")
    operation_id = "ingest-20260819T112000-delete"
    _run(sys.executable, str(VERIFY), "--queue", str(work / "queue.json"),
         "--out", str(work / "del.json"), "--operation-id", operation_id,
         "--presentation", str(work / "pres.md"))

    bundle = json.loads((work / "del.json").read_text(encoding="utf-8"))
    assert bundle["writes"]
    assert all(w["mode"] == "delete" for w in bundle["writes"])
    assert all(w["path"].startswith("inbox/") for w in bundle["writes"])

    before = _lint_counts(vault)
    result = _apply(vault, work / "del.json", work, "delete")
    assert "state=complete" in result.stdout
    assert not (vault / "inbox/reconcile-source.md").exists()
    assert (vault / ".raw/reconcile-source.md").is_file(), "退避先まで消えている"
    assert _lint_counts(vault) == before, "inbox からの delete が lint を動かしている"


def test_presentation_lists_every_target(ready) -> None:
    """件数の要約でなく、削除対象を1件ずつ全件列挙する（規約3.2の2）。"""
    vault, work = ready
    _apply(vault, _archive(vault, work), work, "archive")
    _run(sys.executable, str(VERIFY), "--queue", str(work / "queue.json"),
         "--out", str(work / "del.json"), "--operation-id", "ingest-20260819T112000-delete",
         "--presentation", str(work / "pres.md"))
    text = (work / "pres.md").read_text(encoding="utf-8")
    assert "**inbox/reconcile-source.md**" in text, "削除行が太字で列挙されていない"
    assert "backups/" in text, "復旧手段が書かれていない"
    assert "git 管理下にない" in text


def test_journal_keeps_the_original_after_delete(ready) -> None:
    vault, work = ready
    _apply(vault, _archive(vault, work), work, "archive")
    operation_id = "ingest-20260819T112000-delete"
    _run(sys.executable, str(VERIFY), "--queue", str(work / "queue.json"),
         "--out", str(work / "del.json"), "--operation-id", operation_id)
    original = (vault / "inbox/reconcile-source.md").read_bytes()
    _apply(vault, work / "del.json", work, "delete")

    state = Path.home() / ".local/state/vaultctl"
    backups = list(state.glob(f"*/transactions/{operation_id}/backups/*.original"))
    assert backups, "journal に原本が退避されていない"
    assert any(b.read_bytes() == original for b in backups)
