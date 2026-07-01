# 贡献指南

感谢你考虑为 Genie 做出贡献！

## 行为准则

本项目遵循 [贡献者公约](CODE_OF_CONDUCT.md)。参与即表示你同意遵守其条款。

## 如何贡献

### 报告 Bug

1. 使用 [Bug Report](https://github.com/1406152161/genie/issues/new?template=bug_report.yml) 模板
2. 描述复现步骤
3. 附上 Genie 版本和 Python 版本

### 功能建议

1. 使用 [Feature Request](https://github.com/1406152161/genie/issues/new?template=feature_request.yml) 模板
2. 描述使用场景和期望行为

### 贡献 RolePack

1. 阅读 [RolePack 编写指南](docs/rolepack-guide.md)
2. 在 `rolepacks/community/` 下创建你的 RolePack
3. 确保通过校验：`genie pack validate your-pack`
4. 提交 PR

### 贡献代码

1. Fork 本仓库
2. 从 `main` 分支创建 `feature/xxx` 分支
3. 编写代码 + 测试
4. 运行 `pytest` 确保全绿
5. 提交 PR 到 `main`

## 开发环境

```bash
git clone https://github.com/1406152161/genie.git
cd genie
pip install -e ".[dev]"
```

## 提交规范

使用 [Conventional Commits](https://www.conventionalcommits.org/)：

```
feat: 添加 RolePack 自动校验功能
fix: 修复并行角色文件冲突
docs: 更新 RolePack 编写指南
test: 添加 Director 决策测试
```

## 分支策略

| 分支 | 用途 |
|------|------|
| `main` | 稳定发布 |
| `feature/*` | 新功能 |
| `fix/*` | Bug 修复 |

## 代码风格

- Python: Black + isort + mypy
- TypeScript: Prettier + ESLint
- 注释使用中文
- 所有公开 API 必须有 docstring

## 测试

```bash
# 单元测试
pytest tests/ -q

# 含覆盖率
pytest tests/ --cov=genie_engine -q

# RolePack 回归测试
genie pack test code.rolepack
```
