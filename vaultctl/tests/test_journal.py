import json

import pytest

from vaultctl.journal import (
    JOURNAL_SCHEMA,
    Transaction,
    list_transactions,
    open_transaction,
    read_journal,
    set_state,
    write_journal,
)
from vaultctl.vault import VaultError


def _journal(operation_id: str) -> dict:
    return {
        "schema": JOURNAL_SCHEMA,
        "operation_id": operation_id,
        "operation_type": "ingest",
        "state": "pending",
        "approval_sha256": "a" * 64,
        "input_bundle_sha256": "b" * 64,
        "created_epoch": 1.0,
        "completed_epoch": None,
        "applied": [],
        "writes": [
            {
                "path": "wiki/index.md",
                "mode": "replace",
                "backup": "0001.original",
                "original_sha256": "c" * 64,
                "new_sha256": "d" * 64,
                "original_mode": 384,
                "new_mode": 384,
            }
        ],
    }


def test_open_transaction_creates_directories(txn_vault) -> None:
    tx = open_transaction(txn_vault, "ingest-20260817-0001")

    assert isinstance(tx, Transaction)
    assert tx.dir == txn_vault.transactions_dir / "ingest-20260817-0001"
    assert tx.dir.is_dir()
    assert tx.backups_dir == tx.dir / "backups"
    assert tx.backups_dir.is_dir()
    assert tx.journal_path == tx.dir / "journal.json"
    assert not tx.journal_path.exists()


def test_open_transaction_rejects_duplicate_operation_id(txn_vault) -> None:
    open_transaction(txn_vault, "ingest-20260817-0001")

    with pytest.raises(VaultError):
        open_transaction(txn_vault, "ingest-20260817-0001")


def test_write_and_read_journal_roundtrip(txn_vault) -> None:
    tx = open_transaction(txn_vault, "ingest-20260817-0002")
    journal = _journal("ingest-20260817-0002")

    write_journal(tx, journal)

    assert read_journal(tx.journal_path) == journal
    assert json.loads(tx.journal_path.read_text(encoding="utf-8"))["schema"] == JOURNAL_SCHEMA


def test_set_state_writes_back_and_returns_updated(txn_vault) -> None:
    tx = open_transaction(txn_vault, "ingest-20260817-0003")
    journal = _journal("ingest-20260817-0003")
    write_journal(tx, journal)

    updated = set_state(tx, journal, "complete")

    assert updated["state"] == "complete"
    assert read_journal(tx.journal_path)["state"] == "complete"
    assert journal["state"] == "pending"


def test_set_state_rejects_unknown_state(txn_vault) -> None:
    tx = open_transaction(txn_vault, "ingest-20260817-0004")
    journal = _journal("ingest-20260817-0004")
    write_journal(tx, journal)

    with pytest.raises(VaultError):
        set_state(tx, journal, "finished")


def test_list_transactions_returns_all_in_name_order(txn_vault) -> None:
    open_transaction(txn_vault, "b-op")
    open_transaction(txn_vault, "a-op")

    txs = list_transactions(txn_vault)

    assert [tx.dir.name for tx in txs] == ["a-op", "b-op"]


def test_list_transactions_on_empty_state_dir(txn_vault) -> None:
    assert list_transactions(txn_vault) == []
