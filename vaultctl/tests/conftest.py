"""vaultctl のテスト共通 fixture."""

from __future__ import annotations

from pathlib import Path

import pytest

from vaultctl.vault import resolve_vault


@pytest.fixture
def synthetic_vault_root(tmp_path: Path) -> Path:
    """tmp_path 上に合成 vault を作る。実 vault は一切触らない。"""
    root = tmp_path / "exocortex"
    (root / "wiki" / "concepts").mkdir(parents=True)
    (root / "wiki" / "sources").mkdir()
    (root / "wiki" / "entities").mkdir()
    (root / "wiki" / "meta" / "ledgers").mkdir(parents=True)
    (root / "inbox").mkdir()
    (root / ".raw").mkdir()
    (root / "wiki" / "index.md").write_text("# index\n", encoding="utf-8")
    return root


@pytest.fixture
def state_home_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """XDG_STATE_HOME を tmp に閉じ込め、環境変数の漏れを断つ。"""
    home = tmp_path / "state"
    home.mkdir()
    monkeypatch.setenv("XDG_STATE_HOME", str(home))
    monkeypatch.delenv("VAULTCTL_VAULT", raising=False)
    return home


@pytest.fixture
def vault(synthetic_vault_root: Path, state_home_dir: Path):
    return resolve_vault(str(synthetic_vault_root))


@pytest.fixture
def txn_vault(tmp_path, monkeypatch):
    """T4〜T6 共通: wiki/ と inbox/ を持つ合成 vault。state は tmp 配下に閉じ込める。"""
    root = tmp_path / "vault"
    (root / "wiki").mkdir(parents=True)
    (root / "inbox").mkdir()
    state_home = tmp_path / "state"
    state_home.mkdir()
    monkeypatch.setenv("XDG_STATE_HOME", str(state_home))
    monkeypatch.delenv("VAULTCTL_VAULT", raising=False)
    return resolve_vault(str(root))
