"""vaultctl のテスト共通 fixture."""

from __future__ import annotations

from pathlib import Path

import pytest

from vaultctl.frontmatter import render_page
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
    # 実 vault の index.md は type: meta の frontmatter を持つ（T7 の追加決定事項1）。
    # frontmatter が無いと iter_pages() が FrontmatterError で落ちるため、実物に合わせる。
    (root / "wiki" / "index.md").write_text(
        "---\n"
        "type: meta\n"
        "title: index\n"
        "status: evergreen\n"
        "created: 2026-08-01\n"
        "updated: 2026-08-01\n"
        "tags:\n"
        "  - meta\n"
        "---\n"
        "\n"
        "# index\n",
        encoding="utf-8",
    )
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


# --- T7 追記: ページ生成ヘルパ（T8・T9 も使う） ---

DEFAULT_FRONTMATTER = {
    "type": "concept",
    "title": "テストページ",
    "status": "developing",
    "created": "2026-08-01",
    "updated": "2026-08-02",
    "tags": ["concept"],
}


def make_page(root, relpath, body="# 見出し\n\n本文です。\n", **fm):
    """合成 vault にページを1枚作り、作ったファイルの Path を返す。

    fm でデフォルトの frontmatter を上書きできる。値に None を渡すと
    そのキーを削除する（必須キー欠落のテスト用）。
    """
    data = dict(DEFAULT_FRONTMATTER)
    data.update(fm)
    data = {k: v for k, v in data.items() if v is not None}
    path = Path(root) / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_page(data, body), encoding="utf-8")
    return path
