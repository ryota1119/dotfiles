"""ローカル state ディレクトリ上のロック."""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from vaultctl.vault import Vault

LOCK_SCHEMA = "vaultctl.lock.v1"


class LockHeld(Exception):
    """他プロセスがロックを保持していることを表す."""


def boot_id() -> str:
    if sys.platform == "darwin":
        try:
            result = subprocess.run(
                ["sysctl", "-n", "kern.boottime"],
                capture_output=True,
                text=True,
                check=True,
                timeout=5,
            )
        except (OSError, subprocess.SubprocessError):
            return "unknown"
        return result.stdout.strip() or "unknown"
    if sys.platform.startswith("linux"):
        try:
            value = Path("/proc/sys/kernel/random/boot_id").read_text(
                encoding="utf-8"
            )
        except OSError:
            return "unknown"
        return value.strip() or "unknown"
    return "unknown"


def _make_payload(operation_id: str) -> dict:
    return {
        "schema": LOCK_SCHEMA,
        "hostname": socket.gethostname(),
        "pid": os.getpid(),
        "boot_id": boot_id(),
        "created_epoch": time.time(),
        "operation_id": operation_id,
    }


def _read_lock(path: Path) -> dict | None:
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _is_stale(path: Path) -> bool:
    """既存ロックを奪ってよいか判定する（判定順序は設計書 4.2）."""
    payload = _read_lock(path)
    if payload is None:
        return True  # (1) JSON が壊れている
    if payload.get("boot_id") != boot_id():
        return True  # (2) 再起動をまたいでいる
    pid = payload.get("pid")
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return True
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return True  # (3) プロセスが死んでいる
    except PermissionError:
        return False  # 生きている（別ユーザー所有）
    return False  # (4) 生きている


def acquire(vault: Vault, operation_id: str) -> dict:
    path = vault.lock_path
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = _make_payload(operation_id)
    data = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")

    for _ in range(2):
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            if not _is_stale(path):
                raise LockHeld(f"ロックは他プロセスが保持しています: {path}")
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
            continue
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
        except BaseException:
            try:
                os.unlink(path)
            except FileNotFoundError:
                pass
            raise
        return payload

    raise LockHeld(f"ロックを取得できませんでした: {path}")


def release(vault: Vault, payload: dict) -> None:
    path = vault.lock_path
    current = _read_lock(path)
    if current is None:
        return
    if current.get("pid") != payload.get("pid"):
        return
    try:
        os.unlink(path)
    except FileNotFoundError:
        pass


@contextmanager
def hold_lock(vault: Vault, operation_id: str) -> Iterator[dict]:
    payload = acquire(vault, operation_id)
    try:
        yield payload
    finally:
        release(vault, payload)
