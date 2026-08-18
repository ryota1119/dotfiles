import os
from pathlib import Path

import pytest

from vaultctl.atomic import atomic_write, backup_file, fsync_dir


def test_atomic_write_creates_file_with_given_mode(tmp_path: Path) -> None:
    target = tmp_path / "sub" / "new.md"

    atomic_write(target, "新規\n".encode("utf-8"), mode=0o600)

    assert target.read_bytes() == "新規\n".encode("utf-8")
    assert os.stat(target).st_mode & 0o777 == 0o600


def test_atomic_write_preserves_existing_file_mode(tmp_path: Path) -> None:
    target = tmp_path / "existing.md"
    target.write_bytes(b"old\n")
    os.chmod(target, 0o644)

    atomic_write(target, b"new\n", mode=0o600)

    assert target.read_bytes() == b"new\n"
    assert os.stat(target).st_mode & 0o777 == 0o644


def test_atomic_write_leaves_no_temporary_file(tmp_path: Path) -> None:
    target = tmp_path / "a.md"

    atomic_write(target, b"x\n")

    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.md"]


def test_backup_file_copies_content_and_mode(tmp_path: Path) -> None:
    src = tmp_path / "src.md"
    src.write_bytes("原本\n".encode("utf-8"))
    os.chmod(src, 0o640)
    dest = tmp_path / "backups" / "0001.original"

    backup_file(src, dest)

    assert dest.read_bytes() == "原本\n".encode("utf-8")
    assert os.stat(dest).st_mode & 0o777 == 0o640
    assert src.exists()


def test_fsync_dir_accepts_existing_directory(tmp_path: Path) -> None:
    fsync_dir(tmp_path)


def test_fsync_dir_rejects_missing_directory(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        fsync_dir(tmp_path / "missing")
