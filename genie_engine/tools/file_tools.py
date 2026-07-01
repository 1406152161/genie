"""文件读写工具"""

from pathlib import Path

from genie_engine.sandbox.scope import FileScope
from genie_engine.tools.base import Tool, ToolResult


class FileReadTool(Tool):
    name = "file_read"
    description = "读取文件内容"

    async def execute(self, params: dict, scope: FileScope) -> ToolResult:
        path = Path(params.get("path", ""))
        scope.validate_read(path)
        try:
            content = path.read_text(encoding="utf-8")
            return ToolResult(success=True, data=content[:5000])
        except Exception as exc:
            return ToolResult(success=False, data="", error=str(exc))


class FileWriteTool(Tool):
    name = "file_write"
    description = "写入文件内容"

    async def execute(self, params: dict, scope: FileScope) -> ToolResult:
        path = Path(params.get("path", ""))
        content = params.get("content", "")
        scope.validate_write(path)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return ToolResult(success=True, data=f"写入成功: {path}")
        except Exception as exc:
            return ToolResult(success=False, data="", error=str(exc))
