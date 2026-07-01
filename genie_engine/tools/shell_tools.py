"""Shell 命令执行工具"""

import subprocess
from genie_engine.sandbox.scope import FileScope
from genie_engine.tools.base import Tool, ToolResult


class RunCommandTool(Tool):
    name = "run_command"
    description = "执行 shell 命令（在允许的目录内）"

    async def execute(self, params: dict, scope: FileScope) -> ToolResult:
        cmd = params.get("command", "")
        cwd = params.get("cwd", ".")
        scope.validate_write(cwd)
        try:
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True,
                cwd=cwd, timeout=30,
            )
            return ToolResult(
                success=result.returncode == 0,
                data=result.stdout[:2000] or result.stderr[:2000],
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, data="", error="命令执行超时 (30s)")
        except Exception as exc:
            return ToolResult(success=False, data="", error=str(exc))
