"""wikilink グラフの構築と検査（T8、lint 規則4・5・7）。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from .findings import Finding, sort_findings
from .frontmatter import Page
from .schema import is_meta_page

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
HUB_RELPATHS = ("wiki/index.md", "wiki/hot.md", "wiki/log.md",
                "wiki/dashboard.md", "wiki/overview.md")
INDEX_RELPATH = "wiki/index.md"
LINK_FIELDS = ("related", "sources")


@dataclass(frozen=True)
class Graph:
    pages: dict[str, Page]
    by_relpath: dict[str, Page]
    targets: dict[str, list[str]]
    backlinks: dict[str, set[str]]


def extract_links(body: str) -> list[str]:
    """本文中の [[...]] をリンク先 slug の列にする（見出し・表示名は落とす）。"""
    return [m.group(1).strip() for m in WIKILINK_RE.finditer(body)]


def _frontmatter_links(page: Page) -> list[str]:
    out: list[str] = []
    for field in LINK_FIELDS:
        value = page.frontmatter.get(field)
        if isinstance(value, str):
            out.extend(extract_links(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    out.extend(extract_links(item))
    return out


def build_graph(pages: Iterable[Page]) -> Graph:
    by_slug: dict[str, Page] = {}
    by_relpath: dict[str, Page] = {}
    targets: dict[str, list[str]] = {}
    backlinks: dict[str, set[str]] = {}

    for page in pages:
        by_relpath[page.relpath] = page
        by_slug.setdefault(page.slug, page)
        backlinks.setdefault(page.slug, set())
        ordered: list[str] = []
        for slug in extract_links(page.body) + _frontmatter_links(page):
            if slug not in ordered:
                ordered.append(slug)
        targets[page.relpath] = ordered

    for relpath, slugs in targets.items():
        for slug in slugs:
            backlinks.setdefault(slug, set()).add(relpath)

    return Graph(pages=by_slug, by_relpath=by_relpath, targets=targets, backlinks=backlinks)


def check_broken_links(graph: Graph) -> list[Finding]:
    """規則4: 解決先の無い wikilink。"""
    found: list[Finding] = []
    for relpath, slugs in graph.targets.items():
        for slug in slugs:
            if slug not in graph.pages:
                found.append(Finding(
                    rule="4", level="violation", path=relpath,
                    message=f"リンク先が存在しません: [[{slug}]]"))
    return sort_findings(found)


def check_orphans(graph: Graph) -> list[Finding]:
    """規則5: どこからもリンクされていない知識ページ。ハブからのリンクは数えない。"""
    found: list[Finding] = []
    for relpath, page in graph.by_relpath.items():
        if is_meta_page(relpath):
            continue
        incoming = {
            src for src in graph.backlinks.get(page.slug, set())
            if src != relpath and src not in HUB_RELPATHS
        }
        if not incoming:
            found.append(Finding(
                rule="5", level="violation", path=relpath,
                message="どこからもリンクされていません（ハブページからのリンクは除く）"))
    return sort_findings(found)


def check_index(graph: Graph) -> list[Finding]:
    """規則7: wiki/index.md の wikilink 集合と知識ページ集合を双方向に照合する。"""
    if INDEX_RELPATH not in graph.by_relpath:
        return [Finding(rule="7", level="violation", path=INDEX_RELPATH,
                        message="wiki/index.md が存在しません")]

    listed = set(graph.targets.get(INDEX_RELPATH, []))
    found: list[Finding] = []

    for relpath, page in graph.by_relpath.items():
        if is_meta_page(relpath):
            continue
        if page.slug not in listed:
            found.append(Finding(rule="7", level="violation", path=relpath,
                                 message="wiki/index.md に載っていません"))

    for slug in listed - set(graph.pages):
        found.append(Finding(
            rule="7", level="violation", path=INDEX_RELPATH,
            message=f"wiki/index.md に載っているページが存在しません: [[{slug}]]"))

    return sort_findings(found)
