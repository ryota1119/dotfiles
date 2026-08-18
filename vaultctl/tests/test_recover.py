import json
import os
import signal
import subprocess
import sys
from pathlib import Path

import pytest

from vaultctl.apply import apply_plan
from vaultctl.hashing import sha256_file
from vaultctl.journal import open_transaction, read_journal, write_journal
from vaultctl.recover import (
    RecoveryResult,
    find_incomplete,
    recover_all,
    recover_transaction,
)
from test_apply import A_ORIGINAL, C_ORIGINAL, make_fixture


def _stage_interrupted_transaction(txn_vault, tmp_path: Path, operation_id: str) -> dict:
    """apply が wiki/a.md と wiki/b.md まで進んだところで止まった状態を、手で作る。

    戻り値は書き出したジャーナル dict。
    """
    plan, _ = make_fixture(txn_vault, tmp_path, operation_id=operation_id)
    root = txn_vault.root
    tx = open_transaction(txn_vault, operation_id)

    entries = []
    backup_no = 0
    for write in plan["writes"]:
        if write["mode"] == "create":
            backup = None
            original_mode = None
        else:
            backup_no += 1
            backup = f"{backup_no:04d}.original"
            original_mode = os.stat(root / write["path"]).st_mode & 0o7777
            (tx.backups_dir / backup).write_bytes((root / write["path"]).read_bytes())
        entries.append(
            {
                "path": write["path"],
                "mode": write["mode"],
                "backup": backup,
                "original_sha256": write["original_sha256"],
                "new_sha256": write.get("new_sha256"),
                "original_mode": original_mode,
                "new_mode": 0o600,
            }
        )

    # wiki/a.md と wiki/b.md までは書かれてしまっている状態を作る
    (root / "wiki" / "a.md").write_text("A新版\n", encoding="utf-8")
    (root / "wiki" / "b.md").write_text("B新規\n", encoding="utf-8")

    journal = {
        "schema": "vaultctl.transaction-journal.v1",
        "operation_id": operation_id,
        "operation_type": "ingest",
        "state": "pending",
        "approval_sha256": plan["approval_sha256"],
        "input_bundle_sha256": plan["input_bundle_sha256"],
        "created_epoch": 1.0,
        "completed_epoch": None,
        "applied": ["wiki/a.md", "wiki/b.md"],
        "writes": entries,
    }
    write_journal(tx, journal)
    return journal


def test_find_incomplete_detects_pending(txn_vault, tmp_path: Path) -> None:
    _stage_interrupted_transaction(txn_vault, tmp_path, "recover-0001")

    txs = find_incomplete(txn_vault)

    assert [tx.dir.name for tx in txs] == ["recover-0001"]


def test_find_incomplete_skips_complete_transactions(txn_vault, tmp_path: Path) -> None:
    plan, _ = make_fixture(txn_vault, tmp_path, operation_id="done-0001")
    apply_plan(txn_vault, plan, plan["approval_sha256"])

    assert find_incomplete(txn_vault) == []


def test_find_incomplete_detects_rolling_back(txn_vault, tmp_path: Path) -> None:
    journal = _stage_interrupted_transaction(txn_vault, tmp_path, "recover-0002")
    tx_dir = txn_vault.transactions_dir / "recover-0002"
    journal["state"] = "rolling-back"
    (tx_dir / "journal.json").write_text(
        json.dumps(journal, ensure_ascii=False), encoding="utf-8"
    )

    assert [tx.dir.name for tx in find_incomplete(txn_vault)] == ["recover-0002"]


def test_recover_transaction_restores_and_marks_rolled_back(txn_vault, tmp_path: Path) -> None:
    journal = _stage_interrupted_transaction(txn_vault, tmp_path, "recover-0003")
    root = txn_vault.root
    original_sha = {w["path"]: w["original_sha256"] for w in journal["writes"]}
    (tx,) = find_incomplete(txn_vault)

    result = recover_transaction(txn_vault, tx)

    assert isinstance(result, RecoveryResult)
    assert result.operation_id == "recover-0003"
    assert result.previous_state == "pending"
    assert result.restored == ["wiki/b.md", "wiki/a.md"]

    assert not (root / "wiki" / "b.md").exists()
    assert (root / "wiki" / "a.md").read_text(encoding="utf-8") == A_ORIGINAL
    assert (root / "wiki" / "c.md").read_text(encoding="utf-8") == C_ORIGINAL
    assert sha256_file(root / "wiki" / "a.md") == original_sha["wiki/a.md"]
    assert sha256_file(root / "wiki" / "c.md") == original_sha["wiki/c.md"]

    after = read_journal(tx.journal_path)
    assert after["state"] == "rolled-back"
    assert after["applied"] == []


def test_recover_transaction_is_idempotent(txn_vault, tmp_path: Path) -> None:
    _stage_interrupted_transaction(txn_vault, tmp_path, "recover-0004")
    (tx,) = find_incomplete(txn_vault)
    recover_transaction(txn_vault, tx)

    assert find_incomplete(txn_vault) == []


