# AGENTS.md — Genie 项目开发规范

> 这份文件就是我的"入职手册"。我会在每次操作前检查是否违反了这里的规定。
> 如果我发现规范有遗漏，我会主动建议更新这个文件。

---

## 一、根本原则

### 你只需要告诉我"做什么"，"怎么做"我来。

如果一件事满足以下所有条件，**直接做，不要问**：
- 不会改变公开 API
- 不会删除已有功能
- 不需要外部服务（push/publish/API key）
- 你已有足够上下文做出正确判断

---

## 二、代码质量 — 写完不算完，以下全部通过才算完

### 提交前自检清单（每次 commit 前必须全部 ✅）

```
□ ruff check     →  0 errors
□ mypy           →  0 errors（至少 genie_engine/ 目录）
□ pytest         →  全部通过
□ 新增代码有测试  →  覆盖率不低于70%
□ 公开函数有 docstring
□ 类型注解完整（无 Any 除非有明确理由）
□ 无 dead code（未使用的 import/变量/函数）
□ 无 print 调试语句
□ pyproject.toml 依赖与实际 import 一致
```

### 如果我漏了其中任何一步

那就是我的失误。你应该在 review 时指出来，我会立刻修正。

### 测试写什么

| 代码类型 | 必须的测试 |
|---------|-----------|
| 数据类/Schema | 序列化/反序列化、边界值 |
| Provider | mock 调用、异常处理（超时/认证失败/格式错误） |
| 核心逻辑 | 正常路径 + 异常路径 + 边界条件 |
| CLI 命令 | 参数解析、输出格式 |
| RolePack YAML | 校验通过/失败用例 |

### 测试怎么写

```python
# ✅ 好的测试：独立、快速、有明确断言
async def test_pack_loader_valid_yaml():
    loader = PackLoader(Path("code.rolepack.yaml"))
    definition = loader.load()
    assert definition.name == "Genie Code"
    assert len(definition.stages) == 4

# ✅ 好的测试：也测失败路径
def test_pack_loader_invalid_yaml_raises():
    with pytest.raises(PackLoadError, match="schema校验失败"):
        PackLoader(Path("invalid.rolepack.yaml")).load()

# ❌ 坏的测试：依赖外部服务、有副作用、断言模糊
def test_bad():
    result = some_function()
    assert result  # 断言什么？
```

---

## 三、提交规范

### Commit Message 格式

```
<type>: <简短中文描述>

<可选的详细说明>
```

| type | 何时用 |
|------|--------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 重构（行为不变） |
| `test` | 添加/修改测试 |
| `docs` | 文档变更 |
| `chore` | 构建/依赖/配置 |

### 提交粒度

- **一个 commit = 一个逻辑变更**
- 不要把"实现功能 + 修 bug + 改格式"混在一个 commit 里
- 如果发现上一個 commit 有问题，用 `--amend` 而不是新开一个 "fix typo" commit
- **不要提交 WIP（work in progress）** — 要么做完再 commit，要么用 stash

### 不要提交的东西

```
□ .env 文件（含真实密钥）
□ __pycache__/
□ .pytest_cache/
□ 大文件（>1MB 的二进制）
□ node_modules/
□ IDE 配置（.vscode/ 除共享配置外）
```

---

## 四、项目结构纪律

### 文件组织

```
新增一个 Provider  → genie_engine/providers/<name>.py + 在 registry.py 注册
新增一个 Tool      → genie_engine/tools/<name>.py + 在 registry.py 注册
新增一个 Schema    → genie_engine/schemas/<name>.py
新增一个核心模块    → genie_engine/core/<name>.py
新增测试           → tests/test_<module>.py（镜像 src 结构）
```

### 模块依赖规则

```
schemas/         ← 零依赖，纯数据类
providers/       ← 只依赖 schemas/
tools/           ← 只依赖 sandbox/
sandbox/         ← 零依赖
progress/        ← 零依赖
cost/            ← 只依赖 providers/（读model价目表）
core/            ← 依赖以上所有
pipeline/        ← 依赖 core/
```

**绝对禁止循环依赖。** 如果发现可能循环，提取共享接口到 schemas/。

### import 规范

