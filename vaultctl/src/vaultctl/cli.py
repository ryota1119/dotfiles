"""vaultctl の CLI 親 parser."""

from __future__ import annotations

import argparse
import sys


def register_subcommands(sub: argparse._SubParsersAction) -> None:
    """subcommand を登録する。T2 以降がこの関数に追記する。"""
    return None


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
