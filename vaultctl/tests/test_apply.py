import os
from pathlib import Path

import pytest

from vaultctl.apply import (
    ApprovalMismatch,
    PreconditionError,
    apply_plan,
)
from vaultctl.hashing import sha256_file
from vaultctl.plan import build_plan

A_ORIGINAL = "A原本\n"
C_ORIGINAL = "C原本\n"
A_NEW = "A新版\n"
B_NEW = "B新規\n"
C_NEW = "C新版\n"


def make_fixture(txn_vault, tmp_path, operation_id="apply-20260817-0001"):
    """wiki/a.md(replace) / wiki/b.md(create) / wiki/c.md(replace) の3件を持つ plan を作る。

    戻り値は (plan, staging_dir)。
    """
    root = txn_vault.root
    (root / "wiki" / "a.md").write_text(A_ORIGINAL, encoding="utf-8")
    (root / "wiki" / "c.md").write_text(C_ORIGINAL, encoding="utf-8")

    staging = tmp_path / "staging"
    staging.mkdir(exist_ok=True)
    (staging / "a.md").write_text(A_NEW, encoding="utf-8")
    (staging / "b.md").write_text(B_NEW, encoding="utf-8")
    (staging / "c.md").write_text(C_NEW, encoding="utf-8")

    bundle = {
        "schema": "vaultctl.bundle.v1",
        "operation_id": operation_id,
        "operation_type": "ingest",
        "writes": [
            {"path": "wiki/a.md", "mode": "replace", "content_file": str(staging / "a.md")},
            {"path": "wiki/b.md", "mode": "create", "content_file": str(staging / "b.md")},
            {"path": "wiki/c.md", "mode": "replace", "content_file": str(staging / "c.md")},
        ],
    }
    return build_plan(txn_vault, bundle), staging


def test_apply_rejects_wrong_approval_hash(txn_vault, tmp_path: Path) -> None:
    """検証5: 承認ハッシュ不一致で ApprovalMismatch。"""
    plan, _ = make_fixture(txn_vault, tmp_path)
    root = txn_vault.root

    with pytest.raises(ApprovalMismatch):
        apply_plan(txn_vault, plan, "0" * 64)

    assert (root / "wiki" / "a.md").read_text(encoding="utf-8") == A_ORIGINAL
    assert (root / "wiki" / "c.md").read_text(encoding="utf-8") == C_ORIGINAL
    assert not (root / "wiki" / "b.md").exists()
    assert list(txn_vault.transactions_dir.iterdir()) == []


def test_apply_aborts_on_precondition_mismatch_without_touching_any_file(
    txn_vault, tmp_path: Path
) -> None:
    """検証2: plan 作成後に対象を外部から書き換えたら中断し、どのファイルも変更されない。"""
    plan, _ = make_fixture(txn_vault, tmp_path)
    root = txn_vault.root

    # plan 作成後に、vaultctl を通らない経路で wiki/c.md を書き換える
    tampered = "外部から書き換えた\n"
    (root / "wiki" / "c.md").write_text(tampered, encoding="utf-8")

    before = {
        "wiki/a.md": sha256_file(root / "wiki" / "a.md"),
        "wiki/c.md": sha256_file(root / "wiki" / "c.md"),
    }

    with pytest.raises(PreconditionError) as excinfo:
        apply_plan(txn_vault, plan, plan["approval_sha256"])

    assert "wiki/c.md" in str(excinfo.value)
    assert sha256_file(root / "wiki" / "a.md") == before["wiki/a.md"]
    assert sha256_file(root / "wiki" / "c.md") == before["wiki/c.md"]
    assert (root / "wiki" / "a.md").read_text(encoding="utf-8") == A_ORIGINAL
    assert (root / "wiki" / "c.md").read_text(encoding="utf-8") == tampered
    assert not (root / "wiki" / "b.md").exists()
    # トランザクションディレクトリすら作られていないこと
    assert list(txn_vault.transactions_dir.iterdir()) == []
    # ロックも残っていないこと
    assert not txn_vault.lock_path.exists()


def test_apply_aborts_when_create_target_already_exists(txn_vault, tmp_path: Path) -> None:
    plan, _ = make_fixture(txn_vault, tmp_path)
    root = txn_vault.root
    (root / "wiki" / "b.md").write_text("横から作られた\n", encoding="utf-8")

    with pytest.raises(PreconditionError):
        apply_plan(txn_vault, plan, plan["approval_sha256"])

    assert (root / "wiki" / "b.md").read_text(encoding="utf-8") == "横から作られた\n"
    assert (root / "wiki" / "a.md").read_text(encoding="utf-8") == A_ORIGINAL


def test_apply_aborts_when_replace_target_is_missing(txn_vault, tmp_path: Path) -> None:
    plan, _ = make_fixture(txn_vault, tmp_path)
    (txn_vault.root / "wiki" / "c.md").unlink()

    with pytest.raises(PreconditionError):
        apply_plan(txn_vault, plan, plan["approval_sha256"])

    assert list(txn_vault.transactions_dir.iterdir()) == []
