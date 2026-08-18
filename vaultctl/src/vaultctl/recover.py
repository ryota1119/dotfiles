"""未完了トランザクションの検出と巻き戻し（設計書 3節 `vaultctl recover`）。"""

from __future__ import annotations

from dataclasses import dataclass

from vaultctl.apply import restore_write
from vaultctl.journal import Transaction, list_transactions, read_journal, set_state
from vaultctl.lock import hold_lock
from vaultctl.vault import Vault

INCOMPLETE_STATES = ("pending", "rolling-back")

__all__ = [
    "RecoveryResult",
    "INCOMPLETE_STATES",
    "find_incomplete",
    "recover_all",
    "recover_transaction",
]


@dataclass(frozen=True)
class RecoveryResult:
    operation_id: str
    previous_state: str
    restored: list[str]


def find_incomplete(vault: Vault) -> list[Transaction]:
    """`state` が pending / rolling-back のトランザクションを返す。"""
    incomplete: list[Transaction] = []
    for tx in list_transactions(vault):
        if not tx.journal_path.is_file():
            continue
        journal = read_journal(tx.journal_path)
        if journal.get("state") in INCOMPLETE_STATES:
            incomplete.append(tx)
    return incomplete


def recover_transaction(vault: Vault, tx: Transaction) -> RecoveryResult:
    """`applied` に載っているぶんを逆順に戻し、state を rolled-back にする。"""
    journal = read_journal(tx.journal_path)
    previous_state = journal["state"]
    journal = set_state(tx, journal, "rolling-back")

    entries = {e["path"]: e for e in journal["writes"]}
    restored: list[str] = []
    for relpath in reversed(list(journal.get("applied", []))):
        restore_write(vault, tx, entries[relpath])
        restored.append(relpath)

    journal["applied"] = []
    set_state(tx, journal, "rolled-back")
    return RecoveryResult(
        operation_id=journal["operation_id"],
        previous_state=previous_state,
        restored=restored,
    )


def recover_all(vault: Vault) -> list[RecoveryResult]:
    """未完了トランザクションを新しい順に巻き戻す。

    ロックは1回だけ取る。落ちたプロセスが残した stale lock は、`lock.acquire` の
    PID 生存確認により奪われる（設計書 4.2）。
    """
    if not find_incomplete(vault):
        return []
    results: list[RecoveryResult] = []
    with hold_lock(vault, "recover"):
        for tx in reversed(find_incomplete(vault)):
            results.append(recover_transaction(vault, tx))
    return results
