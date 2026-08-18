import json
import os
import stat
import subprocess
import sys

import pytest

from vaultctl.lock import LOCK_SCHEMA, LockHeld, acquire, boot_id, hold_lock, release


def write_lock(vault, *, pid, boot="", operation_id="other-op", raw=None):
    vault.lock_path.parent.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        vault.lock_path.write_text(raw, encoding="utf-8")
        return
    payload = {
        "schema": LOCK_SCHEMA,
        "hostname": "somehost",
        "pid": pid,
        "boot_id": boot if boot else boot_id(),
        "created_epoch": 0.0,
        "operation_id": operation_id,
    }
    vault.lock_path.write_text(json.dumps(payload), encoding="utf-8")


def test_boot_id_is_non_empty_string():
    value = boot_id()
    assert isinstance(value, str)
    assert value != ""


def test_acquire_creates_lock_file_with_expected_payload(vault):
    payload = acquire(vault, "ingest-20260817-a")

    assert vault.lock_path.is_file()
    on_disk = json.loads(vault.lock_path.read_text(encoding="utf-8"))
    assert on_disk == payload
    assert payload["schema"] == LOCK_SCHEMA
    assert payload["pid"] == os.getpid()
    assert payload["boot_id"] == boot_id()
    assert payload["operation_id"] == "ingest-20260817-a"
    assert isinstance(payload["created_epoch"], float)
    assert isinstance(payload["hostname"], str) and payload["hostname"]
    mode = stat.S_IMODE(vault.lock_path.stat().st_mode)
    assert mode == 0o600


def test_acquire_raises_lock_held_when_self_holds_it(vault):
    acquire(vault, "ingest-20260817-a")
    with pytest.raises(LockHeld):
        acquire(vault, "ingest-20260817-b")


def test_acquire_does_not_steal_lock_of_live_process(vault):
    """設計書12節 検証項目4: 生きたプロセスのロックは奪わない."""
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        write_lock(vault, pid=proc.pid)
        with pytest.raises(LockHeld):
            acquire(vault, "ingest-20260817-b")
        # ロックの中身が書き換わっていないこと
        on_disk = json.loads(vault.lock_path.read_text(encoding="utf-8"))
        assert on_disk["pid"] == proc.pid
        assert on_disk["operation_id"] == "other-op"
    finally:
        proc.kill()
        proc.wait(timeout=10)


def test_acquire_steals_lock_of_dead_process(vault):
    """設計書12節 検証項目3: 死んだPIDのロックは奪う."""
    proc = subprocess.Popen([sys.executable, "-c", "pass"])
    proc.wait(timeout=10)
    dead_pid = proc.pid
    with pytest.raises(ProcessLookupError):
        os.kill(dead_pid, 0)

    write_lock(vault, pid=dead_pid)
    payload = acquire(vault, "ingest-20260817-b")

    assert payload["pid"] == os.getpid()
    on_disk = json.loads(vault.lock_path.read_text(encoding="utf-8"))
    assert on_disk["operation_id"] == "ingest-20260817-b"


def test_acquire_steals_broken_json_lock(vault):
    write_lock(vault, pid=0, raw="{壊れた JSON")
    payload = acquire(vault, "ingest-20260817-b")
    assert payload["pid"] == os.getpid()
    on_disk = json.loads(vault.lock_path.read_text(encoding="utf-8"))
    assert on_disk["operation_id"] == "ingest-20260817-b"


def test_acquire_steals_lock_with_different_boot_id(vault):
    """再起動後の PID 再利用対策: boot_id 不一致なら生きた PID でも奪う."""
    proc = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
    try:
        write_lock(vault, pid=proc.pid, boot="boot-id-from-previous-boot")
        payload = acquire(vault, "ingest-20260817-b")
        assert payload["pid"] == os.getpid()
        assert payload["boot_id"] == boot_id()
    finally:
        proc.kill()
        proc.wait(timeout=10)


def test_release_removes_own_lock(vault):
    payload = acquire(vault, "ingest-20260817-a")
    release(vault, payload)
    assert not vault.lock_path.exists()


def test_release_keeps_lock_owned_by_another_pid(vault):
    payload = acquire(vault, "ingest-20260817-a")
    write_lock(vault, pid=os.getpid() + 1, operation_id="someone-else")
    release(vault, payload)
    assert vault.lock_path.is_file()
    on_disk = json.loads(vault.lock_path.read_text(encoding="utf-8"))
    assert on_disk["operation_id"] == "someone-else"


def test_release_is_noop_when_lock_missing(vault):
    payload = acquire(vault, "ingest-20260817-a")
    vault.lock_path.unlink()
    release(vault, payload)  # 例外を出さない
    assert not vault.lock_path.exists()


def test_hold_lock_releases_on_success(vault):
    with hold_lock(vault, "ingest-20260817-a") as payload:
        assert vault.lock_path.is_file()
        assert payload["operation_id"] == "ingest-20260817-a"
    assert not vault.lock_path.exists()


def test_hold_lock_releases_on_exception(vault):
    class Boom(Exception):
        pass

    with pytest.raises(Boom):
        with hold_lock(vault, "ingest-20260817-a"):
            assert vault.lock_path.is_file()
            raise Boom
    assert not vault.lock_path.exists()
