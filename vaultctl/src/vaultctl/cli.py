"""vaultctl の CLI 親 parser."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from vaultctl.hashing import canonical_json
from vaultctl.plan import PlanError, build_plan, load_bundle
from vaultctl.vault import VaultError, resolve_vault


def cmd_plan(args: argparse.Namespace) -> int:
    try:
        vault = resolve_vault(args.vault)
        bundle = load_bundle(Path(args.bundle))
        plan = build_plan(vault, bundle)
    except (VaultError, PlanError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(canonical_json(plan) + b"\n")
    print(plan["approval_sha256"])
    return 0


def register_subcommands(sub: argparse._SubParsersAction) -> None:
    """subcommand を登録する。T5 以降がこの関数に追記する。"""
    plan_parser = sub.add_parser("plan", help="変更計画を作る（vault は変更しない）")
    plan_parser.add_argument("--bundle", required=True, metavar="B.json")
    plan_parser.add_argument("--out", required=True, metavar="P.json")
    plan_parser.set_defaults(handler=cmd_plan)
    _add_apply_parser(sub)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vaultctl",
        description="exocortex vault の整合性管理 CLI",
    )
    parser.add_argument(
        "--vault",
        default=None,
        metavar="DIR",
        help="vault のルートディレクトリ（省略時は VAULTCTL_VAULT、次に cwd からの上方探索）",
    )
    sub = parser.add_subparsers(dest="command", metavar="COMMAND")
    register_subcommands(sub)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_usage(sys.stderr)
        return 64
    return int(args.handler(args))


def _add_apply_parser(sub) -> None:
    parser = sub.add_parser("apply", help="承認済みプランを vault に適用する")
    parser.add_argument("--plan", required=True, help="plan.json のパス")
    parser.add_argument(
        "--approved-plan-sha256",
        dest="approved_plan_sha256",
        required=True,
        help="承認済みプランハッシュ",
    )
    parser.set_defaults(handler=_cmd_apply)


def _cmd_apply(args) -> int:
    from vaultctl.apply import ApplyError, apply_plan
    from vaultctl.lock import LockHeld
    from vaultctl.vault import VaultError

    vault = resolve_vault(args.vault)
    plan = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    try:
        journal = apply_plan(vault, plan, args.approved_plan_sha256)
    except (ApplyError, LockHeld, VaultError) as exc:
        print(f"apply 失敗: {exc}", file=sys.stderr)
        return 1
    print(
        f"applied {len(journal['applied'])} files "
        f"(operation_id={journal['operation_id']}, state={journal['state']})"
    )
    return 0
