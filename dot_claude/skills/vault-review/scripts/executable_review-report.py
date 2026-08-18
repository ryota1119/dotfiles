#!/usr/bin/env python3
"""lint / ledger verify の finding を対処区分別に整形する。"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable


SECTION_RULES = {
    "A": {"1", "2", "3", "6", "7"},
    "B": {"4", "5", "8", "11"},
    "C": {"10", "10-a", "10-b", "10-c", "10-d"},
    "D": {"9", "9-a", "9-b"},
}
SECTION_TITLES = (
    ("A", "A. 機械的に直せる違反"),
    ("B", "B. 判断が要る違反"),
    ("C", "C. 要レビュー・出所"),
    ("D", "D. 要レビュー・成熟度"),
)


def _parse_json(text: str, source: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"error: {source} の JSON を解析できません: {exc.msg}") from exc


def _validate_findings(value: Any, source: str) -> list[dict[str, str]]:
    if not isinstance(value, list):
        raise SystemExit(f"error: {source} の findings は配列である必要があります")
    findings: list[dict[str, str]] = []
    for index, finding in enumerate(value):
        if not isinstance(finding, dict):
            raise SystemExit(f"error: {source} の finding[{index}] は object である必要があります")
        required = ("rule", "level", "path", "message")
        if any(not isinstance(finding.get(key), str) for key in required):
            raise SystemExit(
                f"error: {source} の finding[{index}] は rule/level/path/message の文字列が必要です"
            )
        findings.append({key: finding[key] for key in required})
    return findings


def parse_lint_json(text: str) -> list[dict[str, str]]:
    """ラッパー付き lint JSON をパースする。"""
    value = _parse_json(text, "lint")
    if isinstance(value, list):
        raise SystemExit("error: lint JSON は裸の配列ではなくラッパー付き object が必要です")
    if not isinstance(value, dict) or not isinstance(value.get("counts"), dict) or "findings" not in value:
        raise SystemExit("error: lint JSON は counts と findings を持つ object が必要です")
    return _validate_findings(value["findings"], "lint JSON")


def parse_ledger_json(text: str) -> list[dict[str, str]]:
    """裸の finding 配列である ledger verify JSON をパースする。"""
    value = _parse_json(text, "ledger")
    if isinstance(value, dict):
        raise SystemExit("error: ledger JSON はラッパー付き object ではなく findings の裸の配列が必要です")
    return _validate_findings(value, "ledger JSON")


def finding_key(finding: dict[str, str]) -> tuple[str, str, str]:
    return finding["rule"], finding["path"], finding["message"]


def _format_finding(finding: dict[str, str]) -> str:
    path = finding["path"] or "(vault 全体)"
    return f"[規則{finding['rule']}] {path}: {finding['message']}"


def reconcile_findings(
    lint_findings: list[dict[str, str]], ledger_findings: list[dict[str, str]]
) -> tuple[list[dict[str, str]], list[str]]:
    """lint と ledger を照合し、キーが同じ finding を1件へまとめる。"""
    lint_rule10 = {
        finding_key(finding): finding
        for finding in lint_findings
        if finding["rule"] in SECTION_RULES["C"]
    }
    ledger_by_key = {finding_key(finding): finding for finding in ledger_findings}
    lint_only = sorted(lint_rule10.keys() - ledger_by_key.keys())
    ledger_only = sorted(ledger_by_key.keys() - lint_rule10.keys())

    if not lint_only and not ledger_only:
        preamble = [
            f"照合: lintの規則10とledger verifyが一致（{len(lint_rule10)}件、重複を除去）"
        ]
    else:
        preamble = [
            "警告: lintとledger verifyが食い違う"
            f"（lintのみ{len(lint_only)}件 / ledgerのみ{len(ledger_only)}件）"
        ]
        preamble.extend(f"- lintのみ {_format_finding(lint_rule10[key])}" for key in lint_only)
        preamble.extend(f"- ledgerのみ {_format_finding(ledger_by_key[key])}" for key in ledger_only)

    deduplicated: dict[tuple[str, str, str], dict[str, str]] = {}
    for finding in [*lint_findings, *ledger_findings]:
        deduplicated.setdefault(finding_key(finding), finding)
    merged = list(deduplicated.values())
    preamble.append(
        f"入力{len(lint_findings) + len(ledger_findings)}件 → 重複除去後{len(merged)}件"
    )
    return merged, preamble


def classify_findings(
    findings: Iterable[dict[str, str]],
) -> tuple[dict[str, list[dict[str, str]]], Counter[str]]:
    sections: dict[str, list[dict[str, str]]] = {key: [] for key, _ in SECTION_TITLES}
    unknown: Counter[str] = Counter()
    for finding in findings:
        rule = finding["rule"]
        section = next((key for key, rules in SECTION_RULES.items() if rule in rules), None)
        if section is None:
            section = "B"
            unknown[rule] += 1
        sections[section].append(finding)
    for values in sections.values():
        values.sort(key=lambda item: (item["rule"], item["path"], item["message"]))
    return sections, unknown


def render_report(findings: list[dict[str, str]], preamble: Iterable[str] = ()) -> str:
    lines = list(preamble)
    if not findings:
        lines.append("指摘なし")
        return "\n".join(lines) + "\n"

    sections, unknown = classify_findings(findings)
    if sum(len(values) for values in sections.values()) != len(findings):
        raise SystemExit("error: 区分別の件数合計が入力 finding 総数と一致しません")

    for key, title in SECTION_TITLES:
        values = sections[key]
        lines.append(f"{title} — {len(values)}件")
        if key == "B":
            for rule in sorted(unknown):
                lines.append(f"警告: 未分類の規則 {rule} が {unknown[rule]} 件")
        for finding in values:
            lines.append(f"- {_format_finding(finding)}")
    return "\n".join(lines) + "\n"


def _read_text(path: str | None, *, stdin: Any) -> str:
    return Path(path).read_text(encoding="utf-8") if path else stdin.read()


def main(argv: list[str] | None = None, *, stdin: Any = sys.stdin) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lint-json", metavar="PATH", help="lint --json の出力（省略時は標準入力）")
    parser.add_argument("--ledger-json", metavar="PATH", help="ledger verify --json の出力")
    args = parser.parse_args(argv)

    lint_findings = parse_lint_json(_read_text(args.lint_json, stdin=stdin))
    preamble: list[str] = []
    if args.ledger_json:
        ledger_findings = parse_ledger_json(_read_text(args.ledger_json, stdin=stdin))
        findings, preamble = reconcile_findings(lint_findings, ledger_findings)
    else:
        findings = lint_findings
    sys.stdout.write(render_report(findings, preamble))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
