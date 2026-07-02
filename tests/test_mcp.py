"""Test MCP Server protocol"""

import json
import pytest

from genie_mcp.server import MCPServer


class TestMCPServer:
    def test_initialize(self):
        server = MCPServer()
        msg = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        resp = server._handle(msg)
        assert resp is not None
        assert resp["id"] == 1
        assert "protocolVersion" in resp["result"]
        assert resp["result"]["serverInfo"]["name"] == "genie-mcp"

    def test_tools_list(self):
        server = MCPServer()
        server._initialized = True
        msg = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        resp = server._handle(msg)
        assert resp is not None
        tools = resp["result"]["tools"]
        tool_names = {t["name"] for t in tools}
        assert "genie_run" in tool_names
        assert "genie_list_packs" in tool_names
        assert "genie_hub_search" in tool_names

    def test_ping(self):
        server = MCPServer()
        msg = json.dumps({"jsonrpc": "2.0", "id": 3, "method": "ping"})
        resp = server._handle(msg)
        assert resp["id"] == 3
        assert resp["result"] == {}

    def test_unknown_method(self):
        server = MCPServer()
        msg = json.dumps({"jsonrpc": "2.0", "id": 4, "method": "nonexistent"})
        resp = server._handle(msg)
        assert "error" in resp
        assert resp["error"]["code"] == -32601

    def test_notification_no_response(self):
        server = MCPServer()
        msg = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"})
        resp = server._handle(msg)
        assert resp is None

    def test_list_packs(self):
        server = MCPServer()
        result = server._call_tool("genie_list_packs", {})
        assert "Genie Code" in result or "RolePack" in result

    def test_hub_search(self):
        server = MCPServer()
        result = server._call_tool("genie_hub_search", {"query": "code"})
        assert "Genie Code" in result or "RolePack" in result.lower()

    def test_run_requires_goal(self):
        server = MCPServer()
        result = server._call_tool("genie_run", {"pack": "code"})
        assert "Error" in result