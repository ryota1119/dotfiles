"""lint の集約と出力形式（設計書6節）。

規則1〜8と11は violation、規則9〜10は review。番号は追記のみで振り直さないため、
番号の大小と level は対応しない。取捨選択は人間が行うため、
この層は判定結果を並べるだけで、修正の提案はしない。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from .findings import Finding, sort_findings
from .frontmatter import collect_pages
from .graph import build_graph, check_broken_links, check_index, check_orphans
from .hygiene import check_conflict_copies, check_empty_sections, check_trailing_newline
from .ledger import (
    check_claims,
    check_page_ledger_consistency,
    check_refresh_due,
    check_review_status,
)
from .maturity import check_promotion_queue, check_stale_developing
from .schema import check_pages
from .vault import Vault

LINT_REPORT_SCHEMA = "vaultctl.lint-report.v1"

EXIT_OK = 0
EXIT_VIOLATION = 1
EXIT_REVIEW = 2
EXIT_USAGE = 64


@dataclass(frozen=True)
class LintReport:
    findings: list[Finding]

    @property
    def violations(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "violation"]

    @property
    def reviews(self) -> list[Finding]:
        return [f for f in self.findings if f.level == "review"]


def run_lint(vault: Vault, *, today: date) -> LintReport:
    """規則1〜11のすべての checker を呼び、findings を整列して返す。"""
    root = vault.root
    pages, unreadable = collect_pages(root)
    graph = build_graph(pages)

    findings: list[Finding] = []
    findings.extend(unreadable)                              # frontmatter を読めない .md
    findings.extend(check_pages(pages))                      # 規則1〜3
    findings.extend(check_broken_links(graph))               # 規則4
    findings.extend(check_orphans(graph))                    # 規則5
    for page in pages:
        findings.extend(check_empty_sections(page))          # 規則6
    findings.extend(check_index(graph))                      # 規則7
    findings.extend(check_conflict_copies(root))             # 規則8
    findings.extend(check_promotion_queue(pages))            # 規則9-a
    findings.extend(check_stale_developing(pages, today))    # 規則9-b
    findings.extend(check_page_ledger_consistency(root, pages))  # 規則10-a
    findings.extend(check_refresh_due(root, today))          # 規則10-b
    findings.extend(check_review_status(root))               # 規則10-c
    findings.extend(check_claims(root, pages))               # 規則10-d
    findings.extend(check_trailing_newline(root))            # 規則11

    return LintReport(findings=sort_findings(findings))


def format_text(report: LintReport) -> str:
    """人間が読む1行1件のテキスト。1行目は件数の要約。"""
    lines = [f"violation {len(report.violations)} 件 / review {len(report.reviews)} 件"]
    for finding in report.findings:
        where = finding.path or "(vault 全体)"
        lines.append(f"[{finding.level}] 規則{finding.rule}\t{where}\t{finding.message}")
    if not report.findings:
        lines.append("指摘なし")
    return "\n".join(lines) + "\n"


def format_json(report: LintReport) -> str:
    """機械可読な JSON。正準JSONではなく indent=2 の人間可読形式にする。"""
    payload = {
        "schema": LINT_REPORT_SCHEMA,
        "counts": {
            "violation": len(report.violations),
            "review": len(report.reviews),
        },
        "findings": [
            {
                "rule": finding.rule,
                "level": finding.level,
                "path": finding.path,
                "message": finding.message,
            }
            for finding in report.findings
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
