"""source / claim ledger の読み書きと整合検査（lint 規則10、設計書 6.2・7節）。

既存 ledger の `schema` 文字列は `claude-obsidian.*` のまま維持する（書き換えない）。
読み込み側だけが `claude-obsidian.*` と `vaultctl.*` の両方を受け付ける。
"""

from __future__ import annotations

import copy
import json
from datetime import date
from pathlib import Path
from typing import Iterable

from .findings import Finding, sort_findings
from .frontmatter import Page

SOURCE_LEDGER_RELPATH = "wiki/meta/ledgers/source-ledger.json"
CLAIM_LEDGER_RELPATH = "wiki/meta/ledgers/claim-ledger.json"

_SOURCE_SCHEMA_SUFFIX = "source-ledger.v1"
_CLAIM_SCHEMA_SUFFIX = "claim-ledger.v1"
_ACCEPTED_SCHEMA_PREFIXES = ("claude-obsidian.", "vaultctl.")


class LedgerError(Exception):
    """ledger を読めない、または想定外の形をしている。"""


def _parse_date(value: object) -> date | None:
    if isinstance(value, str):
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None
    return None


def _dump_ledger(obj: dict) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _load(root: Path, relpath: str, suffix: str, container: str) -> dict:
    path = Path(root) / relpath
    if not path.exists():
        return {"schema": f"vaultctl.{suffix}", "generated_at": None, container: {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise LedgerError(f"ledger を読めない: {relpath}: {exc}") from exc
    if not isinstance(data, dict):
        raise LedgerError(f"ledger の最上位が object でない: {relpath}")
    schema = data.get("schema")
    if not isinstance(schema, str) or schema not in tuple(
        prefix + suffix for prefix in _ACCEPTED_SCHEMA_PREFIXES
    ):
        raise LedgerError(f"未知の ledger schema: {schema!r}（{relpath}）")
    if not isinstance(data.get(container), dict):
        raise LedgerError(f"ledger の {container} が object でない: {relpath}")
    return data


def load_source_ledger(root: Path) -> dict:
    return _load(root, SOURCE_LEDGER_RELPATH, _SOURCE_SCHEMA_SUFFIX, "sources")


def load_claim_ledger(root: Path) -> dict:
    return _load(root, CLAIM_LEDGER_RELPATH, _CLAIM_SCHEMA_SUFFIX, "claims")


def check_page_ledger_consistency(root: Path, pages: Iterable[Page]) -> list[Finding]:
    """規則10-a: ページ ↔ source-ledger の双方向整合。

    ledger が参照するページは `wiki/sources/**` に限らず、`wiki/concepts/**` と
    `wiki/entities/**` も対象になる（設計書 6.2 節）。逆方向（ledger から
    参照されていないページ）は出所追跡が目的なので `wiki/sources/**` のみを見る。
    """
    pages = list(pages)
    existing = {p.relpath for p in pages}
    ledger = load_source_ledger(root)
    sources = ledger["sources"]
    referenced: set[str] = set()
    findings: list[Finding] = []

    for source_id in sorted(sources):
        for relpath in sources[source_id].get("pages") or []:
            referenced.add(relpath)
            if relpath not in existing:
                findings.append(
                    Finding(
                        rule="10-a",
                        level="review",
                        path=relpath,
                        message=f"ledger が参照するページが存在しない（source_id={source_id}）",
                    )
                )

    for page in pages:
        if not page.relpath.startswith("wiki/sources/"):
            continue
        if page.relpath in referenced:
            continue
        findings.append(
            Finding(
                rule="10-a",
                level="review",
                path=page.relpath,
                message="source-ledger から参照されていない source ページ（出所が追えない）",
            )
        )

    return sort_findings(findings)


def check_refresh_due(root: Path, today: date) -> list[Finding]:
    """規則10-b: `refresh_due` の超過。当日ちょうどは超過としない。"""
    sources = load_source_ledger(root)["sources"]
    findings: list[Finding] = []
    for source_id in sorted(sources):
        entry = sources[source_id]
        due = _parse_date(entry.get("refresh_due"))
        if due is None or due >= today:
            continue
        entry_pages = entry.get("pages") or []
        findings.append(
            Finding(
                rule="10-b",
                level="review",
                path=entry_pages[0] if entry_pages else "",
                message=(
                    f"refresh_due 超過: source_id={source_id} "
                    f"refresh_due={due.isoformat()}（{(today - due).days}日超過）"
                ),
            )
        )
    return sort_findings(findings)


def check_review_status(root: Path) -> list[Finding]:
    """規則10-c: `review_status: unreviewed` の滞留。"""
    sources = load_source_ledger(root)["sources"]
    findings: list[Finding] = []
    for source_id in sorted(sources):
        entry = sources[source_id]
        if entry.get("review_status") != "unreviewed":
            continue
        entry_pages = entry.get("pages") or []
        findings.append(
            Finding(
                rule="10-c",
                level="review",
                path=entry_pages[0] if entry_pages else "",
                message=f"review_status: unreviewed のまま滞留している（source_id={source_id}）",
            )
        )
    return sort_findings(findings)


def check_claims(root: Path, pages: Iterable[Page]) -> list[Finding]:
    """規則10-d: ページの `claim_ids` の実在確認と、孤児 claim の検出。"""
    pages = list(pages)
    existing = {p.relpath for p in pages}
    claims = load_claim_ledger(root)["claims"]
    findings: list[Finding] = []

    for page in pages:
        for claim_id in page.frontmatter.get("claim_ids") or []:
            if claim_id not in claims:
                findings.append(
                    Finding(
                        rule="10-d",
                        level="review",
                        path=page.relpath,
                        message=f"claim_ids の {claim_id} が claim-ledger に存在しない",
                    )
                )

    for claim_id in sorted(claims):
        location = claims[claim_id].get("location") or {}
        relpath = location.get("path")
        if not relpath:
            findings.append(
                Finding(
                    rule="10-d",
                    level="review",
                    path="",
                    message=f"孤児 claim: {claim_id} に location.path がない",
                )
            )
            continue
        if relpath not in existing:
            findings.append(
                Finding(
                    rule="10-d",
                    level="review",
                    path=relpath,
                    message=f"孤児 claim: {claim_id} の location.path が存在しない",
                )
            )

    return sort_findings(findings)


def _stage_one(
    root: Path,
    staging_dir: Path,
    *,
    relpath: str,
    filename: str,
    ledger: dict,
    container: str,
    entries: dict,
) -> dict:
    merged = dict(ledger[container])
    merged.update(entries)
    ledger[container] = merged
    staged_path = staging_dir / filename
    staged_path.write_text(_dump_ledger(ledger), encoding="utf-8")
    mode = "replace" if (Path(root) / relpath).exists() else "create"
    return {"path": relpath, "mode": mode, "content_file": str(staged_path)}


def stage_ledger_writes(
    root: Path,
    bundle: dict,
    *,
    sources: dict | None = None,
    claims: dict | None = None,
    staging_dir: Path,
) -> dict:
    """ledger 追記を bundle の writes に足した新しい bundle を返す。

    ページ作成と ledger 追記が同一トランザクションに入るようにするための入口
    （設計書7節）。既存 ledger の `schema` 文字列は書き換えない。
    `generated_at` も更新しない（決定論性を保つため、更新は呼び出し側の責務）。
    """
    staged = copy.deepcopy(bundle)
    writes = list(staged.get("writes", []))
    staging_dir = Path(staging_dir)
    staging_dir.mkdir(parents=True, exist_ok=True)

    if sources:
        writes.append(
            _stage_one(
                root,
                staging_dir,
                relpath=SOURCE_LEDGER_RELPATH,
                filename="source-ledger.json",
                ledger=load_source_ledger(root),
                container="sources",
                entries=sources,
            )
        )
    if claims:
        writes.append(
            _stage_one(
                root,
                staging_dir,
                relpath=CLAIM_LEDGER_RELPATH,
                filename="claim-ledger.json",
                ledger=load_claim_ledger(root),
                container="claims",
                entries=claims,
            )
        )

    staged["writes"] = writes
    return staged
