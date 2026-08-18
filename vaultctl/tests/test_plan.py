import json

import pytest

from vaultctl.cli import main
from vaultctl.hashing import canonical_sha256, sha256_bytes
from vaultctl.plan import (
    BUNDLE_SCHEMA,
    PLAN_SCHEMA,
    PlanError,
    build_plan,
    load_bundle,
    plan_approval_sha256,
)


def make_bundle(writes, operation_id="ingest-20260817-inbox-batch"):
    return {
        "schema": BUNDLE_SCHEMA,
        "operation_id": operation_id,
        "operation_type": "ingest",
        "writes": writes,
    }


def content(tmp_path, name, data: bytes) -> str:
    path = tmp_path / name
    path.write_bytes(data)
    return str(path)


def test_build_plan_records_hashes_for_each_mode(vault, tmp_path):
    (vault.wiki / "index.md").write_bytes(b"old index\n")
    (vault.inbox / "foo.html").write_bytes(b"<html>\n")
    new_page = content(tmp_path, "foo.md", b"new page\n")
    new_index = content(tmp_path, "index.md", b"new index\n")

    bundle = make_bundle(
        [
            {
                "path": "wiki/sources/foo.md",
                "mode": "create",
                "content_file": new_page,
            },
            {
                "path": "wiki/index.md",
                "mode": "replace",
                "content_file": new_index,
            },
            {"path": "inbox/foo.html", "mode": "delete"},
        ]
    )
    plan = build_plan(vault, bundle)

    assert plan["schema"] == PLAN_SCHEMA
    assert plan["vault_id"] == vault.vault_id
    assert plan["operation_id"] == "ingest-20260817-inbox-batch"
    assert plan["operation_type"] == "ingest"
    assert plan["input_bundle_sha256"] == canonical_sha256(bundle)

    created, replaced, deleted = plan["writes"]
    assert created["original_sha256"] is None
    assert created["new_sha256"] == sha256_bytes(b"new page\n")
    assert created["content_file"] == new_page
    assert replaced["original_sha256"] == sha256_bytes(b"old index\n")
    assert replaced["new_sha256"] == sha256_bytes(b"new index\n")
    assert deleted["original_sha256"] == sha256_bytes(b"<html>\n")
    assert deleted["new_sha256"] is None
    assert deleted["content_file"] is None
    assert plan["approval_sha256"] == plan_approval_sha256(plan)


def test_build_plan_rejects_parent_traversal(vault, tmp_path):
    src = content(tmp_path, "evil.md", b"x\n")
    bundle = make_bundle(
        [{"path": "wiki/../../evil.md", "mode": "create", "content_file": src}]
    )
    with pytest.raises(PlanError):
        build_plan(vault, bundle)


def test_build_plan_rejects_absolute_path(vault, tmp_path):
    src = content(tmp_path, "abs.md", b"x\n")
    bundle = make_bundle(
        [{"path": "/etc/passwd", "mode": "create", "content_file": src}]
    )
    with pytest.raises(PlanError):
        build_plan(vault, bundle)


def test_build_plan_rejects_create_on_existing_file(vault, tmp_path):
    src = content(tmp_path, "index.md", b"x\n")
    bundle = make_bundle(
        [{"path": "wiki/index.md", "mode": "create", "content_file": src}]
    )
    with pytest.raises(PlanError):
        build_plan(vault, bundle)


def test_build_plan_rejects_replace_on_missing_file(vault, tmp_path):
    src = content(tmp_path, "ghost.md", b"x\n")
    bundle = make_bundle(
        [{"path": "wiki/concepts/ghost.md", "mode": "replace", "content_file": src}]
    )
    with pytest.raises(PlanError):
        build_plan(vault, bundle)


def test_build_plan_rejects_delete_on_missing_file(vault):
    bundle = make_bundle([{"path": "inbox/ghost.html", "mode": "delete"}])
    with pytest.raises(PlanError):
        build_plan(vault, bundle)


def test_build_plan_rejects_unknown_mode(vault, tmp_path):
    src = content(tmp_path, "x.md", b"x\n")
    bundle = make_bundle(
        [{"path": "wiki/concepts/x.md", "mode": "append", "content_file": src}]
    )
    with pytest.raises(PlanError):
        build_plan(vault, bundle)


def test_build_plan_rejects_duplicate_paths(vault, tmp_path):
    first = content(tmp_path, "a.md", b"a\n")
    second = content(tmp_path, "b.md", b"b\n")
    bundle = make_bundle(
        [
            {"path": "wiki/concepts/x.md", "mode": "create", "content_file": first},
            {"path": "wiki/concepts/x.md", "mode": "create", "content_file": second},
        ]
    )
    with pytest.raises(PlanError):
        build_plan(vault, bundle)


def test_plan_approval_sha256_ignores_approval_key(vault, tmp_path):
    src = content(tmp_path, "x.md", b"x\n")
    bundle = make_bundle(
        [{"path": "wiki/concepts/x.md", "mode": "create", "content_file": src}]
    )
    plan = build_plan(vault, bundle)

    without_key = {k: v for k, v in plan.items() if k != "approval_sha256"}
    tampered = dict(plan)
    tampered["approval_sha256"] = "0" * 64

    assert plan_approval_sha256(without_key) == plan["approval_sha256"]
    assert plan_approval_sha256(tampered) == plan["approval_sha256"]


def test_load_bundle_rejects_wrong_schema(tmp_path):
    path = tmp_path / "bundle.json"
    path.write_text(
        json.dumps({"schema": "other.v1", "operation_id": "a", "writes": []}),
        encoding="utf-8",
    )
    with pytest.raises(PlanError):
        load_bundle(path)


def test_load_bundle_rejects_broken_json(tmp_path):
    path = tmp_path / "bundle.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(PlanError):
        load_bundle(path)


def test_load_bundle_reads_valid_bundle(tmp_path):
    bundle = make_bundle([{"path": "inbox/a.html", "mode": "delete"}])
    path = tmp_path / "bundle.json"
    path.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    assert load_bundle(path) == bundle


def test_cli_plan_writes_plan_and_prints_approval_hash(vault, tmp_path, capsys):
    src = content(tmp_path, "x.md", b"x\n")
    bundle = make_bundle(
        [{"path": "wiki/concepts/x.md", "mode": "create", "content_file": src}]
    )
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    out_path = tmp_path / "plan.json"

    code = main(
        [
            "--vault",
            str(vault.root),
            "plan",
            "--bundle",
            str(bundle_path),
            "--out",
            str(out_path),
        ]
    )

    assert code == 0
    printed = capsys.readouterr().out.strip()
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert written["schema"] == PLAN_SCHEMA
    assert printed == written["approval_sha256"]
    assert printed == plan_approval_sha256(written)
    # vault は変更されない
    assert not (vault.wiki / "concepts" / "x.md").exists()


def test_cli_plan_returns_1_on_plan_error(vault, tmp_path, capsys):
    bundle = make_bundle([{"path": "inbox/ghost.html", "mode": "delete"}])
    bundle_path = tmp_path / "bundle.json"
    bundle_path.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")

    code = main(
        [
            "--vault",
            str(vault.root),
            "plan",
            "--bundle",
            str(bundle_path),
            "--out",
            str(tmp_path / "plan.json"),
        ]
    )

    assert code == 1
    assert "error:" in capsys.readouterr().err
