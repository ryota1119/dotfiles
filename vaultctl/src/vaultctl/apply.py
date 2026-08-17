"""plan の適用とロールバック（設計書 4.3）。"""

from __future__ import annotations

from pathlib import Path

from vaultctl.hashing import sha256_file
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


def apply_plan(vault: Vault, plan: dict, approved_sha256: str) -> dict:
    verify_approval(plan, approved_sha256)
    if plan.get("vault_id") not in (None, vault.vault_id):
        raise ApplyError(
            f"plan の vault_id が対象 vault と異なる: {plan.get('vault_id')} != {vault.vault_id}"
        )
    with hold_lock(vault, plan["operation_id"]):
        check_preconditions(vault, plan)
        raise ApplyError("書き込みは未実装")
