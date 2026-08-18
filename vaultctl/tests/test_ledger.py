"""ledger の読み書きと lint 規則10のテスト。"""

import json
from datetime import date
from pathlib import Path

import pytest

import vaultctl.apply
from vaultctl.apply import apply_plan
from vaultctl.frontmatter import Page
from vaultctl.ledger import (
    CLAIM_LEDGER_RELPATH,
    SOURCE_LEDGER_RELPATH,
    LedgerError,
    check_claims,
    check_page_ledger_consistency,
    check_refresh_due,
    check_review_status,
    load_claim_ledger,
    load_source_ledger,
    stage_ledger_writes,
)
from vaultctl.plan import BUNDLE_SCHEMA, build_plan
from vaultctl.vault import resolve_vault


def make_page(relpath, *, type_, claim_ids=None):
    slug = relpath.rsplit("/", 1)[-1][: -len(".md")]
    frontmatter = {
        "type": type_,
        "title": slug,
        "status": "evergreen",
        "created": date(2026, 1, 1),
        "updated": date(2026, 8, 1),
        "tags": [],
    }
    if claim_ids is not None:
        frontmatter["claim_ids"] = claim_ids
    return Page(relpath=relpath, slug=slug, frontmatter=frontmatter, body="## 概要\n\n本文\n")


def source_entry(pages, *, refresh_due="2027-08-01", review_status="active"):
    return {
        "authority": "official",
        "content_kind": "webpage",
        "content_sha256": "0" * 64,
        "origin": {"kind": "url", "locator": "https://example.com/"},
        "pages": list(pages),
        "refresh_due": refresh_due,
        "retrieved_at": "2026-08-01",
        "review_status": review_status,
        "title": "テスト用ソース",
    }


def claim_entry(path):
    return {
        "assessment": "provisional",
        "confidence": "low",
        "evidence": [{"relation": "supports", "source_id": "src-a"}],
        "location": {"anchor": "抽出した事実", "path": path},
        "notes": "テスト用",
        "reviewed_at": "2026-08-01",
        "risk": "normal",
        "text": "テスト用の主張",
    }


