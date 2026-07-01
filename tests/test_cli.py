"""测试 CLI 命令"""

import subprocess
import sys
from pathlib import Path


class TestCLI:
    def test_validate_valid_pack(self):
        pack = Path(__file__).parent.parent / "rolepacks" / "code.rolepack.yaml"
        result = subprocess.run(
            [sys.executable, "-m", "genie_cli.main", "validate", str(pack)],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        assert "通过" in result.stdout

    def test_validate_invalid_pack(self):
        result = subprocess.run(
            [sys.executable, "-m", "genie_cli.main", "validate", "nonexistent.yaml"],
            capture_output=True, text=True,
        )
        assert result.returncode == 1

    def test_run_no_args(self):
        result = subprocess.run(
            [sys.executable, "-m", "genie_cli.main", "run"],
            capture_output=True, text=True,
        )
        assert "用法" in result.stdout
