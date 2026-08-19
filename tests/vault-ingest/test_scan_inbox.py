"""T14-1 の受け入れテスト。

`scan_inbox.py` は読み取り専用なので、実 vault に対しても安全に走らせられる。
ただしテストは合成 vault だけで完結させ、実 vault へのアクセスは monkeypatch で禁止する。
"""

from __future__ import annotations

import builtins
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import unicodedata
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_SCRIPT = ROOT / "scripts" / "make-ingest-fixture.sh"
# chezmoi は `executable_` 接頭辞が無いと実行ビットを展開先に保存しない。
# 接頭辞を外した名前（scan_inbox.py）が ~/.claude/ 側の実際のファイル名になる。
SCAN = ROOT / "dot_claude/skills/vault-ingest/scripts/executable_scan_inbox.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def scan_inbox():
    return _load(SCAN, "scan_inbox")


@pytest.fixture
def vault(tmp_path: Path) -> Path:
    dest = tmp_path / "vault"
    subprocess.run(["bash", str(FIXTURE_SCRIPT), str(dest)], check=True, capture_output=True)
    return dest


def _by_name(queue: dict) -> dict[str, dict]:
    return {i["inbox_path"][len("inbox/"):]: i for i in queue["items"]}


def test_classifies_every_case(scan_inbox, vault: Path) -> None:
    queue = scan_inbox.scan(vault, "")
    assert queue["counts"] == {"ingest": 1, "reconcile": 1, "inconsistent": 3}
    items = _by_name(queue)
    assert items["reconcile-source.md"]["classification"] == "reconcile"
    assert items["fresh-source.md"]["classification"] == "ingest"
    assert items["drifted-source.md"]["classification"] == "inconsistent"
    assert items["orphan-page-source.md"]["classification"] == "inconsistent"
    assert items["unledgered-source.md"]["classification"] == "inconsistent"


def test_inconsistent_reasons_are_distinguished(scan_inbox, vault: Path) -> None:
    """3種類の不整合をひとまとめにせず、原因ごとに書き分ける。"""
    items = _by_name(scan_inbox.scan(vault, ""))
    assert "不整合A" in items["drifted-source.md"]["notes"][0]
    assert "不整合B" in items["orphan-page-source.md"]["notes"][0]
    assert "不整合C" in items["unledgered-source.md"]["notes"][0]


def test_inconsistency_does_not_get_absorbed(scan_inbox, vault: Path) -> None:
    """不整合を自動で吸収しない。ledger を勝手に埋めたり reconcile に倒したりしない。"""
    items = _by_name(scan_inbox.scan(vault, ""))
    unledgered = items["unledgered-source.md"]
    assert unledgered["ledger_source_ids"] == []
    assert unledgered["classification"] != "reconcile"


def test_exit_code_is_nonzero_when_inconsistent(vault: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCAN), "--vault", str(vault)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 1
    assert "inconsistent 3" in result.stdout


