"""vaultctl のテスト共通 fixture."""

from __future__ import annotations

from pathlib import Path

import pytest


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
    from vaultctl.vault import resolve_vault

    return resolve_vault(str(synthetic_vault_root))
