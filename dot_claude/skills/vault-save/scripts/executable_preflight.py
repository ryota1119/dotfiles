#!/usr/bin/env python3
"""vault-save の create と bundle/plan 全体を適用前に検証する。"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import Any


REQUIRED_KEYS = ("type", "title", "status", "created", "updated", "tags")
EXTRA_KEYS = {
    "concept": {"domain", "related", "sources", "assessment", "risk"},
    "entity": {"aliases", "related"},
}
DIR_BY_TYPE = {"concept": "wiki/concepts", "entity": "wiki/entities"}
HUB_PATHS = {"wiki/index.md", "wiki/log.md", "wiki/hot.md"}
COMMON_HUB_PATHS = {"wiki/log.md", "wiki/hot.md"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
OPERATION_ID_RE = re.compile(r"^save-(\d{8}T\d{6})-([a-z0-9]+(?:-[a-z0-9]+)*)$")
WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
FENCE_RE = re.compile(r"^\s*(?:```|~~~)")
KNOWLEDGE_PATH_RE = re.compile(r"^wiki/(?:concepts|sources|entities)/[^/]+\.md$")
YAML_HELPER = r"""
import datetime, json, sys, yaml
def normalize(value):
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): normalize(item) for key, item in value.items()}
    return value
try:
    value = yaml.safe_load(sys.stdin.read())
    if value is None:
        value = {}
    if not isinstance(value, dict):
        raise ValueError("frontmatter が mapping ではありません")
    print(json.dumps(normalize(value), ensure_ascii=False, sort_keys=True))
except Exception as exc:
    print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
    raise SystemExit(1)
