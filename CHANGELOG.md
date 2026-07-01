# Changelog

All notable changes to Genie will be documented in this file.

## [Unreleased]

### Added
- Genie Engine 核心编排框架
- PackLoader: RolePack YAML 加载与校验
- StageExecutor: 阶段 DAG 调度 + 并行角色执行
- RoleFactory: 角色实例化与依赖注入
- Workspace: 共享文件系统工作空间
- Director: 检查点决策与阶段评估
- Provider Registry: OpenAI / DeepSeek / Anthropic / Ollama 适配
- ModelRouter: 全局默认 + 角色级模型覆盖
- FileScope: 角色文件操作权限隔离
- ProgressHub: SSE 实时进度流
- CostEstimator: 运行前成本预估
- BudgetTracker: 运行时预算控制
- PipelineExecutor: 多 RolePack 串联
- genie_api: FastAPI 后端
- genie_web: React 前端 (Run / Hub / PackEditor / Dashboard)
- genie_cli: 命令行工具
- code.rolepack: 代码生成 RolePack (10角色/5阶段)
- pack.rolepack: RolePack 生成器 (5角色/4阶段)

### Planned
- RolePack Hub 在线市场
- genie pack publish 命令
- 社区 RolePack 审核流程
- 多语言 RolePack 支持

---

格式基于 [Keep a Changelog](https://keepachangelog.com/).
