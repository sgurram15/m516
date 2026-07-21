"""CLI entry point: `python -m m516`.

WP0 only proves the scaffold runs. Pipeline subcommands (scan, report, ...) land in later work
packages per docs/22_BUILD_PLAN.md.
"""

from __future__ import annotations

import argparse
import sys

from m516 import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="m516",
        description="M516 - passive attack-surface + compliance-intelligence engine.",
    )
    parser.add_argument("--version", action="version", version=f"m516 {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
