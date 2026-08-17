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


from vaultctl.apply import DEFAULT_MODE
from vaultctl.journal import JOURNAL_SCHEMA, read_journal


def test_apply_writes_all_files_and_completes_journal(txn_vault, tmp_path: Path) -> None:
    plan, _ = make_fixture(txn_vault, tmp_path)
    root = txn_vault.root

    journal = apply_plan(txn_vault, plan, plan["approval_sha256"])

    assert (root / "wiki" / "a.md").read_text(encoding="utf-8") == A_NEW
    assert (root / "wiki" / "b.md").read_text(encoding="utf-8") == B_NEW
    assert (root / "wiki" / "c.md").read_text(encoding="utf-8") == C_NEW

    assert journal["schema"] == JOURNAL_SCHEMA
    assert journal["state"] == "complete"
    assert journal["operation_id"] == "apply-20260817-0001"
    assert journal["operation_type"] == "ingest"
    assert journal["applied"] == ["wiki/a.md", "wiki/b.md", "wiki/c.md"]
    assert journal["approval_sha256"] == plan["approval_sha256"]
    assert journal["input_bundle_sha256"] == plan["input_bundle_sha256"]
    assert isinstance(journal["completed_epoch"], float)

    on_disk = read_journal(txn_vault.transactions_dir / "apply-20260817-0001" / "journal.json")
    assert on_disk == journal


def test_apply_records_backups_only_for_existing_originals(txn_vault, tmp_path: Path) -> None:
    plan, _ = make_fixture(txn_vault, tmp_path)

    journal = apply_plan(txn_vault, plan, plan["approval_sha256"])

    by_path = {w["path"]: w for w in journal["writes"]}
    assert by_path["wiki/a.md"]["backup"] == "0001.original"
    assert by_path["wiki/c.md"]["backup"] == "0002.original"
    assert by_path["wiki/b.md"]["backup"] is None

    backups = txn_vault.transactions_dir / "apply-20260817-0001" / "backups"
    assert sorted(p.name for p in backups.iterdir()) == ["0001.original", "0002.original"]
    assert (backups / "0001.original").read_text(encoding="utf-8") == A_ORIGINAL
    assert (backups / "0002.original").read_text(encoding="utf-8") == C_ORIGINAL


def test_apply_handles_delete_mode(txn_vault, tmp_path: Path) -> None:
    root = txn_vault.root
    (root / "inbox" / "old.html").write_text("捨てる\n", encoding="utf-8")
    bundle = {
        "schema": "vaultctl.bundle.v1",
        "operation_id": "apply-20260817-0002",
        "operation_type": "ingest",
        "writes": [{"path": "inbox/old.html", "mode": "delete"}],
    }
    plan = build_plan(txn_vault, bundle)

    journal = apply_plan(txn_vault, plan, plan["approval_sha256"])

    assert not (root / "inbox" / "old.html").exists()
    assert journal["applied"] == ["inbox/old.html"]
    entry = journal["writes"][0]
    assert entry["new_sha256"] is None
    assert entry["new_mode"] is None
    assert entry["backup"] == "0001.original"
    backup = txn_vault.transactions_dir / "apply-20260817-0002" / "backups" / "0001.original"
    assert backup.read_text(encoding="utf-8") == "捨てる\n"


def test_apply_holds_lock_while_writing(txn_vault, tmp_path: Path, monkeypatch) -> None:
    """apply 中はロックが取られていること（hold_lock 経由）。"""
    import vaultctl.apply as apply_mod

    real_atomic_write = apply_mod.atomic_write
    lock_seen: list[bool] = []

    def spy(target, data, *, mode=DEFAULT_MODE):
        lock_seen.append(txn_vault.lock_path.exists())
        return real_atomic_write(target, data, mode=mode)

    monkeypatch.setattr(apply_mod, "atomic_write", spy)

    plan, _ = make_fixture(txn_vault, tmp_path)
    apply_plan(txn_vault, plan, plan["approval_sha256"])

    assert lock_seen == [True, True, True]
    # 終了後は解放されている
    assert not txn_vault.lock_path.exists()


def test_apply_rejects_duplicate_operation_id(txn_vault, tmp_path: Path) -> None:
    """同一 operation_id のトランザクションが既にあれば拒否する。

    設計書 4.3 の手順は「3 プレコンディション照合 → 4 ジャーナルを pending で書く」の順
    なので、同じ plan を素で2回流すとプレコンディション不一致（`PreconditionError`）が
    先に出て重複検出まで届かない。重複ガード自体を見るため、プレコンディションが成立した
    ままトランザクションディレクトリだけが存在する状態を作る。
    """
    from vaultctl.journal import open_transaction
    from vaultctl.vault import VaultError

    plan, _ = make_fixture(txn_vault, tmp_path)
    open_transaction(txn_vault, plan["operation_id"])

    with pytest.raises(VaultError):
        apply_plan(txn_vault, plan, plan["approval_sha256"])


