"""vaultctl の CLI 親 parser."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from vaultctl.findings import sort_findings
from vaultctl.frontmatter import collect_pages
from vaultctl.hashing import canonical_json
from vaultctl.ledger import (
    LedgerError,
    check_claims,
    check_page_ledger_consistency,
    check_refresh_due,
    check_review_status,
    stage_ledger_writes,
)
from vaultctl.lint import (
    EXIT_OK,
    EXIT_REVIEW,
    EXIT_USAGE,
    EXIT_VIOLATION,
    format_json,
    format_text,
    run_lint,
)
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
    _add_recover_parser(sub)
    _add_ledger_parser(sub)
    _add_lint_parser(sub)
    _add_graph_parser(sub)


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


def _add_recover_parser(sub) -> None:
    parser = sub.add_parser("recover", help="未完了トランザクションを巻き戻す")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="検出結果を表示するだけで、何も変更しない",
    )
    parser.set_defaults(handler=_cmd_recover)


def _cmd_recover(args) -> int:
    from vaultctl.journal import read_journal
    from vaultctl.recover import find_incomplete, recover_all

    vault = resolve_vault(args.vault)
    if args.dry_run:
        txs = find_incomplete(vault)
        for tx in txs:
            journal = read_journal(tx.journal_path)
            print(
                f"{journal['operation_id']}\t{journal['state']}\t"
                f"{len(journal.get('applied', []))} files"
            )
        print(f"未完了 {len(txs)} 件（--dry-run のため巻き戻していない）")
        return 0

    results = recover_all(vault)
    for result in results:
        print(
            f"{result.operation_id}\t{result.previous_state} -> rolled-back\t"
            f"{len(result.restored)} files"
        )
    print(f"巻き戻し {len(results)} 件")
    return 0


def _cmd_ledger_stage(args) -> int:
    try:
        vault = resolve_vault(args.vault)
    except VaultError as exc:
        print(str(exc), file=sys.stderr)
        return 64

    bundle = json.loads(Path(args.bundle).read_text(encoding="utf-8"))
    sources = (
        json.loads(Path(args.add_source).read_text(encoding="utf-8")) if args.add_source else None
    )
    claims = (
        json.loads(Path(args.add_claim).read_text(encoding="utf-8")) if args.add_claim else None
    )
    if sources is None and claims is None:
        print("--add-source か --add-claim のいずれかを指定する", file=sys.stderr)
        return 64

    staging_dir = Path(args.staging_dir) if args.staging_dir else Path(args.out).parent
    staging_dir.mkdir(parents=True, exist_ok=True)
    try:
        staged = stage_ledger_writes(
            vault.root, bundle, sources=sources, claims=claims, staging_dir=staging_dir
        )
    except LedgerError as exc:
        print(str(exc), file=sys.stderr)
        return 64

    Path(args.out).write_text(
        json.dumps(staged, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(args.out)
    return 0


def _cmd_ledger_verify(args) -> int:
    try:
        vault = resolve_vault(args.vault)
    except VaultError as exc:
        print(str(exc), file=sys.stderr)
        return 64

    if args.today is None:
        today = date.today()
    else:
        try:
            today = date.fromisoformat(args.today)
        except ValueError:
            print(f"--today は YYYY-MM-DD 形式で指定する: {args.today}", file=sys.stderr)
            return 64

    pages, unreadable = collect_pages(vault.root)
    findings = sort_findings(
        [
            *unreadable,
            *check_page_ledger_consistency(vault.root, pages),
            *check_refresh_due(vault.root, today),
            *check_review_status(vault.root),
            *check_claims(vault.root, pages),
        ]
    )

    if args.json_output:
        print(
            json.dumps(
                [
                    {"rule": f.rule, "level": f.level, "path": f.path, "message": f.message}
                    for f in findings
                ],
                ensure_ascii=False,
                indent=2,
            )
        )
    else:
        for finding in findings:
            location = finding.path or "(vault)"
            print(f"[{finding.level}] 規則{finding.rule} {location}: {finding.message}")

    if any(f.level == "violation" for f in findings):
        return 1
    if findings:
        return 2
    return 0


def _add_ledger_parser(sub) -> None:
    """`register_subcommands()` の中から呼ぶ。`--vault` は親 parser 側にある。"""
    parser = sub.add_parser("ledger", help="ledger の追記と整合検証")
    ledger_sub = parser.add_subparsers(dest="ledger_command", metavar="SUBCOMMAND")

    stage = ledger_sub.add_parser("stage", help="bundle に ledger の write を追記する")
    stage.add_argument("--bundle", required=True, metavar="FILE")
    stage.add_argument("--out", required=True, metavar="FILE")
    stage.add_argument("--add-source", default=None, metavar="FILE")
    stage.add_argument("--add-claim", default=None, metavar="FILE")
    stage.add_argument("--staging-dir", default=None, metavar="DIR")
    stage.set_defaults(handler=_cmd_ledger_stage)

    verify = ledger_sub.add_parser("verify", help="ledger 整合性（規則10）を検証する")
    verify.add_argument("--json", action="store_true", dest="json_output")
    verify.add_argument("--today", default=None, metavar="YYYY-MM-DD")
    verify.set_defaults(handler=_cmd_ledger_verify)


def _cmd_lint(args) -> int:
    if args.today is None:
        today = date.today()
    else:
        try:
            today = date.fromisoformat(args.today)
        except ValueError:
            print(f"--today は YYYY-MM-DD 形式で指定する: {args.today}", file=sys.stderr)
            return EXIT_USAGE

    try:
        vault = resolve_vault(args.vault)
    except VaultError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE

    report = run_lint(vault, today=today)
    print(format_json(report) if args.json_output else format_text(report), end="")

    if report.violations:
        return EXIT_VIOLATION
    if report.reviews:
        return EXIT_REVIEW
    return EXIT_OK


def _add_lint_parser(sub) -> None:
    """`register_subcommands()` の中から呼ぶ。`--vault` は親 parser 側にある。"""
    parser = sub.add_parser("lint", help="vault を検査する")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON で出力する")
    parser.add_argument("--today", default=None, metavar="YYYY-MM-DD", help="基準日（既定は今日）")
    parser.set_defaults(handler=_cmd_lint)


def _cmd_graph(args) -> int:
    from vaultctl.metrics import build_graph_report, format_json, format_text

    try:
        vault = resolve_vault(args.vault)
    except VaultError as exc:
        print(str(exc), file=sys.stderr)
        return EXIT_USAGE

    report = build_graph_report(vault)
    print(format_json(report) if args.json_output else format_text(report), end="")
    return EXIT_OK


def _add_graph_parser(sub) -> None:
    """`register_subcommands()` の中から呼ぶ。`--vault` は親 parser 側にある。"""
    parser = sub.add_parser("graph", help="wikilink グラフの指標を報告する（検査ではない）")
    parser.add_argument("--json", action="store_true", dest="json_output", help="JSON で出力する")
    parser.set_defaults(handler=_cmd_graph)
