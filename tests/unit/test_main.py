"""--version smoke test (Phase 0 DoD)."""

from __future__ import annotations

import subprocess
import sys

import pytest

from black_mamba import __version__
from black_mamba.main import main


def test_version_constant_format() -> None:
    parts = __version__.split(".")
    assert len(parts) == 3
    assert all(p.isdigit() for p in parts)


def test_main_version_exits_clean() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0


def test_main_no_args_exits_clean() -> None:
    assert main([]) == 0


def test_module_invocation_prints_version() -> None:
    """Black-box: `python -m black_mamba.main --version` runs and prints version."""
    result = subprocess.run(
        [sys.executable, "-m", "black_mamba.main", "--version"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert __version__ in (result.stdout + result.stderr)
