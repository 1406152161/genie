# RolePacks

RolePack 是 Genie 的"虚拟团队定义文件"。一个 YAML 文件定义了：
- 这个领域需要哪些角色
- 每个角色的 System Prompt 和能力
- 角色之间如何协作（阶段和并行关系）
- 检查点策略和重试规则

## 内置 RolePack

| RolePack | 文件 | 用途 |
|----------|------|------|
| 🔧 Code | [code.rolepack.yaml](code.rolepack.yaml) | 从需求到完整项目交付 |
| 📦 Pack Creator | [pack.rolepack.yaml](pack.rolepack.yaml) | 创建新的 RolePack |

## 编写你自己的 RolePack

参见 [RolePack 编写指南](../docs/rolepack-guide.md)。

```bash
# 用 Pack Creator 自动生成
genie run pack "创建一个金融量化分析的RolePack"

# 或手动编写YAML后验证
genie pack validate my-pack.rolepack.yaml

# 测试
genie pack test my-pack.rolepack.yaml
```

## 目录约定

```
rolepacks/
├── code.rolepack.yaml       ← 官方维护
├── pack.rolepack.yaml       ← 官方维护
├── community/               ← 社区贡献
│   ├── finance.rolepack.yaml
│   └── legal.rolepack.yaml
└── my/                      ← 用户自建（gitignore）
    └── custom.rolepack.yaml
```
