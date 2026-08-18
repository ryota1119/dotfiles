"""グラフ指標レポート（T17 `vaultctl graph`）のテスト。"""

import json
from pathlib import Path

from vaultctl import cli
from vaultctl.lint import EXIT_OK, EXIT_USAGE
from vaultctl.metrics import GRAPH_REPORT_SCHEMA, build_graph_report, format_json, format_text
from vaultctl.vault import resolve_vault


def page_text(fm_lines, body):
    return "---\n" + "\n".join(fm_lines) + "\n---\n\n" + body


def base_fm(type_, title, *, status="developing", created="2026-08-01", updated="2026-08-10"):
    return [
        f"type: {type_}",
        f"title: {title}",
        f"status: {status}",
        f"created: {created}",
        f"updated: {updated}",
        "tags: []",
    ]


def write(root: Path, relpath: str, text: str) -> None:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_vault(tmp_path: Path, name: str = "v") -> Path:
    root = tmp_path / name
    (root / "inbox").mkdir(parents=True)
    (root / "wiki").mkdir(parents=True, exist_ok=True)
    return root


def report(tmp_path, root: Path, monkeypatch):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.delenv("VAULTCTL_VAULT", raising=False)
    return build_graph_report(resolve_vault(str(root)))


def by_path(rep):
    return {p.path: p for p in rep.pages}


def test_hub_links_are_not_counted_in_in_degree(tmp_path, monkeypatch):
    root = make_vault(tmp_path)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n"))
    write(root, "wiki/hot.md", page_text(base_fm("meta", "hot"), "- [[a]]\n"))
    write(root, "wiki/concepts/a.md", page_text(base_fm("concept", "A"), "本文\n"))
    write(root, "wiki/concepts/b.md", page_text(base_fm("concept", "B"), "[[a]]\n"))

    pages = by_path(report(tmp_path, root, monkeypatch))

    assert pages["wiki/concepts/a.md"].in_degree == 1
    assert pages["wiki/concepts/a.md"].backlinks == ["wiki/concepts/b.md"]


def test_self_links_are_not_counted_in_in_degree(tmp_path, monkeypatch):
    root = make_vault(tmp_path)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n"))
    write(root, "wiki/concepts/a.md", page_text(base_fm("concept", "A"), "[[a]] を参照\n"))

    pages = by_path(report(tmp_path, root, monkeypatch))

    assert pages["wiki/concepts/a.md"].in_degree == 0
    assert pages["wiki/concepts/a.md"].backlinks == []


def test_self_links_are_not_counted_in_out_degree(tmp_path, monkeypatch):
    root = make_vault(tmp_path)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n- [[b]]\n"))
    write(root, "wiki/concepts/a.md", page_text(base_fm("concept", "A"), "[[a]] と [[b]]\n"))
    write(root, "wiki/concepts/b.md", page_text(base_fm("concept", "B"), "本文\n"))

    pages = by_path(report(tmp_path, root, monkeypatch))

    assert pages["wiki/concepts/a.md"].out_degree == 1
    assert pages["wiki/concepts/a.md"].links == ["wiki/concepts/b.md"]


def test_broken_links_are_not_counted_in_out_degree(tmp_path, monkeypatch):
    root = make_vault(tmp_path)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n- [[b]]\n"))
    write(root, "wiki/concepts/a.md", page_text(base_fm("concept", "A"), "[[b]] と [[nope]]\n"))
    write(root, "wiki/concepts/b.md", page_text(base_fm("concept", "B"), "本文\n"))

    pages = by_path(report(tmp_path, root, monkeypatch))

    assert pages["wiki/concepts/a.md"].out_degree == 1
    assert pages["wiki/concepts/a.md"].links == ["wiki/concepts/b.md"]


def test_body_bytes_excludes_frontmatter(tmp_path, monkeypatch):
    root = make_vault(tmp_path)
    body = "本文です。\n"
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n"))
    write(root, "wiki/concepts/a.md", page_text(base_fm("concept", "A"), body))

    pages = by_path(report(tmp_path, root, monkeypatch))

    assert pages["wiki/concepts/a.md"].body_bytes == len(body.encode("utf-8"))


