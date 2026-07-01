# AGENTS.md — Genie 项目开发规范

## 你对我的期望

1. **能自己判断的不要问我**
2. **能跑通的直接干，别犹豫**
3. **遇到分歧才问我，但给我推荐方案**
4. **持续开发，不要做完一件事就停下来等我**

---

## 一、自主决策边界

### 你可以直接做的（不问我）

| 类型 | 示例 |
|------|------|
| 文件创建/修改 | 创建新模块、补 `__init__.py`、写代码 |
| 技术选型 | 用 `dataclass` 还是 `Pydantic`、函数命名 |
| 代码风格 | 你写的代码你自己定风格，保持一致性即可 |
| 测试编写 | 写完代码自动补测试 |
| 依赖添加 | 往 `pyproject.toml` 加依赖（合理的） |
| 文档更新 | 代码改了自动更新相关文档 |
| Git 操作 | commit 但不 push（push 前问一下我） |
| Bug 修复 | 发现 Bug 直接修 |

### 需要问我但给我推荐方案的

| 类型 | 示例 |
|------|------|
| 架构分歧 | "这里该用事件驱动还是轮询？我推荐A，因为..." |
| 方向性变更 | "这个功能有两种实现路径，各有利弊..." |
| 对外可见的行为变更 | CLI 命令名、API 端点、RolePack 公开接口 |

### 需要明确确认的

| 类型 | 示例 |
|------|------|
| 外部服务 | GitHub push、PyPI 发布、调用外部 API |
| 破坏性操作 | 删除已有功能、改变公开 API |
| 安全相关 | 处理密钥、鉴权逻辑变更 |

---

## 二、开发流程

### 每次开发都要做
```
写代码 → 写测试 → 跑测试 → 有失败就修 → 全绿才结束
```

### 提交规范
- 使用 [Conventional Commits](https://www.conventionalcommits.org/)
- 中文描述，简洁有力
- 每次提交的粒度：一个逻辑单元
- 示例：
  ```
  feat: 实现 PackLoader YAML解析+Schema校验
  fix: 修复 StageExecutor 并行角色死锁
  test: 补充 Director 决策边界测试
  refactor: 提取 Workspace 到独立模块
  ```

### 项目当前状态
- 仓库: `https://github.com/1406152161/genie`
- 分支: `main`
- 阶段: **Phase 1 开发中** （schemas → providers → core）
- 内置 RolePack: `code.rolepack.yaml`, `pack.rolepack.yaml`

---

## 三、技术约定

### Python
- 版本: `>=3.11`
- 类型注解: 所有公开函数必须有
- 格式化: ruff (line-length=100)
- 测试: pytest + asyncio mode=auto
- 依赖管理: `pyproject.toml`

### 项目结构约定
```
genie_engine/core/     ← 入口是 engine.py
genie_engine/schemas/  ← 纯数据类，零依赖
genie_engine/providers/ ← 每个 Provider 一个文件
genie_engine/tools/    ← 每个 Tool 一个文件
tests/                 ← 镜像 src 结构
```

### 代码注释
- 模块级 docstring: 必须，用中文
- 类/函数 docstring: 必须，用中文
- 行内注释: 只在逻辑复杂时加

---

## 四、Phase 1 开发顺序

按依赖关系，从底层到上层：

```
① schemas/         ← 纯数据类，无依赖，先写
② providers/       ← 只依赖 schemas/
③ core/            ← 依赖 ①②
   ├── pack_loader.py
   ├── role_factory.py
   ├── workspace.py
   ├── checkpoint.py
   ├── director.py
   ├── stage_executor.py
   └── engine.py
④ tests/           ← 写完一个模块补一个模块的测试
```

### Phase 1 完成标准
- [ ] `schemas/` 所有数据类定义完毕
- [ ] `providers/` 至少实现 Mock + DeepSeek
- [ ] `core/` 7个文件全部实现
- [ ] `tests/` 覆盖率 > 70%
- [ ] `genie pack validate rolepacks/code.rolepack.yaml` 通过
- [ ] CI 全绿

---

## 五、当你不知道怎么决策时

优先级：
1. **这个项目已有的模式** — 参考已有代码
2. **director-ai 的模式** — 参考 `D:\gitHub\director-ai` 里相同场景的做法
3. **Python 社区最佳实践** — PEP、标准库风格
4. **实在不确定就选最简单的方案** — 复杂是债，简单是对

---

## 六、每次对话结束时

- 说清楚做了什么
- 说清楚下一步是什么
- 如果有未完成的事，明确标记
- commit 代码（不 push）
