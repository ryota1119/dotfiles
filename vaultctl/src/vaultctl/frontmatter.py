"""frontmatter の分解と生成（T7）。

読み込み時、YAML が `datetime.date` へ落とした値はすべて ISO 文字列に正規化する。
以降の層（schema / graph / maturity / ledger）は frontmatter の値が
str / int / float / bool / None / list のいずれかであることを前提にしてよい。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Iterator

import yaml


class FrontmatterError(Exception):
    """frontmatter の構造が壊れている場合に送出する。"""


KEY_ORDER = ("type", "title", "status", "created", "updated", "tags",
             "domain", "aliases", "related", "sources", "assessment", "risk", "claim_ids")

DELIMITER = "---"

_PLAIN_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./+-]*$")
_RESERVED_PLAIN = {"true", "false", "null", "yes", "no", "on", "off", "~"}


@dataclass(frozen=True)
class Page:
    relpath: str
    slug: str
    frontmatter: dict
    body: str


def split_frontmatter(text: str) -> tuple[str, str]:
    """先頭の YAML frontmatter と本文に分ける。区切りが無ければ FrontmatterError。"""
    lines = text.split("\n")
    if not lines or lines[0].strip() != DELIMITER:
        raise FrontmatterError("frontmatter の開始区切り '---' がありません")
    for i in range(1, len(lines)):
        if lines[i].strip() == DELIMITER:
            fm_text = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1:])
            if body.startswith("\n"):
                body = body[1:]
            return fm_text, body
    raise FrontmatterError("frontmatter の終了区切り '---' がありません")


def _normalize(value):
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if isinstance(value, dict):
        return {k: _normalize(v) for k, v in value.items()}
    return value


def parse_page(root: Path, path: Path) -> Page:
    text = path.read_text(encoding="utf-8")
    fm_text, body = split_frontmatter(text)
    try:
        loaded = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        raise FrontmatterError(f"frontmatter の YAML を解析できません: {exc}") from exc
    if loaded is None:
        loaded = {}
    if not isinstance(loaded, dict):
        raise FrontmatterError("frontmatter がマッピングではありません")
    return Page(
        relpath=path.relative_to(root).as_posix(),
        slug=path.stem,
        frontmatter=_normalize(loaded),
        body=body,
    )


def iter_pages(root: Path) -> Iterator[Page]:
    """wiki/**/*.md を relpath 昇順で返す。"""
    paths = sorted((root / "wiki").rglob("*.md"),
                   key=lambda p: p.relative_to(root).as_posix())
    for path in paths:
        yield parse_page(root, path)


def _scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if _PLAIN_RE.match(value) and value.lower() not in _RESERVED_PLAIN:
            return value
        return json.dumps(value, ensure_ascii=False)
    raise FrontmatterError(
        f"frontmatter に未対応の型が含まれています: {type(value).__name__}")


def dump_frontmatter(fm: dict) -> str:
    """KEY_ORDER 順に並べて YAML 文字列にする。KEY_ORDER 外のキーは末尾に名前順で残す。"""
    keys = [k for k in KEY_ORDER if k in fm]
    keys += sorted(k for k in fm if k not in KEY_ORDER)
    out: list[str] = []
    for key in keys:
        value = fm[key]
        if isinstance(value, list):
            if not value:
                out.append(f"{key}: []")
                continue
            out.append(f"{key}:")
            out.extend(f"  - {_scalar(item)}" for item in value)
        else:
            out.append(f"{key}: {_scalar(value)}")
    return "".join(line + "\n" for line in out)


def render_page(fm: dict, body: str) -> str:
    return "---\n" + dump_frontmatter(fm) + "---\n\n" + body
