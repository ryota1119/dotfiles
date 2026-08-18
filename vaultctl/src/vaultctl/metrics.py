"""グラフ指標の集計と出力形式（T17、`vaultctl graph`）。

検査ではなく報告なので Finding は作らず、終了コードも常に 0 になる。
リンク抽出とグラフ構築は `graph.py` の `build_graph` をそのまま使い、
`in_degree` の除外規則は規則5（孤立ページ）と同じ `incoming_relpaths` を使う。
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from .frontmatter import collect_pages
from .graph import build_graph, incoming_relpaths, resolved_relpaths
from .vault import Vault

GRAPH_REPORT_SCHEMA = "vaultctl.graph-report.v1"


@dataclass(frozen=True)
class PageMetrics:
    path: str
    slug: str
    type: str | None
    status: str | None
    updated: str | None
    in_degree: int
    out_degree: int
    body_bytes: int
    backlinks: list[str]
    links: list[str]

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "slug": self.slug,
            "type": self.type,
            "status": self.status,
            "updated": self.updated,
            "in_degree": self.in_degree,
            "out_degree": self.out_degree,
            "body_bytes": self.body_bytes,
            "backlinks": list(self.backlinks),
            "links": list(self.links),
        }


@dataclass(frozen=True)
class GraphReport:
    vault_id: str
    unreadable: list[str]
    pages: list[PageMetrics]


def _sort_key(page: PageMetrics) -> tuple:
    return (-page.in_degree, -page.out_degree, -page.body_bytes, page.path)


def build_graph_report(vault: Vault) -> GraphReport:
    """vault 全ページのグラフ指標を集計する。並び順は固定（8.3 の順序）。"""
    pages, unreadable = collect_pages(vault.root)
    graph = build_graph(pages)

    metrics: list[PageMetrics] = []
    for page in pages:
        backlinks = sorted(incoming_relpaths(graph, page))
        links = sorted(resolved_relpaths(graph, page))
        fm = page.frontmatter
        metrics.append(PageMetrics(
            path=page.relpath,
            slug=page.slug,
            type=fm.get("type"),
            status=fm.get("status"),
            updated=fm.get("updated"),
            in_degree=len(backlinks),
            out_degree=len(links),
            body_bytes=len(page.body.encode("utf-8")),
            backlinks=backlinks,
            links=links,
        ))

    return GraphReport(
        vault_id=vault.vault_id,
        unreadable=sorted(f.path for f in unreadable if f.path),
        pages=sorted(metrics, key=_sort_key),
    )


def format_text(report: GraphReport) -> str:
    """人間が読む簡潔な表。1行目は件数の要約、2行目は列名。"""
    lines = [
        f"pages {len(report.pages)} 件 / 読めないページ {len(report.unreadable)} 件",
        "\t".join(("in", "out", "bytes", "updated", "path")),
    ]
    for page in report.pages:
        lines.append("\t".join((
            str(page.in_degree),
            str(page.out_degree),
            str(page.body_bytes),
            page.updated or "-",
            page.path,
        )))
    for path in report.unreadable:
        lines.append(f"読めません\t{path}")
    return "\n".join(lines) + "\n"


def format_json(report: GraphReport) -> str:
    """機械可読な JSON。lint と同じく indent=2 の人間可読形式にする。"""
    payload = {
        "schema": GRAPH_REPORT_SCHEMA,
        "vault_id": report.vault_id,
        "unreadable": list(report.unreadable),
        "pages": [page.to_dict() for page in report.pages],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
