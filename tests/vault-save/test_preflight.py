"""T13-1 / T13-2 の受け入れテスト。

合成 vault（scripts/make-save-fixture.sh）と preflight.py を、実 vault に一切
触れずに検証する。preflight.py はパス指定でロードし、skill の展開先に依存しない。
"""

from __future__ import annotations

import builtins
import importlib.util
import json
import os
import shutil
import sys
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SCRIPT = ROOT / "scripts" / "make-save-fixture.sh"
# chezmoi は `executable_` 接頭辞が無いと実行ビットを展開先に保存しない。
# 接頭辞を外した名前（preflight.py）が ~/.claude/ 側の実際のファイル名になる。
PREFLIGHT = ROOT / "dot_claude/skills/vault-save/scripts/executable_preflight.py"

# make-save-fixture.sh 冒頭の expected コメントと同じ値をここにも持つ。
# 片方だけ直すとずれるので、両方を必ず一致させること。
EXPECTED_VIOLATIONS = 0
EXPECTED_REVIEWS = 1


def _load_preflight():
    spec = importlib.util.spec_from_file_location("preflight", PREFLIGHT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    # @dataclass は cls.__module__ を sys.modules から引くため、exec_module の前に
    # 登録しておかないと AttributeError になる。
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def preflight():
    return _load_preflight()


def _vaultctl() -> list[str]:
    installed = Path.home() / ".local/bin/vaultctl"
    if installed.is_file() and os.access(installed, os.X_OK):
        return [str(installed)]
    uv = shutil.which("uv")
    if uv:
        return [uv, "run", "--project", str(ROOT / "vaultctl"), "vaultctl"]
    pytest.fail("vaultctl が見つかりません（~/.local/bin/vaultctl も uv も使えません）")


def _make_vault(tmp_path: Path) -> Path:
    vault = tmp_path / "vault"
    subprocess.run(["bash", str(FIXTURE_SCRIPT), str(vault)], check=True, capture_output=True)
    return vault


def _lint(vault: Path) -> dict:
    result = subprocess.run(
        [*_vaultctl(), "--vault", str(vault), "lint", "--json", "--today", "2026-08-19"],
        text=True, capture_output=True, check=False,
    )
    assert result.returncode in (0, 1, 2), result.stderr
    return json.loads(result.stdout)


def _plan(vault: Path, bundle: Path, out: Path) -> dict:
    result = subprocess.run(
        [*_vaultctl(), "--vault", str(vault), "plan", "--bundle", str(bundle), "--out", str(out)],
        text=True, capture_output=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(out.read_text(encoding="utf-8"))


# --- T13-1: 合成 vault -------------------------------------------------------


def test_fixture_is_clean(tmp_path: Path) -> None:
    """vault-save の fixture は「きれいな初期状態」でなければならない。

    vault-review の fixture と目的が正反対で、あちらは finding を意図的に含む。
    """
    vault = _make_vault(tmp_path)
    assert (vault / "wiki").is_dir() and (vault / "inbox").is_dir()
    assert not (vault).is_symlink()
    payload = _lint(vault)
    assert payload["counts"]["violation"] == EXPECTED_VIOLATIONS
    assert payload["counts"]["review"] == EXPECTED_REVIEWS


def test_fixture_rejects_existing_destination(tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    again = subprocess.run(
        ["bash", str(FIXTURE_SCRIPT), str(vault)], text=True, capture_output=True, check=False
    )
    assert again.returncode != 0
    assert "already exists" in again.stderr


def test_fixture_requires_absolute_path(tmp_path: Path) -> None:
    result = subprocess.run(
        ["bash", str(FIXTURE_SCRIPT), "relative/dest"], text=True, capture_output=True, check=False
    )
    assert result.returncode == 64


# --- bundle の組み立てヘルパ -------------------------------------------------


def _write(path: Path, text: str) -> str:
    path.write_text(text, encoding="utf-8")
    return str(path.resolve())


NEW_PAGE = """---
type: concept
title: Fixture new topic
status: developing
created: 2026-08-19
updated: 2026-08-19
tags: []
related:
  - "[[fixture-related]]"
---

# Fixture new topic

新規ページ。[[fixture-related]] を踏まえた内容。

## 内容

本文。

## 根拠と留保

合成データであり裏取りは無い。
"""


def _create_bundle(vault: Path, work: Path, *, page: str = NEW_PAGE,
                   page_path: str = "wiki/concepts/fixture-new-topic.md",
                   operation_id: str = "save-20260819T090000-fixture-new-topic") -> Path:
    staging = work / "staging"
    staging.mkdir(parents=True, exist_ok=True)
    writes = [
        {"path": page_path, "mode": "create",
         "content_file": _write(staging / "new.md", page)},
        {"path": "wiki/index.md", "mode": "replace",
         "content_file": _write(staging / "index.md",
                                (vault / "wiki/index.md").read_text(encoding="utf-8").replace(
                                    "- [[fixture-target]] — 追記・書き換え対象\n",
                                    "- [[fixture-target]] — 追記・書き換え対象\n"
                                    "- [[fixture-new-topic]] — Fixture new topic\n"))},
        {"path": "wiki/concepts/fixture-plain.md", "mode": "replace",
         "content_file": _write(staging / "plain.md",
                                (vault / "wiki/concepts/fixture-plain.md").read_text(encoding="utf-8").replace(
                                    "tags: []\n", 'tags: []\nrelated:\n  - "[[fixture-new-topic]]"\n', 1))},
        {"path": "wiki/log.md", "mode": "replace",
         "content_file": _write(staging / "log.md",
                                (vault / "wiki/log.md").read_text(encoding="utf-8").replace(
                                    "# Wiki Log\n\n",
                                    "# Wiki Log\n\n- 2026-08-19 — save — fixture-new-topic を作成した。\n", 1))},
        {"path": "wiki/hot.md", "mode": "replace",
         "content_file": _write(staging / "hot.md",
                                (vault / "wiki/hot.md").read_text(encoding="utf-8").replace(
                                    "## Last Updated\n\n",
                                    "## Last Updated\n\n- 2026-08-19: [[fixture-new-topic]]\n", 1))},
    ]
    bundle = work / "bundle.json"
    bundle.write_text(json.dumps(
        {"schema": "vaultctl.bundle.v1", "operation_id": operation_id,
         "operation_type": "save", "writes": writes}, ensure_ascii=False, indent=2), encoding="utf-8")
    return bundle


# 新規作成プロファイルの replace 4件に対応する検証モードの宣言。
CREATE_INTENT = {
    "wiki/index.md": {
        "mode": "insert-only",
        "line": "- [[fixture-new-topic]] — Fixture new topic",
        "section": "## Concepts",
    },
    "wiki/concepts/fixture-plain.md": {
        "mode": "frontmatter-only",
        "related_add": "[[fixture-new-topic]]",
    },
    "wiki/log.md": {
        "mode": "insert-only",
        "line": "- 2026-08-19 — save — fixture-new-topic を作成した。",
        "section": "# Wiki Log",
    },
    "wiki/hot.md": {
        "mode": "insert-only",
        "line": "- 2026-08-19: [[fixture-new-topic]]",
        "section": "## Last Updated",
    },
}


def _run(preflight, vault: Path, plan_path: Path, bundle: Path | None = None,
         intent: dict | None = CREATE_INTENT) -> tuple[int, list]:
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    bundle_data = json.loads(bundle.read_text(encoding="utf-8")) if bundle else None
    checks = preflight.validate(vault, plan, bundle_data, intent)
    return (0 if all(c.ok for c in checks) else 1), checks


def _failed(checks) -> list[str]:
    return [c.name for c in checks if not c.ok]


# --- T13-2: preflight --------------------------------------------------------


def test_happy_path_passes_every_check(preflight, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    bundle = _create_bundle(vault, work)
    plan_path = work / "plan.json"
    _plan(vault, bundle, plan_path)
    code, checks = _run(preflight, vault, plan_path, bundle)
    assert code == 0, _failed(checks)
    assert any(c.name == "schema照合" and c.ok for c in checks)


def test_schema_constants_match_vaultctl(preflight) -> None:
    """写経した schema 定数が vaultctl 本体とずれていないこと。

    ずれたまま [OK] を出すのが最悪なので、これ自体をテストで固定する。
    """
    check = preflight._schema_drift_check()
    assert check.ok, check.detail


def test_delete_is_rejected(preflight, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    bundle = _create_bundle(vault, work)
    data = json.loads(bundle.read_text(encoding="utf-8"))
    data["writes"].append({"path": "wiki/concepts/fixture-target.md", "mode": "delete"})
    plan_path = work / "plan-delete.json"
    plan_path.write_text(json.dumps(data), encoding="utf-8")
    code, checks = _run(preflight, vault, plan_path)
    assert code == 1
    assert "delete禁止" in _failed(checks)


def test_relative_content_file_is_rejected(preflight, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    bundle = _create_bundle(vault, work)
    data = json.loads(bundle.read_text(encoding="utf-8"))
    data["writes"][0]["content_file"] = "staging/new.md"
    plan_path = work / "plan-rel.json"
    plan_path.write_text(json.dumps(data), encoding="utf-8")
    code, checks = _run(preflight, vault, plan_path)
    assert code == 1
    assert "content_file" in _failed(checks)


@pytest.mark.parametrize("operation_id", [
    "save-2026-08-19-slug",          # 時刻の書式が違う
    "ingest-20260819T090000-slug",   # op が save でない
    "save-20260819T090000-Slug_A",   # slug に大文字とアンダースコア
    "save-20260899T090000-slug",     # 実在しない日付
])
def test_bad_operation_id_is_rejected(preflight, tmp_path: Path, operation_id: str) -> None:
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    bundle = _create_bundle(vault, work, operation_id=operation_id)
    data = json.loads(bundle.read_text(encoding="utf-8"))
    plan_path = work / "plan-opid.json"
    plan_path.write_text(json.dumps(data), encoding="utf-8")
    code, checks = _run(preflight, vault, plan_path)
    assert code == 1
    assert "operation_id" in _failed(checks)


def test_wrong_location_is_rejected(preflight, tmp_path: Path) -> None:
    """type=concept を wiki/entities/ に置く（規則3の先回り）。"""
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    bundle = _create_bundle(vault, work, page_path="wiki/entities/fixture-new-topic.md")
    data = json.loads(bundle.read_text(encoding="utf-8"))
    plan_path = work / "plan-loc.json"
    plan_path.write_text(json.dumps(data), encoding="utf-8")
    code, checks = _run(preflight, vault, plan_path)
    assert code == 1
    assert "create配置" in _failed(checks)


def test_unresolved_wikilink_is_rejected(preflight, tmp_path: Path) -> None:
    """規則4の先回り。存在しない slug を本文に書く。"""
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    page = NEW_PAGE.replace("[[fixture-related]] を踏まえた内容。",
                            "[[fixture-does-not-exist]] を踏まえた内容。")
    bundle = _create_bundle(vault, work, page=page)
    data = json.loads(bundle.read_text(encoding="utf-8"))
    plan_path = work / "plan-link.json"
    plan_path.write_text(json.dumps(data), encoding="utf-8")
    code, checks = _run(preflight, vault, plan_path)
    assert code == 1
    assert "wikilink" in _failed(checks)


def test_empty_section_is_rejected(preflight, tmp_path: Path) -> None:
    """規則6の先回り。見出しだけの節を作る。"""
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    page = NEW_PAGE.replace("## 内容\n\n本文。\n", "## 内容\n\n")
    bundle = _create_bundle(vault, work, page=page)
    data = json.loads(bundle.read_text(encoding="utf-8"))
    plan_path = work / "plan-empty.json"
    plan_path.write_text(json.dumps(data), encoding="utf-8")
    code, checks = _run(preflight, vault, plan_path)
    assert code == 1
    assert "空セクション" in _failed(checks)


def test_forbidden_extra_key_is_rejected(preflight, tmp_path: Path) -> None:
    """concept に claim_ids は置けない（EXTRA_KEYS の範囲外）。"""
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    page = NEW_PAGE.replace("tags: []\n", "tags: []\nclaim_ids:\n  - clm-x\n", 1)
    bundle = _create_bundle(vault, work, page=page)
    data = json.loads(bundle.read_text(encoding="utf-8"))
    plan_path = work / "plan-extra.json"
    plan_path.write_text(json.dumps(data), encoding="utf-8")
    code, checks = _run(preflight, vault, plan_path)
    assert code == 1
    assert "拡張キー" in _failed(checks)


def test_missing_backlink_is_rejected(preflight, tmp_path: Path) -> None:
    """D-S1: 被リンク元の replace が無い bundle はプロファイル検査で落ちる。"""
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    bundle = _create_bundle(vault, work)
    data = json.loads(bundle.read_text(encoding="utf-8"))
    data["writes"] = [w for w in data["writes"] if w["path"] != "wiki/concepts/fixture-plain.md"]
    plan_path = work / "plan-nobl.json"
    plan_path.write_text(json.dumps(data), encoding="utf-8")
    code, checks = _run(preflight, vault, plan_path)
    assert code == 1
    assert "プロファイル" in _failed(checks)


def test_append_profile_passes(preflight, tmp_path: Path) -> None:
    """追記・書き換えプロファイル（create なし・replace 3件）。"""
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    staging = work / "staging"
    staging.mkdir(parents=True)
    target = (vault / "wiki/concepts/fixture-target.md").read_text(encoding="utf-8")
    writes = [
        {"path": "wiki/concepts/fixture-target.md", "mode": "replace",
         "content_file": _write(staging / "target.md", target + "\n## 追記\n\n追記した本文。\n")},
        {"path": "wiki/log.md", "mode": "replace",
         "content_file": _write(staging / "log.md",
                                (vault / "wiki/log.md").read_text(encoding="utf-8").replace(
                                    "# Wiki Log\n\n", "# Wiki Log\n\n- 2026-08-19 — save — 追記した。\n", 1))},
        {"path": "wiki/hot.md", "mode": "replace",
         "content_file": _write(staging / "hot.md",
                                (vault / "wiki/hot.md").read_text(encoding="utf-8").replace(
                                    "## Last Updated\n\n", "## Last Updated\n\n- 2026-08-19: 追記\n", 1))},
    ]
    plan_path = work / "plan-append.json"
    plan_path.write_text(json.dumps(
        {"schema": "vaultctl.bundle.v1", "operation_id": "save-20260819T091000-append",
         "operation_type": "save", "writes": writes}, ensure_ascii=False), encoding="utf-8")
    intent = {
        "wiki/concepts/fixture-target.md": {
            "mode": "insert-only",
            "line": "## 追記\n\n追記した本文。\n",
            "section": "## Existing constraints",
        },
        "wiki/log.md": {"mode": "insert-only",
                        "line": "- 2026-08-19 — save — 追記した。", "section": "# Wiki Log"},
        "wiki/hot.md": {"mode": "insert-only",
                        "line": "- 2026-08-19: 追記", "section": "## Last Updated"},
    }
    code, checks = _run(preflight, vault, plan_path, intent=intent)
    assert code == 0, _failed(checks)
    assert any(c.name == "プロファイル" and "追記" in c.detail for c in checks)


def test_append_profile_rejects_index_write(preflight, tmp_path: Path) -> None:
    """追記プロファイルで index.md を触ると落ちる（既に掲載済みのため）。"""
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    staging = work / "staging"
    staging.mkdir(parents=True)
    writes = [
        {"path": "wiki/concepts/fixture-target.md", "mode": "replace",
         "content_file": _write(staging / "t.md", "x\n")},
        {"path": "wiki/index.md", "mode": "replace",
         "content_file": _write(staging / "i.md", "x\n")},
        {"path": "wiki/log.md", "mode": "replace", "content_file": _write(staging / "l.md", "x\n")},
        {"path": "wiki/hot.md", "mode": "replace", "content_file": _write(staging / "h.md", "x\n")},
    ]
    plan_path = work / "plan-append-idx.json"
    plan_path.write_text(json.dumps(
        {"schema": "vaultctl.bundle.v1", "operation_id": "save-20260819T091500-append",
         "operation_type": "save", "writes": writes}, ensure_ascii=False), encoding="utf-8")
    code, checks = _run(preflight, vault, plan_path)
    assert code == 1
    assert "プロファイル" in _failed(checks)


def test_never_touches_the_real_vault(preflight, tmp_path: Path, monkeypatch) -> None:
    """preflight が ~/Workspace/exocortex を開かないことを担保する。"""
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    bundle = _create_bundle(vault, work)
    plan_path = work / "plan.json"
    _plan(vault, bundle, plan_path)

    real_open = builtins.open
    real_path_open = Path.open

    def guard(path, *a, **kw):
        if "Workspace/exocortex" in os.fspath(path):
            raise AssertionError(f"実 vault を開こうとした: {path}")
        return real_open(path, *a, **kw)

    def guard_path(self, *a, **kw):
        if "Workspace/exocortex" in os.fspath(self):
            raise AssertionError(f"実 vault を開こうとした: {self}")
        return real_path_open(self, *a, **kw)

    monkeypatch.setattr(builtins, "open", guard)
    monkeypatch.setattr(Path, "open", guard_path)
    code, checks = _run(preflight, vault, plan_path, bundle)
    assert code == 0, _failed(checks)


# --- T13-3 / T13-3b: replace の検証モード -----------------------------------


def _replace_case(preflight, vault: Path, tmp_path: Path, relpath: str,
                  new_text: str, spec: dict) -> list[str]:
    """1件だけの replace を組み、その replace 検証の失敗理由を返す。"""
    staging = tmp_path / "rp"
    staging.mkdir(exist_ok=True)
    target = staging / Path(relpath).name
    target.write_text(new_text, encoding="utf-8")
    writes = [{"path": relpath, "mode": "replace", "content_file": str(target.resolve())}]
    checks = preflight._replace_checks(vault, writes, {relpath: spec})
    return [c.detail for c in checks if not c.ok]


def test_frontmatter_only_rejects_body_change(preflight, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    rel = "wiki/concepts/fixture-plain.md"
    text = (vault / rel).read_text(encoding="utf-8")
    text = text.replace("tags: []\n", 'tags: []\nrelated:\n  - "[[fixture-target]]"\n', 1)
    text = text.replace("This page has no related key", "This page HAS no related key", 1)
    errors = _replace_case(preflight, vault, tmp_path, rel, text,
                           {"mode": "frontmatter-only", "related_add": "[[fixture-target]]"})
    assert errors and "本文が変わっています" in errors[0]


def test_frontmatter_only_rejects_other_key_change(preflight, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    rel = "wiki/concepts/fixture-plain.md"
    text = (vault / rel).read_text(encoding="utf-8")
    text = text.replace("tags: []\n", 'tags: []\nrelated:\n  - "[[fixture-target]]"\n', 1)
    text = text.replace("title: Fixture plain", "title: Fixture plain (renamed)", 1)
    errors = _replace_case(preflight, vault, tmp_path, rel, text,
                           {"mode": "frontmatter-only", "related_add": "[[fixture-target]]"})
    assert errors and "変更キーが" in errors[0]


def test_frontmatter_only_rejects_related_reorder(preflight, tmp_path: Path) -> None:
    """既存の related を並べ替えると失敗する（取りこぼしの検出）。"""
    vault = _make_vault(tmp_path)
    rel = "wiki/concepts/fixture-related.md"
    text = (vault / rel).read_text(encoding="utf-8")
    text = text.replace('related:\n  - "[[fixture-plain]]"\n',
                        'related:\n  - "[[fixture-target]]"\n  - "[[fixture-plain]]"\n', 1)
    errors = _replace_case(preflight, vault, tmp_path, rel, text,
                           {"mode": "frontmatter-only", "related_add": "[[fixture-target]]"})
    assert errors and "並べ替え" in errors[0]


def test_insert_only_rejects_rewrite(preflight, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    rel = "wiki/index.md"
    text = (vault / rel).read_text(encoding="utf-8").replace(
        "- [[fixture-target]] — 追記・書き換え対象", "- [[fixture-target]] — 書き換えた説明", 1)
    errors = _replace_case(preflight, vault, tmp_path, rel, text,
                           {"mode": "insert-only", "line": "x", "section": "## Concepts"})
    assert errors and "挿入以外の変更" in errors[0]


def test_insert_only_rejects_two_insertions(preflight, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    rel = "wiki/index.md"
    text = (vault / rel).read_text(encoding="utf-8")
    text = text.replace("## Entities\n\n", "## Entities\n\n- [[fixture-plain]] — 誤挿入\n", 1)
    text = text.replace("- [[fixture-target]] — 追記・書き換え対象\n",
                        "- [[fixture-target]] — 追記・書き換え対象\n- [[fixture-related]] — 二つ目\n", 1)
    errors = _replace_case(preflight, vault, tmp_path, rel, text,
                           {"mode": "insert-only", "line": "x", "section": "## Concepts"})
    assert errors and "1箇所のみ" in errors[0]


def test_insert_only_rejects_wrong_line(preflight, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    rel = "wiki/log.md"
    text = (vault / rel).read_text(encoding="utf-8").replace(
        "# Wiki Log\n\n", "# Wiki Log\n\n- 2026-08-19 — save — 想定と1文字違う行。\n", 1)
    errors = _replace_case(preflight, vault, tmp_path, rel, text,
                           {"mode": "insert-only",
                            "line": "- 2026-08-19 — save — 想定と1文字違う行", "section": "# Wiki Log"})
    assert errors and "挿入行が意図と違います" in errors[0]


def test_insert_only_rejects_wrong_section(preflight, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    rel = "wiki/index.md"
    line = "- [[fixture-target]] — 節を間違えた挿入"
    text = (vault / rel).read_text(encoding="utf-8").replace(
        "## Entities\n\nNo entity pages.\n", f"## Entities\n\nNo entity pages.\n{line}\n", 1)
    errors = _replace_case(preflight, vault, tmp_path, rel, text,
                           {"mode": "insert-only", "line": line, "section": "## Concepts"})
    assert errors and "意図した節の外" in errors[0]


def test_body_edit_accepts_declared_rewrite(preflight, tmp_path: Path) -> None:
    """D-S28 でやった「旧テキストを新テキストへ置換」を宣言どおりに通す。"""
    vault = _make_vault(tmp_path)
    rel = "wiki/concepts/fixture-target.md"
    old_text = "The body has multiple populated sections for body-edit fixtures."
    new_text = "本文の記述を宣言どおりに書き換えた。"
    text = (vault / rel).read_text(encoding="utf-8").replace(old_text, new_text, 1)
    errors = _replace_case(preflight, vault, tmp_path, rel, text,
                           {"mode": "body-edit", "edits": [[old_text, new_text]]})
    assert not errors, errors


def test_body_edit_detects_undeclared_change(preflight, tmp_path: Path) -> None:
    """宣言していない変更が混ざったら止まる（暴走検出）。これが body-edit の要。"""
    vault = _make_vault(tmp_path)
    rel = "wiki/concepts/fixture-target.md"
    old_text = "The body has multiple populated sections for body-edit fixtures."
    new_text = "本文の記述を宣言どおりに書き換えた。"
    text = (vault / rel).read_text(encoding="utf-8").replace(old_text, new_text, 1)
    text = text.replace("Edits must preserve every undeclared block.", "こっそり書き換えた。", 1)
    errors = _replace_case(preflight, vault, tmp_path, rel, text,
                           {"mode": "body-edit", "edits": [[old_text, new_text]]})
    assert errors and "宣言と一致しません" in errors[0]


def test_body_edit_accepts_declared_deletion(preflight, tmp_path: Path) -> None:
    """削除も宣言できる（新テキストが空）。D-S28 の行削除に相当する。"""
    vault = _make_vault(tmp_path)
    rel = "wiki/concepts/fixture-target.md"
    old_text = "Edits must preserve every undeclared block."
    text = (vault / rel).read_text(encoding="utf-8").replace(old_text + "\n", "", 1)
    errors = _replace_case(preflight, vault, tmp_path, rel, text,
                           {"mode": "body-edit", "edits": [[old_text, ""]]})
    assert not errors, errors


def test_body_edit_requires_declaration(preflight, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    rel = "wiki/concepts/fixture-target.md"
    text = (vault / rel).read_text(encoding="utf-8").replace("multiple", "several", 1)
    errors = _replace_case(preflight, vault, tmp_path, rel, text, {"mode": "body-edit"})
    assert errors and "edits" in errors[0]


def test_replace_without_intent_is_rejected(preflight, tmp_path: Path) -> None:
    """--intent が無いまま replace を通さない（検証の素通りを防ぐ）。"""
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    bundle = _create_bundle(vault, work)
    plan_path = work / "plan.json"
    _plan(vault, bundle, plan_path)
    code, checks = _run(preflight, vault, plan_path, bundle, intent=None)
    assert code == 1
    assert "replace検証" in _failed(checks)


def test_unknown_replace_mode_is_rejected(preflight, tmp_path: Path) -> None:
    vault = _make_vault(tmp_path)
    rel = "wiki/log.md"
    text = (vault / rel).read_text(encoding="utf-8")
    errors = _replace_case(preflight, vault, tmp_path, rel, text, {"mode": "なんでもあり"})
    assert errors and "mode が不正" in errors[0]


# --- T13-8: end-to-end の受け入れ -------------------------------------------


def test_promotion_queue_delta_depends_on_developing_count(tmp_path: Path) -> None:
    """規則9-a の個別 finding の増分は、適用前の developing 枚数で決まる。

    計画2.3-B は「新規ページは updated が当日なので古い順5件に入らない。よって
    review は増えない」としていたが、これは誤り。キューが PROMOTION_QUEUE_LIMIT(5)
    に満たなければ当日更新のページでもそのまま並ぶ。実 vault は developing が20枚超
    あるため増分0になるが、それは条件が満たされているからにすぎない。

    ここでは developing 0枚の合成 vault で「増分1」になることを固定する。
    """
    vault = _make_vault(tmp_path)
    before = _lint(vault)
    developing = [f for f in before["findings"]
                  if f["rule"] == "9-a" and f["path"]]
    assert developing == [], "合成 vault の初期状態は developing 0枚であること"

    page = tmp_path / "new.md"
    page.write_text(NEW_PAGE, encoding="utf-8")
    bundle = tmp_path / "b.json"
    work = tmp_path / "work"
    work.mkdir()
    created = _create_bundle(vault, work)
    plan_path = work / "plan.json"
    plan = _plan(vault, created, plan_path)
    subprocess.run(
        [*_vaultctl(), "--vault", str(vault), "apply", "--plan", str(plan_path),
         "--approved-plan-sha256", plan["approval_sha256"]],
        check=True, capture_output=True, text=True,
    )
    after = _lint(vault)
    assert after["counts"]["violation"] == before["counts"]["violation"], "violation は増えない"
    assert after["counts"]["review"] == before["counts"]["review"] + 1, (
        "developing が5件未満の vault では review が1件増える"
    )
    individual = [f for f in after["findings"] if f["rule"] == "9-a" and f["path"]]
    assert len(individual) == 1


def test_wrong_approval_hash_leaves_vault_untouched(tmp_path: Path) -> None:
    """承認ハッシュが違えば apply は失敗し、vault は1バイトも変わらない。"""
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    bundle = _create_bundle(vault, work)
    plan_path = work / "plan.json"
    plan = _plan(vault, bundle, plan_path)

    def manifest() -> list[tuple[str, int, bytes]]:
        return sorted(
            (str(p.relative_to(vault)), p.stat().st_size, p.read_bytes())
            for p in vault.rglob("*") if p.is_file()
        )

    before = manifest()
    good = plan["approval_sha256"]
    bad = good[:-1] + ("0" if good[-1] != "0" else "1")
    result = subprocess.run(
        [*_vaultctl(), "--vault", str(vault), "apply", "--plan", str(plan_path),
         "--approved-plan-sha256", bad],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "承認ハッシュが一致しない" in (result.stdout + result.stderr)
    assert manifest() == before, "apply が失敗したのに vault が変わっている"


def test_same_operation_id_cannot_be_reused(tmp_path: Path) -> None:
    """同じ operation_id は二度使えない。"""
    vault = _make_vault(tmp_path)
    work = tmp_path / "work"
    bundle = _create_bundle(vault, work)
    plan_path = work / "plan.json"
    plan = _plan(vault, bundle, plan_path)
    args = [*_vaultctl(), "--vault", str(vault), "apply", "--plan", str(plan_path),
            "--approved-plan-sha256", plan["approval_sha256"]]
    first = subprocess.run(args, capture_output=True, text=True, check=False)
    assert first.returncode == 0, first.stderr
    assert "state=complete" in first.stdout
    second = subprocess.run(args, capture_output=True, text=True, check=False)
    assert second.returncode != 0
    assert "既に存在する" in (second.stdout + second.stderr)
