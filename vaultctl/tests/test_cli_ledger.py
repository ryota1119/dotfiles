"""vaultctl ledger subcommand のテスト."""

from __future__ import annotations

import json
from pathlib import Path

from conftest import make_page

from vaultctl.cli import main
from vaultctl.ledger import SOURCE_LEDGER_RELPATH


def _write_source_ledger(root: Path, sources: dict) -> None:
    path = root / SOURCE_LEDGER_RELPATH
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": "claude-obsidian.source-ledger.v1",
                "generated_at": "2026-08-16T02:49:49Z",
                "sources": sources,
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_ledger_stage_appends_write_to_bundle(synthetic_vault_root, tmp_path):
    _write_source_ledger(synthetic_vault_root, {})
    page = tmp_path / "foo.md"
    page.write_text("---\ntype: source\n---\n\n# foo\n", encoding="utf-8")

    bundle = tmp_path / "bundle.json"
    bundle.write_text(
        json.dumps(
            {
                "schema": "vaultctl.bundle.v1",
                "operation_id": "ingest-20260817-cli",
                "operation_type": "ingest",
                "writes": [
                    {"path": "wiki/sources/foo.md", "mode": "create", "content_file": str(page)}
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    entry = tmp_path / "entry.json"
    entry.write_text(
        json.dumps(
            {
                "src-cli0000000000000000": {
                    "authority": "community",
                    "content_kind": "webpage",
                    "content_sha256": "0" * 64,
                    "origin": {"kind": "url", "locator": "https://example.com/foo"},
                    "pages": ["wiki/sources/foo.md"],
                    "refresh_due": "2027-08-17",
                    "retrieved_at": "2026-08-17",
                    "review_status": "active",
                    "title": "例のソース",
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    out = tmp_path / "bundle-staged.json"
    code = main(
        [
            "--vault",
            str(synthetic_vault_root),
            "ledger",
            "stage",
            "--bundle",
            str(bundle),
            "--out",
            str(out),
            "--add-source",
            str(entry),
        ]
    )

    assert code == 0
    staged = json.loads(out.read_text(encoding="utf-8"))
    paths = [w["path"] for w in staged["writes"]]
    assert paths == ["wiki/sources/foo.md", SOURCE_LEDGER_RELPATH]


def test_ledger_verify_exit_code_is_2_when_review_findings_exist(synthetic_vault_root):
    # ledger から参照されていない source ページ → 規則10-a（review）
    _write_source_ledger(synthetic_vault_root, {})
    make_page(
        synthetic_vault_root,
        "wiki/sources/orphan-source.md",
        type="source",
        title="孤立ソース",
        status="evergreen",
        created="2026-08-01",
        updated="2026-08-01",
        tags=["source"],
    )

    code = main(["--vault", str(synthetic_vault_root), "ledger", "verify"])
    assert code == 2
