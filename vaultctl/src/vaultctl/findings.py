"""lint の指摘（Finding）とその整列（T7）。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    """lint が返す1件の指摘。

    rule:    "1"〜"8"、"9-a"、"9-b"、"10-a"〜"10-d"
    level:   "violation"（規則1〜8）| "review"（規則9〜10）
    path:    vault 相対パス。vault 全体に関わるものは ""
    message: 日本語1行
    """

    rule: str
    level: str
    path: str
    message: str


def sort_findings(findings: Iterable[Finding]) -> list[Finding]:
    """(rule, path, message) の昇順に並べた新しいリストを返す。"""
    return sorted(findings, key=lambda f: (f.rule, f.path, f.message))
