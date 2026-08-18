"""vault の解決と state ディレクトリの採番."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path


class VaultError(Exception):
    """vault の解決に失敗したことを表す."""


@dataclass(frozen=True)
class Vault:
    root: Path
    vault_id: str
    state_dir: Path

    @property
    def wiki(self) -> Path:
        return self.root / "wiki"

    @property
    def inbox(self) -> Path:
        return self.root / "inbox"

    @property
    def raw(self) -> Path:
        return self.root / ".raw"

    @property
    def lock_path(self) -> Path:
        return self.state_dir / "lock"

    @property
    def transactions_dir(self) -> Path:
        return self.state_dir / "transactions"


def compute_vault_id(root: Path) -> str:
    digest = hashlib.sha256(str(root).encode("utf-8")).hexdigest()
    return f"{root.name}-{digest[:12]}"


def state_home() -> Path:
    value = os.environ.get("XDG_STATE_HOME")
    if value:
        return Path(value)
    return Path.home() / ".local" / "state"


def _is_vault_root(path: Path) -> bool:
    return (path / "wiki").is_dir() and (path / "inbox").is_dir()


def _search_upward(start: Path) -> Path | None:
    start = Path(os.path.realpath(start))
    for candidate in (start, *start.parents):
        if _is_vault_root(candidate):
            return candidate
    return None


def _validated(path_value: str, source: str) -> Path:
    path = Path(path_value).expanduser()
    if not _is_vault_root(path):
        raise VaultError(
            f"{source} で指定されたディレクトリは vault ではありません"
            f"（wiki/ と inbox/ が必要）: {path}"
        )
    return path


def resolve_vault(explicit: str | None = None, *, cwd: Path | None = None) -> Vault:
    if explicit is not None:
        root = _validated(explicit, "--vault")
    else:
        env_value = os.environ.get("VAULTCTL_VAULT")
        if env_value:
            root = _validated(env_value, "VAULTCTL_VAULT")
        else:
            start = Path(cwd) if cwd is not None else Path.cwd()
            found = _search_upward(start)
            if found is None:
                raise VaultError(f"{start} から上方に vault が見つかりません")
            root = found

    real_root = Path(os.path.realpath(root))
    vault_id = compute_vault_id(real_root)
    vault = Vault(
        root=real_root,
        vault_id=vault_id,
        state_dir=state_home() / "vaultctl" / vault_id,
    )
    vault.transactions_dir.mkdir(parents=True, exist_ok=True)
    return vault
