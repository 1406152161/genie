# Genie MCP Server — Cursor 集成

让 Cursor IDE 直接调用 Genie Engine，一句话生成完整项目。

## 1. 安装

```bash
pip install -e ".[dev]"
```

## 2. 配置 Cursor

打开 Cursor → Settings → MCP → 添加：

```json
{
  "mcpServers": {
    "genie": {
      "command": "python",
      "args": ["-m", "genie_mcp.server"],
      "env": {
        "DEEPSEEK_API_KEY": "你的Key（可选，不用的话用mock）"
      }
    }
  }
}
```

或者用项目本地配置，在项目根目录创建 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "genie": {
      "command": "python",
      "args": ["-m", "genie_mcp.server"]
    }
  }
}
```

## 3. 使用

配置好后，在 Cursor 的 AI 对话框里直接说：

- "用 genie_run 帮我做一个小说写作工具"
- "用 genie_list_packs 看看有哪些可用的 RolePack"
- "用 genie_hub_search 搜索数据分析相关的包"

Cursor 会自动调用 Genie MCP 工具，10个 AI 角色并行工作，项目文件直接出现在工作区。

## 可用工具

| 工具 | 说明 |
|------|------|
| `genie_run` | 一句话生成完整项目 |
| `genie_list_packs` | 列出所有 RolePack |
| `genie_hub_search` | 搜索市场 |

## 架构

```
Cursor (MCP Client)
    │
    │  JSON-RPC over stdio
    │
    ▼
Genie MCP Server (genie_mcp/server.py)
    │
    ▼
Genie Engine → 10 个 AI 角色并行工作 → 项目文件
```