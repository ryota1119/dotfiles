"""bundle の読み込みと plan の組み立て."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath

from vaultctl.hashing import canonical_sha256, sha256_file
from vaultctl.vault import Vault

BUNDLE_SCHEMA = "vaultctl.bundle.v1"
PLAN_SCHEMA = "vaultctl.plan.v1"
VALID_MODES = ("create", "replace", "delete")


class PlanError(Exception):
    """bundle が不正、またはプレコンディションを満たさないことを表す."""


def load_bundle(path: Path) -> dict:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise PlanError(f"bundle を読めません: {path}") from exc
    try:
        bundle = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PlanError(f"bundle が JSON として不正です: {path}") from exc
    if not isinstance(bundle, dict):
        raise PlanError(f"bundle は JSON オブジェクトでなければなりません: {path}")
    if bundle.get("schema") != BUNDLE_SCHEMA:
        raise PlanError(
            f"bundle の schema が {BUNDLE_SCHEMA} ではありません: "
            f"{bundle.get('schema')!r}"
        )
    for key in ("operation_id", "operation_type"):
        value = bundle.get(key)
        if not isinstance(value, str) or not value:
            raise PlanError(f"bundle の {key} が空です")
    writes = bundle.get("writes")
    if not isinstance(writes, list) or not writes:
        raise PlanError("bundle の writes が空です")
    return bundle


def _check_relpath(value: object) -> str:
    if not isinstance(value, str) or not value:
        raise PlanError(f"path が文字列ではありません: {value!r}")
    if "\\" in value:
        raise PlanError(f"path に円記号を含められません: {value}")
    pure = PurePosixPath(value)
    if pure.is_absolute():
        raise PlanError(f"path は vault 相対でなければなりません: {value}")
    if any(part in ("..", "") for part in pure.parts):
        raise PlanError(f"path に .. を含められません: {value}")
    return value


def _check_content_file(value: object, relpath: str, mode: str) -> str:
    if not isinstance(value, str) or not value:
        raise PlanError(f"mode={mode} には content_file が必要です: {relpath}")
    source = Path(value)
    if not source.is_absolute():
        raise PlanError(f"content_file は絶対パスでなければなりません: {value}")
    if not source.is_file():
        raise PlanError(f"content_file が存在しません: {value}")
    return value


def build_plan(vault: Vault, bundle: dict) -> dict:
    entries = bundle.get("writes")
    if not isinstance(entries, list) or not entries:
        raise PlanError("bundle の writes が空です")

    writes: list[dict] = []
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise PlanError(f"writes の要素がオブジェクトではありません: {entry!r}")
        relpath = _check_relpath(entry.get("path"))
        if relpath in seen:
            raise PlanError(f"path が重複しています: {relpath}")
        seen.add(relpath)

        mode = entry.get("mode")
        if mode not in VALID_MODES:
            raise PlanError(f"mode が不正です: {mode!r}（{relpath}）")

        target = vault.root / relpath
        exists = target.is_file()
        if mode == "create":
            if target.exists() or target.is_symlink():
                raise PlanError(f"mode=create の対象が既に存在します: {relpath}")
            original_sha256 = None
        else:
            if not exists:
                raise PlanError(f"mode={mode} の対象が存在しません: {relpath}")
            original_sha256 = sha256_file(target)

        if mode == "delete":
            content_file = None
            new_sha256 = None
        else:
            content_file = _check_content_file(
                entry.get("content_file"), relpath, mode
            )
            new_sha256 = sha256_file(Path(content_file))

        writes.append(
            {
                "path": relpath,
                "mode": mode,
                "original_sha256": original_sha256,
                "new_sha256": new_sha256,
                "content_file": content_file,
            }
        )

    plan = {
        "schema": PLAN_SCHEMA,
        "vault_id": vault.vault_id,
        "operation_id": bundle["operation_id"],
        "operation_type": bundle["operation_type"],
        "input_bundle_sha256": canonical_sha256(bundle),
        "writes": writes,
    }
    plan["approval_sha256"] = plan_approval_sha256(plan)
    return plan


def plan_approval_sha256(plan: dict) -> str:
    return canonical_sha256(
        {key: value for key, value in plan.items() if key != "approval_sha256"}
    )