def write_ledgers(root: Path, sources=None, claims=None, *, source_schema=None, claim_schema=None):
    ledger_dir = root / "wiki" / "meta" / "ledgers"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    if sources is not None:
        (root / SOURCE_LEDGER_RELPATH).write_text(
            json.dumps(
                {
                    "generated_at": "2026-08-16T02:49:49Z",
                    "schema": source_schema or "claude-obsidian.source-ledger.v1",
                    "sources": sources,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    if claims is not None:
        (root / CLAIM_LEDGER_RELPATH).write_text(
            json.dumps(
                {
                    "claims": claims,
                    "generated_at": "2026-08-16T02:49:49Z",
                    "schema": claim_schema or "claude-obsidian.claim-ledger.v1",
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )


@pytest.mark.parametrize(
    "schema",
    ["claude-obsidian.source-ledger.v1", "vaultctl.source-ledger.v1"],
)
def test_load_source_ledger_accepts_both_schema_prefixes(tmp_path, schema):
    write_ledgers(tmp_path, sources={"src-a": source_entry(["wiki/sources/a.md"])}, source_schema=schema)

    ledger = load_source_ledger(tmp_path)

    assert ledger["schema"] == schema
    assert list(ledger["sources"]) == ["src-a"]


@pytest.mark.parametrize(
    "schema",
    ["claude-obsidian.claim-ledger.v1", "vaultctl.claim-ledger.v1"],
)
def test_load_claim_ledger_accepts_both_schema_prefixes(tmp_path, schema):
    write_ledgers(tmp_path, claims={"clm-a": claim_entry("wiki/sources/a.md")}, claim_schema=schema)

    ledger = load_claim_ledger(tmp_path)

    assert ledger["schema"] == schema
    assert list(ledger["claims"]) == ["clm-a"]


def test_load_source_ledger_returns_empty_when_missing(tmp_path):
    ledger = load_source_ledger(tmp_path)

    assert ledger["sources"] == {}
    assert ledger["schema"] == "vaultctl.source-ledger.v1"


def test_load_source_ledger_rejects_unknown_schema(tmp_path):
    write_ledgers(tmp_path, sources={}, source_schema="somebody-else.source-ledger.v1")

    with pytest.raises(LedgerError):
        load_source_ledger(tmp_path)


def test_load_claim_ledger_rejects_broken_json(tmp_path):
    (tmp_path / "wiki" / "meta" / "ledgers").mkdir(parents=True)
    (tmp_path / CLAIM_LEDGER_RELPATH).write_text("{壊れている", encoding="utf-8")

    with pytest.raises(LedgerError):
        load_claim_ledger(tmp_path)


def test_check_10a_detects_source_page_missing_from_ledger(tmp_path):
    write_ledgers(tmp_path, sources={"src-a": source_entry(["wiki/sources/a.md"])})
    pages = [
        make_page("wiki/sources/a.md", type_="source"),
        make_page("wiki/sources/b.md", type_="source"),
    ]

    findings = check_page_ledger_consistency(tmp_path, pages)

    assert [f.path for f in findings] == ["wiki/sources/b.md"]
    assert findings[0].rule == "10-a"
    assert findings[0].level == "review"
    assert "参照されていない" in findings[0].message


def test_check_10a_detects_ledger_pointing_to_missing_page(tmp_path):
    write_ledgers(
        tmp_path,
        sources={
            "src-a": source_entry(["wiki/concepts/gone.md"]),
            "src-b": source_entry(["wiki/entities/cloudflare.md"]),
        },
    )
    pages = [make_page("wiki/entities/cloudflare.md", type_="entity")]

    findings = check_page_ledger_consistency(tmp_path, pages)

    assert [f.path for f in findings] == ["wiki/concepts/gone.md"]
    assert "存在しない" in findings[0].message


def test_check_10a_ignores_non_source_pages_for_the_reverse_direction(tmp_path):
    write_ledgers(tmp_path, sources={})
    pages = [
        make_page("wiki/concepts/a.md", type_="concept"),
        make_page("wiki/entities/b.md", type_="entity"),
    ]

    assert check_page_ledger_consistency(tmp_path, pages) == []


@pytest.mark.parametrize(
    "refresh_due,expected",
    [("2026-08-18", 0), ("2026-08-17", 0), ("2026-08-16", 1)],
)
def test_check_10b_refresh_due_boundary(tmp_path, refresh_due, expected):
    write_ledgers(
        tmp_path,
        sources={"src-a": source_entry(["wiki/sources/a.md"], refresh_due=refresh_due)},
    )

    findings = check_refresh_due(tmp_path, date(2026, 8, 17))

    assert len(findings) == expected
    if expected:
        assert findings[0].rule == "10-b"
        assert findings[0].level == "review"
        assert findings[0].path == "wiki/sources/a.md"
        assert "refresh_due=2026-08-16" in findings[0].message
        assert "1日超過" in findings[0].message


def test_check_10c_reports_unreviewed_entries(tmp_path):
    write_ledgers(
        tmp_path,
        sources={
            "src-a": source_entry(["wiki/sources/a.md"], review_status="active"),
            "src-b": source_entry(["wiki/sources/b.md"], review_status="unreviewed"),
        },
    )

    findings = check_review_status(tmp_path)

    assert [f.path for f in findings] == ["wiki/sources/b.md"]
    assert findings[0].rule == "10-c"
    assert "unreviewed" in findings[0].message


def test_check_10d_detects_missing_claim_and_orphan_claim(tmp_path):
    write_ledgers(tmp_path, claims={"clm-orphan": claim_entry("wiki/sources/vanished.md")})
    pages = [make_page("wiki/sources/a.md", type_="source", claim_ids=["clm-missing"])]

    findings = check_claims(tmp_path, pages)

    assert {f.rule for f in findings} == {"10-d"}
    messages = {f.path: f.message for f in findings}
    assert "clm-missing" in messages["wiki/sources/a.md"]
    assert "clm-orphan" in messages["wiki/sources/vanished.md"]


def test_check_10d_accepts_resolvable_claims(tmp_path):
    write_ledgers(tmp_path, claims={"clm-a": claim_entry("wiki/sources/a.md")})
    pages = [make_page("wiki/sources/a.md", type_="source", claim_ids=["clm-a"])]

    assert check_claims(tmp_path, pages) == []


def make_vault_root(tmp_path: Path) -> Path:
    root = tmp_path / "vault"
    (root / "wiki" / "sources").mkdir(parents=True)
    (root / "wiki" / "meta" / "ledgers").mkdir(parents=True)
    (root / "inbox").mkdir(parents=True)
    return root


def test_stage_ledger_writes_appends_writes_without_mutating_input(tmp_path):
    root = make_vault_root(tmp_path)
    write_ledgers(root, sources={"src-a": source_entry(["wiki/sources/a.md"])}, claims={})
    bundle = {
        "schema": BUNDLE_SCHEMA,
        "operation_id": "ingest-test-stage",
        "operation_type": "ingest",
        "writes": [{"path": "wiki/sources/b.md", "mode": "create", "content_file": "/tmp/dummy.md"}],
    }

    staged = stage_ledger_writes(
        root,
        bundle,
        sources={"src-b": source_entry(["wiki/sources/b.md"])},
        claims={"clm-b": claim_entry("wiki/sources/b.md")},
        staging_dir=tmp_path / "staging",
    )

    assert [w["path"] for w in bundle["writes"]] == ["wiki/sources/b.md"]
    assert [w["path"] for w in staged["writes"]] == [
        "wiki/sources/b.md",
        SOURCE_LEDGER_RELPATH,
        CLAIM_LEDGER_RELPATH,
    ]
    assert staged["writes"][1]["mode"] == "replace"
    assert staged["writes"][2]["mode"] == "replace"

    staged_source = json.loads(Path(staged["writes"][1]["content_file"]).read_text(encoding="utf-8"))
    assert sorted(staged_source["sources"]) == ["src-a", "src-b"]
    assert staged_source["schema"] == "claude-obsidian.source-ledger.v1"


def test_stage_ledger_writes_uses_create_mode_when_ledger_absent(tmp_path):
    root = make_vault_root(tmp_path)
    bundle = {
        "schema": BUNDLE_SCHEMA,
        "operation_id": "ingest-test-create",
        "operation_type": "ingest",
        "writes": [],
    }

    staged = stage_ledger_writes(
        root,
        bundle,
        sources={"src-b": source_entry(["wiki/sources/b.md"])},
        staging_dir=tmp_path / "staging",
    )

    assert [(w["path"], w["mode"]) for w in staged["writes"]] == [
        (SOURCE_LEDGER_RELPATH, "create")
    ]


def test_ledger_write_rolls_back_with_the_transaction(tmp_path, monkeypatch):
    """設計書12節の検証項目9: ledger 追記が apply のトランザクションに含まれ、
    失敗時に一緒に巻き戻ること。"""
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    root = make_vault_root(tmp_path)
    write_ledgers(root, sources={"src-a": source_entry(["wiki/sources/a.md"])}, claims={})
    original_source = (root / SOURCE_LEDGER_RELPATH).read_bytes()
    original_claim = (root / CLAIM_LEDGER_RELPATH).read_bytes()

    content_file = tmp_path / "new-page.md"
    content_file.write_text("---\ntype: source\n---\n\n本文\n", encoding="utf-8")
    bundle = {
        "schema": BUNDLE_SCHEMA,
        "operation_id": "ingest-test-rollback",
        "operation_type": "ingest",
        "writes": [
            {"path": "wiki/sources/b.md", "mode": "create", "content_file": str(content_file)}
        ],
    }
    staged = stage_ledger_writes(
        root,
        bundle,
        sources={"src-b": source_entry(["wiki/sources/b.md"])},
        claims={"clm-b": claim_entry("wiki/sources/b.md")},
        staging_dir=tmp_path / "staging",
    )

    vault = resolve_vault(str(root))
    plan = build_plan(vault, staged)

    real_atomic_write = vaultctl.apply.atomic_write
    calls = {"n": 0}

    def flaky_atomic_write(target, data, *, mode=0o600):
        calls["n"] += 1
        if calls["n"] == 3:
            raise OSError("injected failure on the third write")
        real_atomic_write(target, data, mode=mode)

    monkeypatch.setattr(vaultctl.apply, "atomic_write", flaky_atomic_write)

    with pytest.raises(OSError):
        apply_plan(vault, plan, plan["approval_sha256"])

    assert not (root / "wiki" / "sources" / "b.md").exists()
    assert (root / SOURCE_LEDGER_RELPATH).read_bytes() == original_source
    assert (root / CLAIM_LEDGER_RELPATH).read_bytes() == original_claim