def test_exit_code_is_zero_without_inconsistency(scan_inbox, vault: Path) -> None:
    for name in ("drifted-source.md", "orphan-page-source.md", "unledgered-source.md"):
        (vault / "inbox" / name).unlink()
    result = subprocess.run(
        [sys.executable, str(SCAN), "--vault", str(vault)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stdout


def test_nfd_filename_is_not_misclassified(scan_inbox, vault: Path) -> None:
    """macOS の NFD 名でも manifest（NFC キー）と突合できる。

    素朴な集合比較だと処理済みを未処理と誤判定し、同じソースから二重にページを作る。
    """
    nfc_name = "デザインガイド原本.md"
    nfd_name = unicodedata.normalize("NFD", nfc_name)
    assert nfc_name != nfd_name, "この環境では NFC/NFD が同一（テストの前提が崩れている）"

    payload = b"NFD name test\n"
    (vault / "inbox" / nfd_name).write_bytes(payload)
    manifest_path = vault / ".raw/.manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["sources"][f"inbox/{nfc_name}"] = {
        "hash": hashlib.sha256(payload).hexdigest(),
        "pages_created": ["wiki/sources/reconcile-topic-2026-08.md"],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    queue = scan_inbox.scan(vault, "")
    target = next(i for i in queue["items"]
                  if unicodedata.normalize("NFC", i["inbox_path"]).endswith(nfc_name))
    assert target["classification"] == "reconcile", target["notes"]
    # bundle の path には FS から読んだ生の名前を使う。突合だけ NFC で行う。
    assert target["inbox_path"] != target["inbox_path_nfc"]


def test_raw_target_keeps_the_original_filename(scan_inbox, vault: Path) -> None:
    """`.raw/` はリネームしない。ledger の locator との対応が読めなくなるため。"""
    items = _by_name(scan_inbox.scan(vault, ""))
    for name, item in items.items():
        assert item["raw_target"] == f".raw/{name}"


def test_media_type_is_detected_from_extension(scan_inbox, vault: Path) -> None:
    (vault / "inbox" / "paper.pdf").write_bytes(b"%PDF-1.7\n")
    (vault / "inbox" / "notes.txt").write_bytes(b"plain\n")
    items = _by_name(scan_inbox.scan(vault, ""))
    assert items["paper.pdf"]["media_type"] == "pdf"
    assert items["notes.txt"]["media_type"] == "other"
    assert items["fresh-source.md"]["media_type"] == "markdown"


def test_dotfiles_are_skipped(scan_inbox, vault: Path) -> None:
    (vault / "inbox" / ".gitkeep").write_text("", encoding="utf-8")
    (vault / "inbox" / ".DS_Store").write_bytes(b"\x00")
    names = _by_name(scan_inbox.scan(vault, "")).keys()
    assert not any(n.startswith(".") for n in names)


def test_scan_never_writes_to_the_vault(scan_inbox, vault: Path, tmp_path: Path) -> None:
    def manifest() -> list[tuple[str, bytes]]:
        return sorted((str(p.relative_to(vault)), p.read_bytes())
                      for p in vault.rglob("*") if p.is_file())

    before = manifest()
    out = tmp_path / "queue.json"
    subprocess.run([sys.executable, str(SCAN), "--vault", str(vault), "--out", str(out)],
                   capture_output=True, text=True, check=False)
    assert manifest() == before, "scan が vault を書き換えている"
    assert out.is_file()


def test_queue_json_is_deterministic(vault: Path, tmp_path: Path) -> None:
    outs = []
    for i in range(2):
        out = tmp_path / f"q{i}.json"
        subprocess.run([sys.executable, str(SCAN), "--vault", str(vault),
                        "--out", str(out), "--scanned-at", "2026-08-19T00:00:00Z"],
                       capture_output=True, text=True, check=False)
        outs.append(out.read_bytes())
    assert outs[0] == outs[1]


def test_out_must_be_absolute(vault: Path) -> None:
    result = subprocess.run(
        [sys.executable, str(SCAN), "--vault", str(vault), "--out", "relative/queue.json"],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode != 0
    assert "絶対パス" in (result.stdout + result.stderr)


def test_never_opens_the_real_vault(scan_inbox, vault: Path, monkeypatch) -> None:
    real_open = builtins.open
    real_path_open = Path.open

    def guard(path, *a, **kw):
        if "Workspace/exocortex" in os.fspath(path):
            raise AssertionError(f"実 vault を開こうとした: {path}")
        return real_open(path, *a, **kw)

    def guard_path(self, *a, **kw):
        if "Workspace/exocortex" in os.fspath(self):
            raise AssertionError(f"実 vault を開こうとした: {self}")
        return real_path_open(self, *a, **kw)

    monkeypatch.setattr(builtins, "open", guard)
    monkeypatch.setattr(Path, "open", guard_path)
    queue = scan_inbox.scan(vault, "")
    assert queue["counts"]["reconcile"] == 1