"""


@dataclass(frozen=True)
class Check:
    name: str
    ok: bool
    detail: str

    def render(self) -> str:
        marker = "OK" if self.ok else "NG"
        return f"[{marker}] {self.name}: {self.detail}"


@dataclass(frozen=True)
class PageDraft:
    path: str
    frontmatter: dict[str, Any]
    body: str


def _load_json(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"{label} を読めません: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} の JSON を解析できません: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} は object である必要があります")
    return value


def _vaultctl_python() -> Path:
    configured = os.environ.get("VAULTCTL_PYTHON")
    candidate = (
        Path(configured).expanduser()
        if configured
        else Path.home() / ".local/share/uv/tools/vaultctl/bin/python"
    )
    if not candidate.is_file() or not os.access(candidate, os.X_OK):
        raise ValueError(
            "frontmatter 解析用の vaultctl Python を解決できません: "
            f"{candidate}（VAULTCTL_PYTHON で絶対パスを指定できます）"
        )
    return candidate


def _parse_yaml(text: str) -> dict[str, Any]:
    interpreter = _vaultctl_python()
    result = subprocess.run(
        [str(interpreter), "-c", YAML_HELPER],
        input=text,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "詳細なし"
        raise ValueError(f"frontmatter の YAML を解析できません: {detail}")
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("frontmatter 解析器の出力が不正な JSON です") from exc
    if not isinstance(value, dict):
        raise ValueError("frontmatter が mapping ではありません")
    return value


def _parse_page(path: str, content_file: Path) -> PageDraft:
    try:
        text = content_file.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(f"content_file を読めません: {exc}") from exc
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("frontmatter の開始区切り '---' がありません")
    closing = next((index for index in range(1, len(lines)) if lines[index].strip() == "---"), None)
    if closing is None:
        raise ValueError("frontmatter の終了区切り '---' がありません")
    frontmatter = _parse_yaml("\n".join(lines[1:closing]))
    body = "\n".join(lines[closing + 1 :])
    if body.startswith("\n"):
        body = body[1:]
    return PageDraft(path=path, frontmatter=frontmatter, body=body)


def _writes(value: dict[str, Any], label: str) -> list[dict[str, Any]]:
    writes = value.get("writes")
    if not isinstance(writes, list) or any(not isinstance(item, dict) for item in writes):
        raise ValueError(f"{label}.writes は object の配列である必要があります")
    return writes


def _valid_operation_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    match = OPERATION_ID_RE.fullmatch(value)
    if match is None:
        return False
    try:
        datetime.strptime(match.group(1), "%Y%m%dT%H%M%S")
    except ValueError:
        return False
    return True


def _is_safe_relpath(value: Any) -> bool:
    if not isinstance(value, str) or not value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return not path.is_absolute() and ".." not in path.parts and "" not in path.parts


def _is_existing_knowledge_page(vault: Path, relpath: Any) -> bool:
    return (
        isinstance(relpath, str)
        and KNOWLEDGE_PATH_RE.fullmatch(relpath) is not None
        and (vault / relpath).is_file()
    )


def _profile_check(vault: Path, writes: list[dict[str, Any]]) -> tuple[Check, str | None]:
    modes = [item.get("mode") for item in writes]
    paths = [item.get("path") for item in writes]
    creates = [item for item in writes if item.get("mode") == "create"]
    replaces = [item for item in writes if item.get("mode") == "replace"]
    invalid_modes = sorted({str(mode) for mode in modes if mode not in {"create", "replace", "delete"}})
    if invalid_modes:
        return Check("プロファイル", False, f"未知の mode です: {', '.join(invalid_modes)}"), None
    if any(not _is_safe_relpath(path) for path in paths):
        return Check("プロファイル", False, "writes[].path に不正な vault 相対パスがあります"), None
    if len(paths) != len(set(paths)):
        return Check("プロファイル", False, "writes[].path が重複しています"), None

    if len(creates) == 1:
        replace_paths = {item["path"] for item in replaces}
        candidates = sorted(replace_paths - HUB_PATHS)
        expected_shape = (
            len(writes) == 5
            and len(replaces) == 4
            and HUB_PATHS <= replace_paths
            and len(candidates) == 1
            and _is_existing_knowledge_page(vault, candidates[0])
        )
        if expected_shape:
            return Check(
                "プロファイル",
                True,
                "新規作成（create 1 / replace 4: index・被リンク元・log・hot）",
            ), "create"
        actual = ", ".join(sorted(str(path) for path in paths))
        return Check(
            "プロファイル",
            False,
            "新規作成は create 1 と index・既存の被リンク元・log・hot の replace 4が必要です"
            f"（実際: {actual}）",
        ), "create"

    if len(creates) == 0:
        replace_paths = {item["path"] for item in replaces}
        candidates = sorted(replace_paths - COMMON_HUB_PATHS)
        expected_shape = (
            len(writes) == 3
            and len(replaces) == 3
            and COMMON_HUB_PATHS <= replace_paths
            and len(candidates) == 1
            and _is_existing_knowledge_page(vault, candidates[0])
        )
        if expected_shape:
            return Check(
                "プロファイル",
                True,
                "追記・書き換え（replace 3: 対象ページ・log・hot）",
            ), "append"
        actual = ", ".join(sorted(str(path) for path in paths))
        return Check(
            "プロファイル",
            False,
            "追記・書き換えは既存の対象ページ・log・hot の replace 3が必要です"
            f"（実際: {actual}）",
        ), "append"

    return Check("プロファイル", False, f"create は0件または1件が必要です（実際: {len(creates)}件）"), None


SCHEMA_DUMP = r"""
import json
from vaultctl import schema
from vaultctl.graph import WIKILINK_RE
print(json.dumps({
    "REQUIRED_KEYS": list(schema.REQUIRED_KEYS),
    "EXTRA_KEYS": {k: sorted(v) for k, v in schema.EXTRA_KEYS.items()},
    "DIR_BY_TYPE": dict(schema.DIR_BY_TYPE),
    "DATE_RE": schema.DATE_RE.pattern,
    "WIKILINK_RE": WIKILINK_RE.pattern,
}, ensure_ascii=False, sort_keys=True))
"""


def _schema_drift_check() -> Check:
    """このスクリプトが持つ schema 定数を vaultctl 本体と突き合わせる。

    定数を写経しているのは、preflight が vaultctl の import に依存せず単体で
    動くようにするため。ただし写経は本体の変更で黙ってずれる。ずれたまま
    「[OK]」を出すのが最悪なので、vaultctl に届くときは必ず突き合わせる。
    届かないときは検査をスキップせず、その事実を出力に残す。
    """
    try:
        interpreter = _vaultctl_python()
    except ValueError as exc:
        return Check("schema照合", False, f"vaultctl と突き合わせできません: {exc}")
    result = subprocess.run(
        [str(interpreter), "-c", SCHEMA_DUMP], text=True, capture_output=True, check=False
    )
    if result.returncode != 0:
        detail = result.stderr.strip().splitlines()[-1] if result.stderr.strip() else "詳細なし"
        return Check("schema照合", False, f"vaultctl の定数を取得できません: {detail}")
    try:
        actual = json.loads(result.stdout)
    except json.JSONDecodeError:
        return Check("schema照合", False, "vaultctl の定数出力が不正な JSON です")

    diffs: list[str] = []
    if list(REQUIRED_KEYS) != actual["REQUIRED_KEYS"]:
        diffs.append(f"REQUIRED_KEYS: 本体={actual['REQUIRED_KEYS']}")
    for page_type, keys in EXTRA_KEYS.items():
        upstream = actual["EXTRA_KEYS"].get(page_type)
        if upstream is None or sorted(keys) != upstream:
            diffs.append(f"EXTRA_KEYS[{page_type}]: 本体={upstream}")
    for page_type, directory in DIR_BY_TYPE.items():
        upstream = actual["DIR_BY_TYPE"].get(page_type)
        if upstream != directory:
            diffs.append(f"DIR_BY_TYPE[{page_type}]: 本体={upstream!r}")
    if DATE_RE.pattern != actual["DATE_RE"]:
        diffs.append(f"DATE_RE: 本体={actual['DATE_RE']!r}")
    if WIKILINK_RE.pattern != actual["WIKILINK_RE"]:
        diffs.append(f"WIKILINK_RE: 本体={actual['WIKILINK_RE']!r}")

    if diffs:
        return Check(
            "schema照合",
            False,
            "vaultctl 本体とずれています（このスクリプトの定数を追随させること）: " + "; ".join(diffs),
        )
    return Check("schema照合", True, "vaultctl 本体の定数と一致します")


def _content_files_check(writes: list[dict[str, Any]]) -> Check:
    errors: list[str] = []
    for index, item in enumerate(writes):
        mode = item.get("mode")
        value = item.get("content_file")
        if mode == "delete":
            continue
        if not isinstance(value, str) or not Path(value).is_absolute():
            errors.append(f"writes[{index}] {item.get('path')}: 絶対パスではありません（{value!r}）")
        elif not Path(value).is_file():
            errors.append(f"writes[{index}] {item.get('path')}: 実在しません（{value}）")
    if errors:
        return Check("content_file", False, "; ".join(errors))
    return Check("content_file", True, "create/replace の全 content_file が絶対パスで実在します")


def _bundle_alignment(plan: dict[str, Any], bundle: dict[str, Any] | None) -> Check:
    if bundle is None:
        return Check("bundle照合", True, "--bundle 未指定のため plan の確定内容を検証しました")
    fields_match = all(bundle.get(key) == plan.get(key) for key in ("operation_id", "operation_type"))
    try:
        plan_writes = [
            (item.get("path"), item.get("mode"), item.get("content_file"))
            for item in _writes(plan, "plan")
        ]
        bundle_writes = [
            (item.get("path"), item.get("mode"), item.get("content_file"))
            for item in _writes(bundle, "bundle")
        ]
    except ValueError as exc:
        return Check("bundle照合", False, str(exc))
    if fields_match and plan_writes == bundle_writes:
        return Check("bundle照合", True, "operation と writes が plan に一致します")
    return Check("bundle照合", False, "operation または writes が plan と一致しません")


def _empty_headings(body: str) -> list[str]:
    sections: list[list[Any]] = []
    in_fence = False
    for line in body.split("\n"):
        if FENCE_RE.match(line):
            in_fence = not in_fence
            if sections:
                sections[-1][2] += 1
            continue
        if in_fence:
            if line.strip() and sections:
                sections[-1][2] += 1
            continue
        heading = HEADING_RE.match(line)
        if heading:
            sections.append([len(heading.group(1)), heading.group(2).strip(), 0])
        elif line.strip() and sections:
            sections[-1][2] += 1
    empty: list[str] = []
    for index, (level, title, content_count) in enumerate(sections):
        following = sections[index + 1] if index + 1 < len(sections) else None
        if content_count == 0 and not (following is not None and following[0] > level):
            empty.append(str(title))
    return empty


def _blocks(old_body: str, new_body: str) -> list[tuple[str, str, str, int]]:
    """行単位の差分ブロックを (tag, 旧テキスト, 新テキスト, 挿入行番号) で返す。"""
    old_lines = old_body.split("\n")
    new_lines = new_body.split("\n")
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    out: list[tuple[str, str, str, int]] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        out.append((tag, "\n".join(old_lines[i1:i2]), "\n".join(new_lines[j1:j2]), i1))
    return out


def _section_of(body: str, line_index: int) -> str | None:
    """本文の指定行が、どの見出しの配下にあるかを返す。"""
    current: str | None = None
    for index, line in enumerate(body.split("\n")):
        if index >= line_index:
            break
        if HEADING_RE.match(line):
            current = line.strip()
    return current


def _frontmatter_only(old: PageDraft, new: PageDraft, intent: dict[str, Any]) -> list[str]:
    """被リンク元ページ用。本文がバイト単位で不変であることを要求する（計画8.2）。"""
    errors: list[str] = []
    if old.body != new.body:
        errors.append("本文が変わっています（frontmatter-only は本文を1バイトも変えられません）")
    diff = {k for k in set(old.frontmatter) | set(new.frontmatter)
            if old.frontmatter.get(k) != new.frontmatter.get(k)}
    if not diff <= {"updated", "related"}:
        errors.append(f"変更キーが {{updated, related}} を超えています: {sorted(diff)}")
    expected = intent.get("related_add")
    old_related = list(old.frontmatter.get("related") or [])
    new_related = list(new.frontmatter.get("related") or [])
    if new_related[: len(old_related)] != old_related:
        errors.append("related の既存要素が削除または並べ替えられています")
    elif len(new_related) != len(old_related) + 1:
        errors.append(f"related の追加は1件のみ許されます（{len(old_related)} → {len(new_related)}）")
    elif expected is not None and new_related[-1] != expected:
        errors.append(f"related に追加された値が意図と違います: 期待={expected!r} 実際={new_related[-1]!r}")
    return errors


def _insert_only(old: PageDraft, new: PageDraft, intent: dict[str, Any]) -> list[str]:
    """ハブ用。本文への「1箇所の連続した挿入」だけを許す（計画8.3）。"""
    errors: list[str] = []
    diff = {k for k in set(old.frontmatter) | set(new.frontmatter)
            if old.frontmatter.get(k) != new.frontmatter.get(k)}
    if not diff <= {"updated"}:
        errors.append(f"変更キーが {{updated}} を超えています: {sorted(diff)}")
    blocks = _blocks(old.body, new.body)
    bad = [tag for tag, *_ in blocks if tag != "insert"]
    if bad:
        errors.append(f"挿入以外の変更が含まれます: {sorted(set(bad))}")
        return errors
    if len(blocks) != 1:
        errors.append(f"挿入は1箇所のみ許されます（実際: {len(blocks)}箇所）")
        return errors
    _tag, _old_text, inserted, at = blocks[0]
    expected = intent.get("line")
    if expected is not None and inserted != expected:
        errors.append(f"挿入行が意図と違います: 期待={expected!r} 実際={inserted!r}")
    section = intent.get("section")
    if section is not None:
        actual = _section_of(new.body, at)
        if actual != section:
            errors.append(f"挿入位置が意図した節の外です: 期待={section!r} 実際={actual!r}")
    return errors


def _body_edit(old: PageDraft, new: PageDraft, intent: dict[str, Any]) -> list[str]:
    """既存本文の書き換え用（D-T13-9）。宣言した差分と完全一致することを要求する。

    insert-only は差分に replace / delete が現れないことを要求するため、本文の
    書き換えは定義上通らない。ここでは「期待する差分を先に宣言し、それとの
    完全一致を検証する」方式を採る。宣言に無い変更が1つでもあれば失敗させる
    （暴走検出）。
    """
    errors: list[str] = []
    diff = {k for k in set(old.frontmatter) | set(new.frontmatter)
            if old.frontmatter.get(k) != new.frontmatter.get(k)}
    if not diff <= {"updated"}:
        errors.append(f"変更キーが {{updated}} を超えています: {sorted(diff)}")

    declared = intent.get("edits")
    if not isinstance(declared, list) or not declared:
        errors.append("body-edit には edits（[旧テキスト, 新テキスト] の配列）の宣言が必要です")
        return errors
    pairs: list[tuple[str, str]] = []
    for item in declared:
        if not (isinstance(item, list) and len(item) == 2 and all(isinstance(x, str) for x in item)):
            errors.append(f"edits の要素が [旧テキスト, 新テキスト] ではありません: {item!r}")
            return errors
        pairs.append((item[0].rstrip("\n"), item[1].rstrip("\n")))

    actual = [(o, n) for _tag, o, n, _at in _blocks(old.body, new.body)]
    if actual != pairs:
        errors.append(
            f"実際の差分が宣言と一致しません（宣言{len(pairs)}件 / 実際{len(actual)}件）: "
            f"宣言={pairs!r} 実際={actual!r}"
        )
    return errors


REPLACE_MODES = {
    "frontmatter-only": _frontmatter_only,
    "insert-only": _insert_only,
    "body-edit": _body_edit,
}


def _replace_checks(vault: Path, writes: list[dict[str, Any]],
                    intent: dict[str, Any] | None) -> list[Check]:
    replaces = [w for w in writes if w.get("mode") == "replace"]
    if not replaces:
        return [Check("replace検証", True, "replace はありません")]
    if intent is None:
        return [Check(
            "replace検証", False,
            "--intent が無いため replace を検証できません。"
            "各 replace の検証モード（frontmatter-only / insert-only / body-edit）を宣言してください",
        )]

    checks: list[Check] = []
    for item in sorted(replaces, key=lambda w: str(w.get("path"))):
        relpath = str(item.get("path"))
        spec = intent.get(relpath)
        if not isinstance(spec, dict) or spec.get("mode") not in REPLACE_MODES:
            checks.append(Check(f"replace検証 {relpath}", False,
                                f"intent が無いか mode が不正です: {spec!r}"))
            continue
        target = vault / relpath
        if not target.is_file():
            checks.append(Check(f"replace検証 {relpath}", False, "replace 対象が vault に存在しません"))
            continue
        try:
            old = _parse_page(relpath, target)
            new = _parse_page(relpath, Path(str(item.get("content_file"))))
        except ValueError as exc:
            checks.append(Check(f"replace検証 {relpath}", False, str(exc)))
            continue
        errors = REPLACE_MODES[spec["mode"]](old, new, spec)
        checks.append(Check(
            f"replace検証 {relpath}",
            not errors,
            f"{spec['mode']}: " + ("意図どおりの差分です" if not errors else "; ".join(errors)),
        ))
    return checks


def _create_checks(vault: Path, writes: list[dict[str, Any]]) -> list[Check]:
    names = ("create配置", "必須キーと日付", "拡張キー", "wikilink", "空セクション")
    creates = [item for item in writes if item.get("mode") == "create"]
    if not creates:
        detail = "追記・書き換えプロファイルのため対象外"
        return [Check(name, True, detail) for name in names]
    item = creates[0]
    relpath = item.get("path")
    content_file = item.get("content_file")
    if not isinstance(relpath, str) or not isinstance(content_file, str) or not Path(content_file).is_file():
        detail = f"create の path/content_file を読み取れません（path={relpath!r}）"
        return [Check(name, False, detail) for name in names]
    try:
        page = _parse_page(relpath, Path(content_file))
    except ValueError as exc:
        return [Check(name, False, f"{relpath}: {exc}") for name in names]

    page_type = page.frontmatter.get("type")
    expected_dir = DIR_BY_TYPE.get(page_type)
    location_ok = expected_dir is not None and PurePosixPath(relpath).parent.as_posix() == expected_dir
    location = Check(
        "create配置",
        location_ok,
        f"{relpath}: type={page_type!r}, 期待配置={expected_dir or 'concept/entity のみ'}",
    )

    missing = [key for key in REQUIRED_KEYS if key not in page.frontmatter]
    date_errors: list[str] = []
    parsed_dates: dict[str, datetime] = {}
    for key in ("created", "updated"):
        value = page.frontmatter.get(key)
        if not isinstance(value, str) or DATE_RE.fullmatch(value) is None:
            date_errors.append(f"{key}={value!r} は YYYY-MM-DD ではありません")
            continue
        try:
            parsed_dates[key] = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            date_errors.append(f"{key}={value!r} は実在する日付ではありません")
    if {"created", "updated"} <= parsed_dates.keys() and parsed_dates["updated"] < parsed_dates["created"]:
        date_errors.append(
            f"updated={page.frontmatter['updated']} が created={page.frontmatter['created']} より前です"
        )
    required_ok = not missing and not date_errors
    required_detail = []
    if missing:
        required_detail.append(f"不足={','.join(missing)}")
    required_detail.extend(date_errors)
    required = Check(
        "必須キーと日付",
        required_ok,
        f"{relpath}: " + ("6キーと日付順序が正しいです" if required_ok else "; ".join(required_detail)),
    )

    allowed = set(REQUIRED_KEYS) | EXTRA_KEYS.get(str(page_type), set())
    extras = sorted(set(page.frontmatter) - allowed)
    extension = Check(
        "拡張キー",
        page_type in EXTRA_KEYS and not extras,
        f"{relpath}: "
        + ("type の許可範囲内です" if page_type in EXTRA_KEYS and not extras else f"許可されないキー={extras}"),
    )

    existing_slugs = {path.stem for path in sorted((vault / "wiki").rglob("*.md"))}
    targets = sorted({match.group(1).strip() for match in WIKILINK_RE.finditer(page.body)})
    missing_targets = sorted(target for target in targets if target not in existing_slugs)
    links = Check(
        "wikilink",
        not missing_targets,
        f"{relpath}: "
        + (f"本文のリンク{len(targets)}件はすべて実在します" if not missing_targets else f"実在しないリンク={missing_targets}"),
    )

    empty = _empty_headings(page.body)
    headings = Check(
        "空セクション",
        not empty,
        f"{relpath}: " + ("見出しだけの節はありません" if not empty else f"見出しだけの節={empty}"),
    )
    return [location, required, extension, links, headings]


def validate(vault: Path, plan: dict[str, Any], bundle: dict[str, Any] | None = None,
             intent: dict[str, Any] | None = None) -> list[Check]:
    writes = _writes(plan, "plan")
    delete_paths = sorted(str(item.get("path")) for item in writes if item.get("mode") == "delete")
    delete_check = Check(
        "delete禁止",
        not delete_paths,
        "delete は0件です" if not delete_paths else f"delete が含まれます: {', '.join(delete_paths)}",
    )
    operation_type = plan.get("operation_type")
    operation_type_check = Check(
        "operation_type",
        operation_type == "save",
        f"期待='save', 実際={operation_type!r}",
    )
    operation_id = plan.get("operation_id")
    operation_id_check = Check(
        "operation_id",
        _valid_operation_id(operation_id),
        f"期待=save-YYYYMMDDTHHMMSS-slug, 実際={operation_id!r}",
    )
    profile_check, _profile = _profile_check(vault, writes)
    checks = [
        _schema_drift_check(),
        delete_check,
        _content_files_check(writes),
        operation_type_check,
        operation_id_check,
        profile_check,
        _bundle_alignment(plan, bundle),
    ]
    checks.extend(_create_checks(vault, writes))
    checks.extend(_replace_checks(vault, writes, intent))
    return checks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--bundle", type=Path)
    parser.add_argument(
        "--intent", type=Path,
        help="各 replace の検証モードを宣言した JSON。"
             "{path: {mode, line?, section?, related_add?, edits?}}")
    args = parser.parse_args(argv)

    if not args.vault.is_absolute() or not (args.vault / "wiki").is_dir() or not (args.vault / "inbox").is_dir():
        print(f"[NG] 入力: --vault は wiki/ と inbox/ を持つ絶対パスが必要です（実際={args.vault}）")
        return 1
    try:
        plan = _load_json(args.plan, "plan")
        bundle = _load_json(args.bundle, "bundle") if args.bundle else None
        intent = _load_json(args.intent, "intent") if args.intent else None
        checks = validate(args.vault, plan, bundle, intent)
    except ValueError as exc:
        print(f"[NG] 入力: {exc}")
        return 1

    for check in checks:
        print(check.render())
    return 0 if all(check.ok for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
