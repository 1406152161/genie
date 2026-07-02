"""Genie CLI — 命令行入口"""

import asyncio
import sys
from pathlib import Path


def main():
    """CLI 入口（setup.py entry_point 指向此函数）"""
    if len(sys.argv) < 2:
        _print_usage()
        return

    command = sys.argv[1]

    if command == "run":
        asyncio.run(_cmd_run(sys.argv[2:]))
    elif command == "pack":
        _cmd_pack(sys.argv[2:])
    elif command == "validate":
        _cmd_validate(sys.argv[2:])
    elif command in ("-h", "--help", "help"):
        _print_usage()
    else:
        print(f"未知命令: {command}")
        _print_usage()


def _print_usage():
    print("""Genie — 你说一句话，它还你一个项目。

用法:
  genie run <pack> "你的需求"
  genie pack validate <pack.yaml>
  genie pack list

示例:
  genie run code "做一个小说写作AI工具"
  genie pack validate rolepacks/code.rolepack.yaml
""")


async def _cmd_run(args: list[str]):
    """genie run <pack> <goal>"""
    if len(args) < 2:
        print("用法: genie run <pack> <goal>")
        print("示例: genie run code '做一个小说写作AI工具'")
        return

    pack_name = args[0]
    goal = args[1]

    # 查找 RolePack 文件
    pack_path = _find_pack(pack_name)
    if not pack_path:
        print(f"找不到 RolePack: {pack_name}")
        print("可用: code, pack")
        return

    from genie_engine.core.engine import GenieEngine
    from genie_engine.progress.hub import get_progress_hub

    print(f"\n[Genie] Genie 开始工作: {goal}")
    print(f"[Pack] 使用: {pack_name}\n")

    engine = GenieEngine(pack_path)
    hub = get_progress_hub()

    # 后台订阅进度
    async def print_progress():
        async for event in hub.subscribe("cli_run"):
            if event["type"] == "heartbeat":
                continue
            stage = event.get("stage", "")
            role = event.get("role", "")
            status = event.get("status", "")
            icon = "[OK]" if status == "completed" else "[...]" if status == "running" else "[---]"
            if stage:
                print(f"  {icon} [{stage}] {role or ''} {status}")
            if event.get("done"):
                break

    progress_task = asyncio.create_task(print_progress())

    try:
        result = await engine.execute(goal, model="mock")
        progress_task.cancel()
    except Exception as exc:
        print(f"\n[ERR] 运行失败: {exc}")
        return

    print(f"\n{'='*50}")
    print(f"状态: {result.status}")
    print(f"耗时: {result.total_duration_seconds:.1f}s")
    print(f"阶段: {len(result.stages)} 个")
    for s in result.stages:
        icon = "[OK]" if s.status == "completed" else "[ERR]"
        print(f"  {icon} {s.stage_id}: {s.status} ({s.duration_seconds:.1f}s)")
    if result.warnings:
        print(f"警告: {len(result.warnings)} 条")
    print(f"输出: {result.output_dir}")


def _cmd_pack(args: list[str]):
    """genie pack validate|list"""
    if not args:
        print("用法: genie pack <validate|list>")
        return

    sub = args[0]
    if sub == "validate":
        if len(args) < 2:
            print("用法: genie pack validate <pack.yaml>")
            return
        _validate_pack(args[1])
    elif sub == "list":
        _list_packs()
    else:
        print(f"未知子命令: pack {sub}")


def _cmd_validate(args: list[str]):
    """genie validate <pack.yaml> (简写)"""
    if not args:
        print("用法: genie validate <pack.yaml>")
        return
    _validate_pack(args[0])


def _validate_pack(path_str: str):
    """校验 RolePack 文件"""
    from genie_engine.core.pack_loader import PackLoader

    try:
        definition = PackLoader(path_str).load()
        print(f"[OK] {definition.name} v{definition.version} — 校验通过")
        print(f"   阶段: {len(definition.stages)} 个")
        print(f"   角色: {len(definition.roles)} 个")
    except Exception as exc:
        print(f"[ERR] 校验失败: {exc}")
        sys.exit(1)


def _list_packs():
    """列出可用的 RolePack"""
    packs_dir = Path(__file__).parent.parent / "rolepacks"
    for f in packs_dir.glob("*.yaml"):
        print(f"  [Pack] {f.stem} — {f.name}")


def _find_pack(name: str) -> Path | None:
    """按名称查找 RolePack 文件"""
    packs_dir = Path(__file__).parent.parent / "rolepacks"
    candidates = [
        packs_dir / f"{name}.rolepack.yaml",
        packs_dir / f"{name}.yaml",
        packs_dir / "community" / f"{name}.rolepack.yaml",
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


if __name__ == "__main__":
    main()
