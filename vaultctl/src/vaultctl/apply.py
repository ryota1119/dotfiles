"""plan の適用とロールバック（設計書 4.3）。"""

from __future__ import annotations

import os
import time
from pathlib import Path

from vaultctl import atomic as _atomic
from vaultctl.atomic import atomic_write, backup_file, fsync_dir
from vaultctl.hashing import sha256_file
from vaultctl.journal import (
    JOURNAL_SCHEMA,
    Transaction,
    open_transaction,
    set_state,
    write_journal,
)
from vaultctl.lock import hold_lock
from vaultctl.plan import plan_approval_sha256
from vaultctl.vault import Vault

DEFAULT_MODE = 0o600

__all__ = [
    "ApplyError",
    "ApprovalMismatch",
    "PreconditionError",
    "DEFAULT_MODE",
    "apply_plan",
    "restore_write",
]


class ApplyError(Exception):
    ...


class ApprovalMismatch(ApplyError):
    ...


class PreconditionError(ApplyError):
    ...


def _target(vault: Vault, relpath: str) -> Path:
    return vault.root / relpath


def verify_approval(plan: dict, approved_sha256: str) -> str:
    """plan を再ハッシュし、渡された承認ハッシュと一致することを確認する（手順1）。"""
    actual = plan_approval_sha256(plan)
    if actual != approved_sha256:
        raise ApprovalMismatch(
            f"承認ハッシュが一致しない: plan={actual} approved={approved_sha256}"
        )
    recorded = plan.get("approval_sha256")
    if recorded is not None and recorded != actual:
        raise ApprovalMismatch(
            f"plan の approval_sha256 が本文と一致しない: recorded={recorded} actual={actual}"
        )
    return actual


def check_preconditions(vault: Vault, plan: dict) -> None:
    """全対象の現在 SHA256 を original_sha256 と照合する（手順3）。1つでも違えば中断。"""
    for write in plan["writes"]:
        relpath = write["path"]
        target = _target(vault, relpath)
        if write["mode"] == "create":
            if target.exists():
                raise PreconditionError(f"create 対象が既に存在する: {relpath}")
            continue
        if not target.is_file():
            raise PreconditionError(f"{write['mode']} 対象が存在しない: {relpath}")
        actual = sha256_file(target)
        if actual != write["original_sha256"]:
            raise PreconditionError(
                f"プレコンディション不一致: {relpath} "
                f"expected={write['original_sha256']} actual={actual}"
            )


def build_journal(plan: dict, *, created_epoch: float) -> dict:
    """state=pending のジャーナルを組み立てる（手順4）。"""
    entries: list[dict] = []
    backup_no = 0
    for write in plan["writes"]:
        if write["mode"] == "create":
            backup = None
        else:
            backup_no += 1
            backup = f"{backup_no:04d}.original"
        entries.append(
            {
                "path": write["path"],
                "mode": write["mode"],
                "backup": backup,
                "original_sha256": write["original_sha256"],
                "new_sha256": write.get("new_sha256"),
                "original_mode": None,
                "new_mode": None,
            }
        )
    return {
        "schema": JOURNAL_SCHEMA,
        "operation_id": plan["operation_id"],
        "operation_type": plan["operation_type"],
        "state": "pending",
        "approval_sha256": plan["approval_sha256"],
        "input_bundle_sha256": plan["input_bundle_sha256"],
        "created_epoch": created_epoch,
        "completed_epoch": None,
        "applied": [],
        "writes": entries,
    }


def _apply_one(vault: Vault, write: dict, entry: dict) -> None:
    target = _target(vault, write["path"])
    if write["mode"] == "delete":
        target.unlink()
        fsync_dir(target.parent)
        entry["new_mode"] = None
        return
    data = Path(write["content_file"]).read_bytes()
    mode = entry["original_mode"] if entry["original_mode"] is not None else DEFAULT_MODE
    atomic_write(target, data, mode=mode)
    entry["new_mode"] = os.stat(target).st_mode & 0o7777


def restore_write(vault: Vault, tx: Transaction, entry: dict) -> None:
    """ジャーナルの writes エントリ1件を原状へ戻す。

    ロールバック経路は monkeypatch 対象になりうるモジュールグローバルの
    `atomic_write` ではなく `_atomic.atomic_write` を直接使う（巻き戻しは常に本物で行う）。
    """
    target = _target(vault, entry["path"])
    if entry["mode"] == "create":
        if target.exists():
            target.unlink()
            fsync_dir(target.parent)
        return
    backup = tx.backups_dir / entry["backup"]
    data = backup.read_bytes()
    mode = entry["original_mode"] if entry["original_mode"] is not None else DEFAULT_MODE
    _atomic.atomic_write(target, data, mode=mode)
    if entry["original_mode"] is not None:
        os.chmod(target, entry["original_mode"])


def _rollback(vault: Vault, tx: Transaction, journal: dict) -> dict:
    """適用済みを逆順に戻す（手順: 失敗時）。"""
    journal = set_state(tx, journal, "rolling-back")
    entries = {e["path"]: e for e in journal["writes"]}
    for relpath in reversed(list(journal["applied"])):
        restore_write(vault, tx, entries[relpath])
    journal["applied"] = []
    return set_state(tx, journal, "rolled-back")


def apply_plan(vault: Vault, plan: dict, approved_sha256: str) -> dict:
    verify_approval(plan, approved_sha256)
    if plan.get("vault_id") not in (None, vault.vault_id):
        raise ApplyError(
            f"plan の vault_id が対象 vault と異なる: {plan.get('vault_id')} != {vault.vault_id}"
        )
    with hold_lock(vault, plan["operation_id"]):
        check_preconditions(vault, plan)

        tx = open_transaction(vault, plan["operation_id"])
        journal = build_journal(plan, created_epoch=time.time())
        entries = {e["path"]: e for e in journal["writes"]}

        for write in plan["writes"]:
            entry = entries[write["path"]]
            if entry["backup"] is None:
                continue
            entry["original_mode"] = os.stat(_target(vault, write["path"])).st_mode & 0o7777

        write_journal(tx, journal)

        for write in plan["writes"]:
            entry = entries[write["path"]]
            if entry["backup"] is None:
                continue
            backup_file(_target(vault, write["path"]), tx.backups_dir / entry["backup"])

        try:
            for write in plan["writes"]:
                entry = entries[write["path"]]
                _apply_one(vault, write, entry)
                journal["applied"].append(write["path"])
                write_journal(tx, journal)
        except BaseException:
            _rollback(vault, tx, journal)
            raise

        journal["completed_epoch"] = time.time()
        return set_state(tx, journal, "complete")