```python
# ✅ 好的 import
from genie_engine.schemas.rolepack import RolePackDefinition
from genie_engine.providers.registry import ProviderRegistry

# ✅ 惰性导入（重型依赖在函数内导入）
def _ensure_client(self):
    import chromadb  # noqa: PLC0415
    ...

# ❌ 坏的 import
from genie_engine.core.engine import *  # 禁止 *
from ..whatever import something       # 禁止相对导入超过一层
```

---

## 五、错误处理规则

### 自定义异常

```python
# genie_engine/core/exceptions.py
class GenieError(Exception): ...
class PackLoadError(GenieError): ...
class StageExecutionError(GenieError): ...
class ProviderError(GenieError): ...
class ProviderAuthError(ProviderError): ...
class ProviderTimeoutError(ProviderError): ...
class SandboxError(GenieError): ...
class BudgetExceededError(GenieError): ...
```

### 错误处理原则

- **不吞异常** — 捕获了就要处理，至少要 log
- **异常消息要有信息量** — `raise ValueError("chapter_index 必须 >0，实际: -1")` 而不是 `raise ValueError("invalid")`
- **预期内错误用自定义异常**，让调用方能精确捕获
- **预期外错误让它炸** — 不要用 `except Exception: pass`

---

## 六、性能与资源

- **重型依赖惰性导入**（chromadb, celery, redis）
- **异步 I/O 用 asyncio**，不阻塞事件循环
- **大文件分块读**，不要一次 `read()` 全进内存
- **不再使用的资源要释放**（文件句柄、数据库连接、Redis 连接）
- **RolePack 执行过程中及时写 Workspace state**，避免崩溃丢进度

---

## 七、安全

- **密钥不进代码** — 全走环境变量，`.env.example` 是模板
- **不 log 密钥** — logging 时脱敏 token/key/password
- **用户输入必须校验** — 不管是 CLI 参数还是 RolePack YAML
- **文件路径防穿越** — `Path(...).resolve()` 必须在允许范围内
- **依赖安全检查** — `pip-audit` 定期跑，Dependabot 告警必须处理

---

## 八、文档同步

| 代码变更 | 需要同步的文档 |
|---------|-------------|
| 新模块 | `docs/architecture.md` |
| 新 API | `docs/api.md` |
| 新 CLI 命令 | `README.md` 快速开始部分 |
| 新 RolePack | `rolepacks/README.md` |
| 公开发布 | `CHANGELOG.md` |
| 设计决策 | `.genie/decisions/` 或本文件 |

---

## 九、CI/CD — 永远不要让 CI 红灯

### CI 做的事（`.github/workflows/ci.yml`）

```
1. ruff check     → 代码风格
2. mypy           → 类型检查
3. pytest         → 测试
4. RolePack 校验   → genie pack validate
5. RolePack 回归   → genie pack test
```

### 我的职责

- **commit 前本地跑过所有 CI 步骤**
- 不确定的话先本地跑一遍再 commit
- CI 红了第一优先级修，不新增功能

---

## 十、与其他项目的关系

### 参考 director-ai 的模式

`D:\gitHub\director-ai` 是本项目的"前辈"，以下模式直接复用：

| director-ai 模式 | 用在哪里 |
|-----------------|---------|
| Provider 注册表 (dict + _resolve) | genie_engine/providers/registry.py |
| ProgressHub (内存 fanout + Redis) | genie_engine/progress/hub.py |
| 任务调度抽象 (background/celery) | genie_engine/core/stage_executor.py |
| Mock Provider 全覆盖 | genie_engine/providers/mock.py |
| 测试 conftest (内存DB+环境变量隔离) | tests/conftest.py |
| Story Bible 结构化知识 | 项目知识库（未来） |

---

## 十一、持续改进

### 这个文件本身应该持续更新

如果我发现：
- 某个规则反复被违反 → 说明规则不清晰，需要细化
- 出现了新的项目约定 → 加到本文件
- 某个规则过时了 → 更新它

**我会在发现这些问题时主动建议更新 AGENTS.md。**

---

## 十二、当前状态（Phase 1）

```
✅ 项目骨架      34个文件，已推送到GitHub
✅ AGENTS.md     本文件
⏳ schemas/      待实现
⏳ providers/    待实现
⏳ core/         待实现
⏳ tests/        待实现
```

**下一步：实现 Phase 1 — schemas/ → providers/ → core/ → tests/**

每个模块完成后自己跑 `ruff + mypy + pytest`，全绿才算这个模块 done。
