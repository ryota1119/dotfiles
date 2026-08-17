"""原子的な書き込みとバックアップ退避。

すべての vault 内ファイル更新はこのモジュールを経由する（設計書 4.3 手順6）。
tmp へ書く → fsync → os.rename → 親ディレクトリ fsync、の順を守る。
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

__all__ = ["fsync_dir", "atomic_write", "backup_file"]


def fsync_dir(path: Path) -> None:
    """ディレクトリエントリの更新をディスクに固定する。"""
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _fsync_file(path: Path) -> None:
    fd = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(target: Path, data: bytes, *, mode: int = 0o600) -> None:
    """`target` を原子的に `data` へ置き換える。

    `target` が既に存在する場合、その権限ビットを維持する（`mode` は新規作成時のみ使う）。
    """
    target = Path(target)
    parent = target.parent
    parent.mkdir(parents=True, exist_ok=True)

    effective_mode = mode
    try:
        effective_mode = os.stat(target).st_mode & 0o7777
    except FileNotFoundError:
        pass

    tmp = parent / f".{target.name}.vaultctl-tmp"
    fd = os.open(str(tmp), os.O_CREAT | os.O_WRONLY | os.O_TRUNC, effective_mode)
    try:
        os.write(fd, data)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.chmod(tmp, effective_mode)
    os.rename(tmp, target)
    fsync_dir(parent)


def backup_file(src: Path, dest: Path) -> None:
    """原本を `dest` へ退避する。内容・権限・mtime を保つ。"""
    src = Path(src)
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    _fsync_file(dest)
    fsync_dir(dest.parent)
