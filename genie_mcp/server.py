"""Genie MCP Server — JSON-RPC 2.0 over stdio

Cursor 配置:
{
  "mcpServers": {
    "genie": {
      "command": "python",
      "args": ["-m", "genie_mcp.server"]
    }
  }
}
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Any

# ── MCP Protocol constants ──
JSONRPC = "2.0"
SERVER_NAME = "genie-mcp"
SERVER_VERSION = "0.1.0"

# ── Tool definitions ──
TOOLS = [
    {
        "name": "genie_run",
        "description": "Run a Genie RolePack to generate a complete project from a one-sentence goal. "
                       "Like having a team of AI engineers build your project autonomously.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pack": {
                    "type": "string",
                    "description": "RolePack name: 'code' for software projects, 'pack' to create new RolePacks",
                    "default": "code",
                },
                "goal": {
                    "type": "string",
                    "description": "Your one-sentence project goal, e.g. 'Build a todo app with FastAPI backend'",
                },
                "model": {
                    "type": "string",
                    "description": "AI model: 'mock' (instant, demo), 'deepseek' (needs DEEPSEEK_API_KEY), 'gpt4'",
                    "default": "mock",
                },
            },
            "required": ["goal"],
        },
    },
    {
        "name": "genie_list_packs",
        "description": "List all installed and available Genie RolePacks",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "genie_hub_search",
        "description": "Search the Genie RolePack marketplace",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search keyword",
                    "default": "",
                },
            },
        },
    },
]


class MCPServer:
    """Minimal MCP stdio server"""

    def __init__(self):
        self._initialized = False
        self._tools = {t["name"]: t for t in TOOLS}

    async def run(self) -> None:
        """Main loop: read JSON-RPC from stdin, write responses to stdout"""
        loop = asyncio.get_event_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        writer_transport, writer_protocol = await loop.connect_write_pipe(
            asyncio.streams.FlowControlMixin, sys.stdout.buffer
        )
        writer = asyncio.StreamWriter(writer_transport, writer_protocol, reader, loop)

        buffer = ""
        while True:
            try:
                chunk = await reader.read(65536)
                if not chunk:
                    break
                buffer += chunk.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if line.strip():
                        response = self._handle(line.strip())
                        if response:
                            resp_bytes = (json.dumps(response, ensure_ascii=False) + "\n").encode("utf-8")
                            writer.write(resp_bytes)
                            await writer.drain()
            except Exception:
                break

    def _handle(self, raw: str) -> dict[str, Any] | None:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            return self._error(None, -32700, "Parse error")

        msg_id = msg.get("id")
        method = msg.get("method", "")

        # Initialize
        if method == "initialize":
            self._initialized = True
            return self._response(msg_id, {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                "capabilities": {"tools": {}},
            })

        if method == "notifications/initialized":
            return None  # No response for notifications

        # Tools
        if method == "tools/list":
            return self._response(msg_id, {"tools": TOOLS})

        if method == "tools/call":
            params = msg.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = self._call_tool(tool_name, arguments)
            return self._response(msg_id, {
                "content": [{"type": "text", "text": result}]
            })

        if method == "ping":
            return self._response(msg_id, {})

        if method == "shutdown":
            return self._response(msg_id, {})

        return self._error(msg_id, -32601, f"Method not found: {method}")

    def _call_tool(self, name: str, args: dict[str, Any]) -> str:
        try:
            if name == "genie_list_packs":
                return self._list_packs()
            elif name == "genie_hub_search":
                return self._hub_search(args.get("query", ""))
            elif name == "genie_run":
                return asyncio.get_event_loop().run_until_complete(
                    self._run_pack(args)
                )
            else:
                return f"Unknown tool: {name}"
        except Exception as exc:
            return f"Error: {exc}"

    async def _run_pack(self, args: dict[str, Any]) -> str:
        """Run a RolePack and return summary"""
        pack_name = args.get("pack", "code")
        goal = args.get("goal", "")
        model = args.get("model", "mock")

        if not goal:
            return "Error: 'goal' is required"

        from genie_cli.main import _find_pack
        from genie_engine.core.engine import GenieEngine

        pack_path = _find_pack(pack_name)
        if not pack_path:
            return f"Error: RolePack '{pack_name}' not found. Available: code, pack"

        engine = GenieEngine(pack_path)
        result = await engine.execute(goal, model=model)

        lines = [
            f"✅ Genie Run Complete",
            f"Status: {result.status}",
            f"Duration: {result.total_duration_seconds:.1f}s",
            f"Model: {model}",
            f"Stages: {len(result.stages)}",
        ]
        for s in result.stages:
            icon = "✅" if s.status == "completed" else "❌"
            roles_str = ", ".join(r.role_name for r in s.roles if hasattr(r, 'role_name'))
            lines.append(f"  {icon} [{s.stage_id}] {s.status} — {roles_str}")
        if result.warnings:
            lines.append(f"Warnings: {len(result.warnings)}")
        lines.append(f"Output: {result.output_dir}")
        return "\n".join(lines)

    def _list_packs(self) -> str:
        from genie_hub import LocalRegistry
        registry = LocalRegistry()
        packs = registry.list_all()
        if not packs:
            return "No RolePacks installed"
        lines = [f"Installed RolePacks ({len(packs)}):"]
        for p in packs:
            lines.append(f"  {p.icon} {p.name} v{p.version} — {p.description}")
        return "\n".join(lines)

    def _hub_search(self, query: str) -> str:
        from genie_hub import LocalRegistry, Marketplace
        registry = LocalRegistry()
        marketplace = Marketplace(registry)
        results = marketplace.search(query) if query else marketplace.list_community()
        if not results:
            return "No matching RolePacks found"
        lines = [f"Search results ({len(results)}):"]
        for p in results:
            installed = "[installed]" if registry.is_installed(p.name) else "[available]"
            lines.append(f"  {p.icon} {installed} {p.name} v{p.version} — {p.description}")
        return "\n".join(lines)

    @staticmethod
    def _response(msg_id: Any, result: Any) -> dict[str, Any]:
        return {"jsonrpc": JSONRPC, "id": msg_id, "result": result}

    @staticmethod
    def _error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": JSONRPC, "id": msg_id, "error": {"code": code, "message": message}}


def main():
    server = MCPServer()
    asyncio.run(server.run())


if __name__ == "__main__":
    main()