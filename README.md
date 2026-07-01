# 🧠 Genie — 你说一句话，它还你一个项目

[![CI](https://github.com/1406152161/genie/actions/workflows/ci.yml/badge.svg)](https://github.com/1406152161/genie/actions/workflows/ci.yml)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![RolePacks](https://img.shields.io/badge/RolePacks-2-8A2BE2)](rolepacks/)

> **不是 AI 助手。不是 Copilot。是一个能组建虚拟团队、自主完成项目的 AI 引擎。**

---

## 这是什么

你说 "我想做一个小说写作AI工具"，Genie 会：

1. 🔍 **自动调研** — 搜索 GitHub 竞品，分析技术方案
2. 🏗️ **自主设计** — 选技术栈，画架构，定数据模型
3. ⚡ **并行构建** — 5个AI工程师同时写后端、前端、测试、文档
4. 🔬 **自动验证** — 跑测试、lint、修复问题
5. ✅ **完整交付** — 10分钟后，一个能跑的项目就绪

**你不写一行代码。你只说一句话。**

---

## 快速开始

### 安装

```bash
pip install genie-engine
```

### 一句话生成项目

```bash
genie run code "帮我做一个待办事项管理Web应用"
```

### 创建你自己的领域RolePack

```bash
genie run pack "创建一个电商数据分析的RolePack"
```

### 串联多个RolePack

```bash
genie run code "做区块链钱包" | genie run pack "为这个项目做安全审计"
```

---

## 核心概念

```
你说一句话
    │
    ▼
┌──────────────────────┐
│   🧠 Genie Engine    │  ← 领域无关的编排引擎
│   (永不改变)          │
└──────┬───────────────┘
       │ 加载
┌──────▼───────────────┐
│   📦 RolePack        │  ← YAML定义的虚拟团队
│   (无限扩展)          │
└──────┬───────────────┘
       │ 执行
┌──────▼───────────────┐
│   🎬 一次 Run        │
│   完整项目交付         │
└──────────────────────┘
```

- **Genie Engine**：只做一件事 — 加载 RolePack，执行角色，交付结果。不关心领域。
- **RolePack**：一个 YAML 文件，定义了"这个领域需要哪些角色、怎么协作"。
- **Run**：用户选一个 RolePack + 一句话需求 = 一个完整的项目。

---

## 内置 RolePack

| RolePack | 用途 | 角色数 | 阶段 |
|----------|------|--------|------|
| 🔧 `code` | 从需求到完整项目交付 | 10 | 5 |
| 📦 `pack` | 创建新的 RolePack | 5 | 4 |

### 安装社区 RolePack

```bash
genie pack install community/finance    # 量化金融分析
genie pack install community/legal      # 合同审查
```

[查看所有 RolePack →](https://github.com/1406152161/genie/tree/main/rolepacks)

---

## Web 界面

除了 CLI，Genie 还提供 Web 界面：

```bash
genie web
# 打开 http://localhost:5173
```

- 📝 **Run 页面**：输入需求，实时看进度
- 📦 **Hub 页面**：浏览安装 RolePack
- ✏️ **PackEditor**：可视化管理 RolePack

---

## 项目结构

```
genie/
├── genie_engine/          # 🧠 引擎核心
│   ├── core/              # 编排层
│   ├── providers/         # AI后端适配
│   ├── tools/             # 角色工具集
│   ├── sandbox/           # 安全隔离
│   ├── progress/          # 实时进度
│   ├── cost/              # 成本控制
│   ├── pipeline/          # 串联管道
│   └── schemas/           # 数据定义
├── genie_api/             # 🌐 FastAPI后端
├── genie_web/             # 🖥️ React前端
├── genie_cli/             # ⌨️ CLI
├── genie_hub/             # 📦 RolePack市场
├── rolepacks/             # 🎭 内置角色包
├── tests/                 # 🧪 测试
└── docs/                  # 📖 文档
```

---

## 为什么做这个

现有 AI 工具都是**被动的**——你问一句它答一句。你让它写代码，它写一个文件。你让它设计架构，它给你一段话。

Genie 是**主动的**——你说目标，它自己拆解、自己决策、自己执行、自己验证。像一个真正的工程师，不是像一个搜索引擎。

---

## 文档

| 文档 | 适合谁 |
|------|--------|
| [快速开始](docs/quickstart.md) | 所有人 |
| [架构设计](docs/architecture.md) | 开发者 |
| [RolePack 编写指南](docs/rolepack-guide.md) | RolePack 作者 |
| [API 文档](docs/api.md) | 集成开发者 |
| [部署指南](docs/deployment.md) | 运维 |

---

## 贡献

欢迎贡献！详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

- 🐛 [报告 Bug](https://github.com/1406152161/genie/issues/new?template=bug_report.yml)
- 💡 [功能建议](https://github.com/1406152161/genie/issues/new?template=feature_request.yml)
- 📦 [贡献 RolePack](docs/rolepack-guide.md)

---

## 许可证

[AGPL v3](LICENSE) — 开源免费，云服务使用需开源。

商业授权（闭源使用）：联系 1406152161@qq.com

---

<p align="center">
  <b>Genie</b> — 你的 AI 虚拟团队<br>
  Made with ❤️ by <a href="https://github.com/1406152161">1406152161</a>
</p>
