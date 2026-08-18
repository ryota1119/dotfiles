"""トランザクションジャーナルの読み書き（設計書 4.4）。"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from vaultctl.atomic import atomic_write, fsync_dir
from vaultctl.vault import Vault, VaultError

JOURNAL_SCHEMA = "vaultctl.transaction-journal.v1"
JOURNAL_STATES = ("pending", "rolling-back", "rolled-back", "complete")

__all__ = [
    "JOURNAL_SCHEMA",
    "JOURNAL_STATES",
    "Transaction",
    "open_transaction",
    "write_journal",
    "read_journal",
    "set_state",
    "list_transactions",
]


@dataclass(frozen=True)
class Transaction:
    dir: Path
    journal_path: Path
    backups_dir: Path


def _transaction(tx_dir: Path) -> Transaction:
    return Transaction(
        dir=tx_dir,
        journal_path=tx_dir / "journal.json",
        backups_dir=tx_dir / "backups",
    )


def open_transaction(vault: Vault, operation_id: str) -> Transaction:
    """新しいトランザクションディレクトリを作る。同一 operation_id が既にあれば失敗する。"""
    tx_dir = vault.transactions_dir / operation_id
    try:
        tx_dir.mkdir(parents=True)
    except FileExistsError as exc:
        raise VaultError(f"トランザクションが既に存在する: {operation_id}") from exc
    tx = _transaction(tx_dir)
    tx.backups_dir.mkdir()
    fsync_dir(tx.dir)
    fsync_dir(vault.transactions_dir)
    return tx


def write_journal(tx: Transaction, journal: dict) -> None:
    data = json.dumps(journal, sort_keys=True, ensure_ascii=False, indent=2)
    atomic_write(tx.journal_path, (data + "\n").encode("utf-8"), mode=0o600)


def read_journal(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def set_state(tx: Transaction, journal: dict, state: str) -> dict:
    if state not in JOURNAL_STATES:
        raise VaultError(f"未知のジャーナル状態: {state}")
    updated = dict(journal)
    updated["state"] = state
    write_journal(tx, updated)
    return updated


def list_transactions(vault: Vault) -> list[Transaction]:
    if not vault.transactions_dir.is_dir():
        return []
    return [
        _transaction(entry)
        for entry in sorted(vault.transactions_dir.iterdir(), key=lambda p: p.name)
        if entry.is_dir()
    ]
