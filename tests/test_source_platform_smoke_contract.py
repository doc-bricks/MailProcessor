"""Contract test for the standalone source-platform smoke."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_source_platform_smoke_script_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tests" / "source_platform_smoke.py")],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
    )

    assert result.returncode == 0, result.stderr
    assert "MailProcessor source-platform smoke: PASS" in result.stdout

