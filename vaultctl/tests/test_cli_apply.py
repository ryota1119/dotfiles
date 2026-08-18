import json
from pathlib import Path

from vaultctl import cli
from test_apply import A_NEW, B_NEW, C_NEW, make_fixture


def _write_plan(plan: dict, tmp_path: Path) -> Path:
    plan_path = tmp_path / "plan.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")
    return plan_path


def test_cli_apply_applies_plan(txn_vault, tmp_path: Path, capsys) -> None:
    plan, _ = make_fixture(txn_vault, tmp_path)
    plan_path = _write_plan(plan, tmp_path)

    code = cli.main(
        [
            "--vault",
            str(txn_vault.root),
            "apply",
            "--plan",
            str(plan_path),
            "--approved-plan-sha256",
            plan["approval_sha256"],
        ]
    )

    assert code == 0
    root = txn_vault.root
    assert (root / "wiki" / "a.md").read_text(encoding="utf-8") == A_NEW
    assert (root / "wiki" / "b.md").read_text(encoding="utf-8") == B_NEW
    assert (root / "wiki" / "c.md").read_text(encoding="utf-8") == C_NEW
    assert "apply-20260817-0001" in capsys.readouterr().out


def test_cli_apply_returns_1_on_approval_mismatch(txn_vault, tmp_path: Path, capsys) -> None:
    plan, _ = make_fixture(txn_vault, tmp_path)
    plan_path = _write_plan(plan, tmp_path)

    code = cli.main(
        [
            "--vault",
            str(txn_vault.root),
            "apply",
            "--plan",
            str(plan_path),
            "--approved-plan-sha256",
            "0" * 64,
        ]
    )

    assert code == 1
    assert not (txn_vault.root / "wiki" / "b.md").exists()
    assert "承認ハッシュ" in capsys.readouterr().err
