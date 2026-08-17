import os
from pathlib import Path

import pytest

from vaultctl.vault import (
    VaultError,
    compute_vault_id,
    resolve_vault,
    state_home,
)


def test_resolve_vault_explicit(synthetic_vault_root, state_home_dir):
    vault = resolve_vault(str(synthetic_vault_root))
    assert vault.root == Path(os.path.realpath(synthetic_vault_root))
    assert vault.wiki == vault.root / "wiki"
    assert vault.inbox == vault.root / "inbox"
    assert vault.raw == vault.root / ".raw"


def test_resolve_vault_uses_env_when_no_explicit(
    synthetic_vault_root, state_home_dir, monkeypatch
):
    monkeypatch.setenv("VAULTCTL_VAULT", str(synthetic_vault_root))
    vault = resolve_vault(None, cwd=state_home_dir)
    assert vault.root == Path(os.path.realpath(synthetic_vault_root))


def test_resolve_vault_explicit_beats_env(
    synthetic_vault_root, state_home_dir, tmp_path, monkeypatch
):
    other = tmp_path / "other-vault"
    (other / "wiki").mkdir(parents=True)
    (other / "inbox").mkdir()
    monkeypatch.setenv("VAULTCTL_VAULT", str(other))
    vault = resolve_vault(str(synthetic_vault_root))
    assert vault.root == Path(os.path.realpath(synthetic_vault_root))


def test_resolve_vault_searches_upward_from_cwd(synthetic_vault_root, state_home_dir):
    nested = synthetic_vault_root / "wiki" / "concepts"
    vault = resolve_vault(None, cwd=nested)
    assert vault.root == Path(os.path.realpath(synthetic_vault_root))


def test_resolve_vault_rejects_non_vault_directory(tmp_path, state_home_dir):
    plain = tmp_path / "plain"
    (plain / "wiki").mkdir(parents=True)  # inbox が無いので vault ではない
    with pytest.raises(VaultError):
        resolve_vault(str(plain))
    with pytest.raises(VaultError):
        resolve_vault(None, cwd=plain)


def test_resolve_vault_resolves_symlink(tmp_path, synthetic_vault_root, state_home_dir):
    link = tmp_path / "vault-link"
    link.symlink_to(synthetic_vault_root)
    vault = resolve_vault(str(link))
    assert vault.root == Path(os.path.realpath(synthetic_vault_root))


def test_vault_id_is_stable_for_same_root(synthetic_vault_root, state_home_dir):
    first = resolve_vault(str(synthetic_vault_root))
    second = resolve_vault(None, cwd=synthetic_vault_root / "inbox")
    assert first.vault_id == second.vault_id
    assert first.vault_id == compute_vault_id(
        Path(os.path.realpath(synthetic_vault_root))
    )
    assert first.vault_id.startswith("exocortex-")
    assert len(first.vault_id) == len("exocortex-") + 12


def test_state_dir_follows_xdg_state_home(synthetic_vault_root, state_home_dir):
    vault = resolve_vault(str(synthetic_vault_root))
    assert state_home() == state_home_dir
    assert vault.state_dir == state_home_dir / "vaultctl" / vault.vault_id
    assert vault.transactions_dir == vault.state_dir / "transactions"
    assert vault.transactions_dir.is_dir()
    assert vault.lock_path == vault.state_dir / "lock"
    assert not vault.lock_path.exists()
    # vault 側には何も作らない
    assert sorted(p.name for p in synthetic_vault_root.iterdir()) == [
        ".raw",
        "inbox",
        "wiki",
    ]


def test_state_home_defaults_to_local_state(monkeypatch):
    monkeypatch.delenv("XDG_STATE_HOME", raising=False)
    assert state_home() == Path.home() / ".local" / "state"