def test_pages_are_sorted_by_in_out_bytes_then_path(tmp_path, monkeypatch):
    root = make_vault(tmp_path)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n"))
    # in_degree=1 / out_degree=0 / body_bytes 同値の 2 枚は path 昇順で決まる。
    write(root, "wiki/concepts/x.md", page_text(base_fm("concept", "X"), "[[t1]]\n"))
    write(root, "wiki/concepts/y.md", page_text(base_fm("concept", "Y"), "[[t2]]\n"))
    write(root, "wiki/concepts/t1.md", page_text(base_fm("concept", "T1"), "ab\n"))
    write(root, "wiki/concepts/t2.md", page_text(base_fm("concept", "T2"), "ab\n"))

    rep = report(tmp_path, root, monkeypatch)
    order = [(p.in_degree, p.out_degree, p.body_bytes, p.path) for p in rep.pages]

    assert order == sorted(order, key=lambda t: (-t[0], -t[1], -t[2], t[3]))
    assert [p.path for p in rep.pages][:2] == ["wiki/concepts/t1.md", "wiki/concepts/t2.md"]


def test_unreadable_pages_are_listed_and_excluded_from_pages(tmp_path, monkeypatch):
    root = make_vault(tmp_path)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n"))
    write(root, "wiki/concepts/a.md", page_text(base_fm("concept", "A"), "本文\n"))
    write(root, "wiki/concepts/broken.md", "frontmatter がありません\n")

    rep = report(tmp_path, root, monkeypatch)

    assert rep.unreadable == ["wiki/concepts/broken.md"]
    assert "wiki/concepts/broken.md" not in by_path(rep)


def test_frontmatter_values_are_passed_through_and_missing_keys_are_null(tmp_path, monkeypatch):
    root = make_vault(tmp_path)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n"))
    write(
        root,
        "wiki/concepts/a.md",
        page_text(["title: A", "created: 2026-08-01"], "本文\n"),
    )

    page = by_path(report(tmp_path, root, monkeypatch))["wiki/concepts/a.md"]

    assert (page.type, page.status, page.updated) == (None, None, None)
    assert page.slug == "a"


def test_format_json_matches_schema(tmp_path, monkeypatch):
    root = make_vault(tmp_path)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n"))
    write(root, "wiki/concepts/a.md", page_text(base_fm("concept", "A"), "[[b]]\n"))
    write(root, "wiki/concepts/b.md", page_text(base_fm("concept", "B"), "本文\n"))

    rep = report(tmp_path, root, monkeypatch)
    payload = json.loads(format_json(rep))

    assert payload["schema"] == GRAPH_REPORT_SCHEMA
    assert payload["vault_id"] == rep.vault_id
    assert payload["unreadable"] == []
    entry = next(p for p in payload["pages"] if p["path"] == "wiki/concepts/a.md")
    assert set(entry) == {
        "path", "slug", "type", "status", "updated",
        "in_degree", "out_degree", "body_bytes", "backlinks", "links",
    }
    assert entry["links"] == ["wiki/concepts/b.md"]


def test_format_text_has_five_columns(tmp_path, monkeypatch):
    root = make_vault(tmp_path)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n"))
    write(root, "wiki/concepts/a.md", page_text(base_fm("concept", "A"), "本文\n"))

    text = format_text(report(tmp_path, root, monkeypatch))
    lines = text.splitlines()

    assert lines[1].split("\t") == ["in", "out", "bytes", "updated", "path"]
    assert any(line.endswith("wiki/concepts/a.md") for line in lines[2:])


def test_cli_graph_json_returns_0(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    root = make_vault(tmp_path)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n"))
    write(root, "wiki/concepts/a.md", page_text(base_fm("concept", "A"), "本文\n"))

    code = cli.main(["--vault", str(root), "graph", "--json"])

    out = capsys.readouterr().out
    assert code == EXIT_OK, out
    assert json.loads(out)["schema"] == GRAPH_REPORT_SCHEMA


def test_cli_graph_text_returns_0(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    root = make_vault(tmp_path)
    write(root, "wiki/index.md", page_text(base_fm("meta", "索引"), "- [[a]]\n"))

    code = cli.main(["--vault", str(root), "graph"])

    out = capsys.readouterr().out
    assert code == EXIT_OK, out
    assert "wiki/index.md" in out


def test_cli_graph_returns_64_for_unknown_vault(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.delenv("VAULTCTL_VAULT", raising=False)

    code = cli.main(["--vault", str(tmp_path / "missing"), "graph"])

    assert code == EXIT_USAGE
    assert capsys.readouterr().err.strip() != ""
