"""Black_Mamba entrypoint.

Phase 0 surface: --version only. The orchestrator loop is wired up in later phases.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from black_mamba import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="black_mamba",
        description="Autonomous trading agent for Kalshi daily high-temperature markets.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"black_mamba {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    parser.parse_args(argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