def test_apply_replay_of_same_plan_fails_preconditions(txn_vault, tmp_path: Path) -> None:
    """適用済みの plan をもう一度流すと、重複検出より先にプレコンディションで止まる。"""
    plan, _ = make_fixture(txn_vault, tmp_path)
    apply_plan(txn_vault, plan, plan["approval_sha256"])

    with pytest.raises(PreconditionError):
        apply_plan(txn_vault, plan, plan["approval_sha256"])


class BoomError(RuntimeError):
    """テスト用: N回目の atomic_write で送出する。"""


def fail_on_nth_write(monkeypatch, n: int) -> dict:
    """`vaultctl.apply.atomic_write` を「n回目の呼び出しで BoomError を投げる」ラッパに差し替える。

    ロールバック経路は `vaultctl.apply._atomic.atomic_write` を使うため、この差し替えの
    影響を受けない。戻り値はカウンタ dict（`counter["calls"]` で実呼び出し回数を見る）。
    """
    import vaultctl.apply as apply_mod

    real_atomic_write = apply_mod.atomic_write
    counter = {"calls": 0}

    def flaky(target, data, *, mode=DEFAULT_MODE):
        counter["calls"] += 1
        if counter["calls"] == n:
            raise BoomError(f"{n}回目の書き込みで失敗させた: {target}")
        return real_atomic_write(target, data, mode=mode)

    monkeypatch.setattr(apply_mod, "atomic_write", flaky)
    return counter


def test_rollback_removes_created_file_and_restores_sha256(
    txn_vault, tmp_path: Path, monkeypatch
) -> None:
    """検証6・7: mode=create を含むトランザクションのロールバック。"""
    plan, _ = make_fixture(txn_vault, tmp_path)
    root = txn_vault.root

    original_sha = {w["path"]: w["original_sha256"] for w in plan["writes"]}
    counter = fail_on_nth_write(monkeypatch, 3)  # wiki/a.md, wiki/b.md の後で失敗させる

    with pytest.raises(BoomError):
        apply_plan(txn_vault, plan, plan["approval_sha256"])

    assert counter["calls"] == 3

    # 検証6: mode=create で作られたファイルが削除されている
    assert not (root / "wiki" / "b.md").exists()

    # 検証7: 全対象の SHA256 が original_sha256 に戻っている
    assert sha256_file(root / "wiki" / "a.md") == original_sha["wiki/a.md"]
    assert sha256_file(root / "wiki" / "c.md") == original_sha["wiki/c.md"]
    assert (root / "wiki" / "a.md").read_text(encoding="utf-8") == A_ORIGINAL
    assert (root / "wiki" / "c.md").read_text(encoding="utf-8") == C_ORIGINAL

    journal = read_journal(txn_vault.transactions_dir / "apply-20260817-0001" / "journal.json")
    assert journal["state"] == "rolled-back"
    assert journal["applied"] == []
    assert not txn_vault.lock_path.exists()


def test_rollback_on_first_write_leaves_everything_untouched(
    txn_vault, tmp_path: Path, monkeypatch
) -> None:
    plan, _ = make_fixture(txn_vault, tmp_path)
    root = txn_vault.root
    original_sha = {w["path"]: w["original_sha256"] for w in plan["writes"]}
    fail_on_nth_write(monkeypatch, 1)

    with pytest.raises(BoomError):
        apply_plan(txn_vault, plan, plan["approval_sha256"])

    assert sha256_file(root / "wiki" / "a.md") == original_sha["wiki/a.md"]
    assert sha256_file(root / "wiki" / "c.md") == original_sha["wiki/c.md"]
    assert not (root / "wiki" / "b.md").exists()
    journal = read_journal(txn_vault.transactions_dir / "apply-20260817-0001" / "journal.json")
    assert journal["state"] == "rolled-back"


def test_rollback_preserves_original_file_mode(txn_vault, tmp_path: Path, monkeypatch) -> None:
    plan, _ = make_fixture(txn_vault, tmp_path)
    root = txn_vault.root
    os.chmod(root / "wiki" / "a.md", 0o640)
    fail_on_nth_write(monkeypatch, 3)

    with pytest.raises(BoomError):
        apply_plan(txn_vault, plan, plan["approval_sha256"])

    assert os.stat(root / "wiki" / "a.md").st_mode & 0o777 == 0o640