VICTIM_SCRIPT = '''"""テスト用: apply を N 回目の書き込み直前で SIGKILL する被験スクリプト。

argv[1] = vault root、argv[2] = plan.json のパス。
環境変数 VAULTCTL_TEST_KILL_BEFORE_WRITE = 何回目の atomic_write の直前で自殺するか（1始まり）。
"""

import json
import os
import signal
import sys
from pathlib import Path

import vaultctl.apply as apply_mod
from vaultctl.vault import resolve_vault


def main() -> int:
    vault_root = Path(sys.argv[1])
    plan_path = Path(sys.argv[2])
    kill_before = int(os.environ["VAULTCTL_TEST_KILL_BEFORE_WRITE"])

    plan = json.loads(plan_path.read_text(encoding="utf-8"))

    real_atomic_write = apply_mod.atomic_write
    counter = {"calls": 0}

    def suicidal(target, data, *, mode=apply_mod.DEFAULT_MODE):
        counter["calls"] += 1
        if counter["calls"] == kill_before:
            sys.stderr.write("killing self before write %d\\n" % counter["calls"])
            sys.stderr.flush()
            os.kill(os.getpid(), signal.SIGKILL)
        return real_atomic_write(target, data, mode=mode)

    apply_mod.atomic_write = suicidal

    vault = resolve_vault(str(vault_root))
    apply_mod.apply_plan(vault, plan, plan["approval_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
'''


def test_recover_after_sigkill_during_apply(txn_vault, tmp_path: Path) -> None:
    """検証1: SIGKILL で中断された apply を、親プロセスから recover_all で巻き戻す。"""
    plan, _ = make_fixture(txn_vault, tmp_path, operation_id="sigkill-0001")
    root = txn_vault.root
    original_sha = {w["path"]: w["original_sha256"] for w in plan["writes"]}

    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")

    script = tmp_path / "victim.py"
    script.write_text(VICTIM_SCRIPT, encoding="utf-8")

    env = dict(os.environ)
    env["VAULTCTL_TEST_KILL_BEFORE_WRITE"] = "3"  # wiki/a.md と wiki/b.md の後で死ぬ

    proc = subprocess.run(
        [sys.executable, str(script), str(root), str(plan_path)],
        env=env,
        capture_output=True,
    )

    # SIGKILL で落ちたこと
    assert proc.returncode == -signal.SIGKILL, proc.stderr.decode("utf-8", "replace")

    # 中断直後の状態: 2件だけ書かれ、ジャーナルは pending、ロックは残ったまま
    assert (root / "wiki" / "a.md").read_text(encoding="utf-8") == "A新版\n"
    assert (root / "wiki" / "b.md").read_text(encoding="utf-8") == "B新規\n"
    assert (root / "wiki" / "c.md").read_text(encoding="utf-8") == C_ORIGINAL
    journal_path = txn_vault.transactions_dir / "sigkill-0001" / "journal.json"
    assert read_journal(journal_path)["state"] == "pending"
    assert read_journal(journal_path)["applied"] == ["wiki/a.md", "wiki/b.md"]
    assert txn_vault.lock_path.exists()

    # 親から巻き戻す（死んだプロセスのロックは奪う）
    results = recover_all(txn_vault)

    assert [r.operation_id for r in results] == ["sigkill-0001"]
    assert results[0].previous_state == "pending"
    assert results[0].restored == ["wiki/b.md", "wiki/a.md"]

    assert not (root / "wiki" / "b.md").exists()
    assert sha256_file(root / "wiki" / "a.md") == original_sha["wiki/a.md"]
    assert sha256_file(root / "wiki" / "c.md") == original_sha["wiki/c.md"]
    assert (root / "wiki" / "a.md").read_text(encoding="utf-8") == A_ORIGINAL
    assert read_journal(journal_path)["state"] == "rolled-back"
    assert not txn_vault.lock_path.exists()
    assert find_incomplete(txn_vault) == []


def test_recover_all_returns_empty_when_nothing_incomplete(txn_vault, tmp_path: Path) -> None:
    plan, _ = make_fixture(txn_vault, tmp_path, operation_id="done-0002")
    apply_plan(txn_vault, plan, plan["approval_sha256"])

    assert recover_all(txn_vault) == []


def test_cli_recover_dry_run_changes_nothing(txn_vault, tmp_path: Path, capsys) -> None:
    from vaultctl import cli

    journal = _stage_interrupted_transaction(txn_vault, tmp_path, "recover-cli-0001")
    root = txn_vault.root
    before = {
        "a": (root / "wiki" / "a.md").read_text(encoding="utf-8"),
        "b": (root / "wiki" / "b.md").read_text(encoding="utf-8"),
        "c": (root / "wiki" / "c.md").read_text(encoding="utf-8"),
    }

    code = cli.main(["--vault", str(root), "recover", "--dry-run"])

    assert code == 0
    out = capsys.readouterr().out
    assert "recover-cli-0001" in out
    assert "pending" in out
    # 何も変更していない
    assert (root / "wiki" / "a.md").read_text(encoding="utf-8") == before["a"]
    assert (root / "wiki" / "b.md").read_text(encoding="utf-8") == before["b"]
    assert (root / "wiki" / "c.md").read_text(encoding="utf-8") == before["c"]
    assert read_journal(
        txn_vault.transactions_dir / "recover-cli-0001" / "journal.json"
    )["state"] == journal["state"] == "pending"
    assert [tx.dir.name for tx in find_incomplete(txn_vault)] == ["recover-cli-0001"]


def test_cli_recover_rolls_back(txn_vault, tmp_path: Path, capsys) -> None:
    from vaultctl import cli

    _stage_interrupted_transaction(txn_vault, tmp_path, "recover-cli-0002")
    root = txn_vault.root

    code = cli.main(["--vault", str(root), "recover"])

    assert code == 0
    assert "recover-cli-0002" in capsys.readouterr().out
    assert not (root / "wiki" / "b.md").exists()
    assert (root / "wiki" / "a.md").read_text(encoding="utf-8") == A_ORIGINAL
    assert read_journal(
        txn_vault.transactions_dir / "recover-cli-0002" / "journal.json"
    )["state"] == "rolled-back"
