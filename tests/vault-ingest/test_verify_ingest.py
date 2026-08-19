"""T14-5〜T14-7 の受け入れテスト。ingest の Tx-2 のプリフライト検証。"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SCRIPT = ROOT / "scripts" / "make-ingest-fixture.sh"
VERIFY = ROOT / "dot_claude/skills/vault-ingest/scripts/executable_verify_ingest.py"
LEDGER = "wiki/meta/ledgers/source-ledger.json"
SLUG = "fresh-topic-2026-08"
PAGE = f"wiki/sources/{SLUG}.md"

PAGE_TEXT = """---
type: source
title: "取り込みテスト用のソース"
status: developing
created: 2026-08-19
updated: 2026-08-19
tags:
  - source
  - fixture
---

# 取り込みテスト用のソース

合成 vault で ingest モードを通すためのソースページ。

## 概要

[[reconcile-topic-2026-08]] と同じ経路で取り込まれた。

## 出典

- 原本: .raw/fresh-source.md （取得日: 2026-08-19）
"""


def _load():
    spec = importlib.util.spec_from_file_location("verify_ingest", VERIFY)
    module = importlib.util.module_from_spec(spec)
    sys.modules["verify_ingest"] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def vi():
    return _load()


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    dest = tmp_path / "vault"
    subprocess.run(["bash", str(FIXTURE_SCRIPT), str(dest)], check=True, capture_output=True)
    (dest / ".raw/fresh-source.md").write_bytes((dest / "inbox/fresh-source.md").read_bytes())
    return dest


def _plan(vault: Path, work: Path, *, page: str = PAGE_TEXT, page_path: str = PAGE,
          backlink: str = "wiki/sources/reconcile-topic-2026-08.md",
          ledger_mutate=None, drop_index: bool = False) -> dict:
    work.mkdir(parents=True, exist_ok=True)
    def w(name: str, text: str) -> str:
        p = work / name
        p.write_text(text, encoding="utf-8")
        return str(p.resolve())

    writes = [{"path": page_path, "mode": "create", "content_file": w("page.md", page)}]
    if not drop_index:
        idx = (vault / "wiki/index.md").read_text(encoding="utf-8").replace(
            "- [[unledgered-topic-2026-08]] — Unledgered topic\n",
            f"- [[unledgered-topic-2026-08]] — Unledgered topic\n- [[{SLUG}]] — 取り込みテスト\n")
        writes.append({"path": "wiki/index.md", "mode": "replace",
                       "content_file": w("index.md", idx.replace("updated: 2026-08-19", "updated: 2026-08-19"))})
    bl = (vault / backlink).read_text(encoding="utf-8")
    bl = bl.replace("を参照する。", f"を参照する。\n同じ経路の [[{SLUG}]] もある。", 1)
    writes.append({"path": backlink, "mode": "replace", "content_file": w("bl.md", bl)})

    ledger = json.loads((vault / LEDGER).read_text(encoding="utf-8"))
    raw = (vault / ".raw/fresh-source.md").read_bytes()
    ledger["sources"]["src-fixturefresh0000000000"] = {
        "authority": "community", "content_kind": "webpage",
        "content_sha256": hashlib.sha256(raw).hexdigest(),
        "origin": {"kind": "file", "locator": ".raw/fresh-source.md"},
        "pages": [page_path], "refresh_due": "2027-08-19", "retrieved_at": "2026-08-19",
        "review_status": "active", "title": "取り込みテスト用のソース"}
    ledger["generated_at"] = "2026-08-19T08:00:00Z"
    if ledger_mutate:
        ledger_mutate(ledger)
    writes.append({"path": LEDGER, "mode": "replace",
                   "content_file": w("ledger.json", json.dumps(ledger, ensure_ascii=False, indent=2) + "\n")})
    return {"writes": writes}


def _failed(report) -> list[str]:
    return [l for l in report.lines if l.startswith("[NG]")]


def test_happy_path(vi, vault: Path, tmp_path: Path) -> None:
    report = vi.verify(vault, _plan(vault, tmp_path / "w"))
    assert not report.failed, _failed(report)


def test_hub_as_backlink_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    """ハブを被リンク先にしても規則5 は消えない。最も気づきにくい失敗。"""
    plan = _plan(vault, tmp_path / "w")
    plan["writes"] = [w for w in plan["writes"]
                      if w["path"] != "wiki/sources/reconcile-topic-2026-08.md"]
    hot = (vault / "wiki/hot.md").read_text(encoding="utf-8").replace(
        "## Last Updated\n\n", f"## Last Updated\n\n- [[{SLUG}]]\n", 1)
    p = tmp_path / "w/hot.md"
    p.write_text(hot, encoding="utf-8")
    plan["writes"].append({"path": "wiki/hot.md", "mode": "replace", "content_file": str(p.resolve())})
    report = vi.verify(vault, plan)
    assert report.failed
    assert any("被リンク先の replace が1件以上" in l for l in _failed(report))


def test_relative_content_file_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    """ledger stage --staging-dir に相対を渡した場合の再現（規約10節の既知の罠）。"""
    plan = _plan(vault, tmp_path / "w")
    plan["writes"][-1]["content_file"] = "staging/source-ledger.json"
    report = vi.verify(vault, plan)
    assert report.failed
    assert any("絶対パス" in l for l in _failed(report))


def test_missing_index_write_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    report = vi.verify(vault, _plan(vault, tmp_path / "w", drop_index=True))
    assert report.failed
    assert any("index.md の replace" in l for l in _failed(report))


def test_evergreen_status_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    page = PAGE_TEXT.replace("status: developing", "status: evergreen")
    report = vi.verify(vault, _plan(vault, tmp_path / "w", page=page))
    assert report.failed
    assert any("status が developing" in l for l in _failed(report))


def test_bad_slug_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    report = vi.verify(vault, _plan(vault, tmp_path / "w",
                                    page_path="wiki/sources/FreshTopic.md"))
    assert report.failed
    assert any("slug が <英数ハイフン>" in l for l in _failed(report))


def test_slug_collision_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    report = vi.verify(vault, _plan(vault, tmp_path / "w",
                                    page_path="wiki/sources/reconcile-topic-2026-08.md"))
    assert report.failed
    assert any("slug が既存と衝突しない" in l for l in _failed(report))


def test_missing_sources_section_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    page = PAGE_TEXT.replace("## 出典\n\n- 原本: .raw/fresh-source.md （取得日: 2026-08-19）\n", "")
    report = vi.verify(vault, _plan(vault, tmp_path / "w", page=page))
    assert report.failed
    assert any("## 出典" in l for l in _failed(report))


def test_unresolved_wikilink_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    page = PAGE_TEXT.replace("[[reconcile-topic-2026-08]]", "[[does-not-exist-2026-08]]")
    report = vi.verify(vault, _plan(vault, tmp_path / "w", page=page))
    assert report.failed
    assert any("wikilink" in l for l in _failed(report))


def test_ledger_schema_change_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    report = vi.verify(vault, _plan(vault, tmp_path / "w",
                                    ledger_mutate=lambda d: d.update(schema="something-else.v9")))
    assert report.failed
    assert any("schema が書き換わっていない" in l for l in _failed(report))


def test_dropping_existing_ledger_entry_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    """dict.update の取り違えで既存エントリが消える事故を検出する。"""
    def drop(d):
        d["sources"].pop("src-fixture-reconcile00")
    report = vi.verify(vault, _plan(vault, tmp_path / "w", ledger_mutate=drop))
    assert report.failed
    assert any("1件も欠けていない" in l for l in _failed(report))


def test_inbox_locator_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    def to_inbox(d):
        d["sources"]["src-fixturefresh0000000000"]["origin"]["locator"] = "inbox/fresh-source.md"
    report = vi.verify(vault, _plan(vault, tmp_path / "w", ledger_mutate=to_inbox))
    assert report.failed
    assert any("locator が .raw/ か URL" in l for l in _failed(report))


def test_unreviewed_status_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    def unreviewed(d):
        d["sources"]["src-fixturefresh0000000000"]["review_status"] = "unreviewed"
    report = vi.verify(vault, _plan(vault, tmp_path / "w", ledger_mutate=unreviewed))
    assert report.failed
    assert any("review_status が active" in l for l in _failed(report))


def test_bad_generated_at_format_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    report = vi.verify(vault, _plan(vault, tmp_path / "w",
                                    ledger_mutate=lambda d: d.update(generated_at="2026-08-19")))
    assert report.failed
    assert any("generated_at" in l for l in _failed(report))


def test_delete_in_tx2_is_rejected(vi, vault: Path, tmp_path: Path) -> None:
    plan = _plan(vault, tmp_path / "w")
    plan["writes"].append({"path": "inbox/fresh-source.md", "mode": "delete"})
    report = vi.verify(vault, plan)
    assert report.failed
    assert any("delete が含まれていない" in l for l in _failed(report))
