import asyncio
import sys
from pathlib import Path


def main():
    """CLI entry point"""
    if len(sys.argv) < 2:
        _print_usage()
        return

    command = sys.argv[1]

    if command == "compare":
        asyncio.run(_cmd_compare(sys.argv[2:]))
    elif command == "hub":
        _cmd_hub(sys.argv[2:])
    elif command == "run":
        asyncio.run(_cmd_run(sys.argv[2:]))
    elif command == "pack":
        _cmd_pack(sys.argv[2:])
    elif command == "validate":
        _cmd_validate(sys.argv[2:])
    elif command in ("-h", "--help", "help"):
        _print_usage()
    else:
        print(f"Unknown command: {command}")
        _print_usage()


def _print_usage():
    print("""Genie - One sentence, one project.

Usage:
  genie run <pack> "your goal"
  genie pack validate <pack.yaml>
  genie pack list
  genie hub search <query>
  genie hub list
  genie compare <pack> <goal> [--models m1,m2]
  genie pipeline run <steps.yaml>

Examples:
  genie run code "Build a novel writing AI tool"
  genie pack validate rolepacks/code.rolepack.yaml
  genie hub search code
""")


async def _cmd_run(args: list[str]):
    """genie run <pack> <goal>"""
    if len(args) < 2:
        print("Usage: genie run <pack> <goal>")
        print('Example: genie run code "Build a novel writing AI tool"')
        return

    pack_name = args[0]
    goal = args[1]

    pack_path = _find_pack(pack_name)
    if not pack_path:
        print(f"RolePack not found: {pack_name}")
        print("Available: code, pack")
        return

    from genie_engine.core.engine import GenieEngine
    from genie_engine.progress.hub import get_progress_hub

    print(f"\n[Genie] Starting: {goal}")
    print(f"[Pack] Using: {pack_name}\n")

    engine = GenieEngine(pack_path)
    hub = get_progress_hub()

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
        print(f"\n[ERR] Run failed: {exc}")
        return

    print(f"\n{'='*50}")
    print(f"Status: {result.status}")
    print(f"Duration: {result.total_duration_seconds:.1f}s")
    print(f"Stages: {len(result.stages)}")
    for s in result.stages:
        icon = "[OK]" if s.status == "completed" else "[ERR]"
        print(f"  {icon} {s.stage_id}: {s.status} ({s.duration_seconds:.1f}s)")
    if result.warnings:
        print(f"Warnings: {len(result.warnings)}")
    print(f"Output: {result.output_dir}")


def _cmd_pack(args: list[str]):
    """genie pack validate|list"""
    if not args:
        print("Usage: genie pack <validate|list>")
        return

    sub = args[0]
    if sub == "validate":
        if len(args) < 2:
            print("Usage: genie pack validate <pack.yaml>")
            return
        _validate_pack(args[1])
    elif sub == "list":
        _list_packs()
    else:
        print(f"Unknown sub-command: pack {sub}")


def _cmd_validate(args: list[str]):
    """genie validate <pack.yaml> (shorthand)"""
    if not args:
        print("Usage: genie validate <pack.yaml>")
        return
    _validate_pack(args[0])


def _validate_pack(path_str: str):
    """Validate a RolePack file"""
    from genie_engine.core.pack_loader import PackLoader

    try:
        definition = PackLoader(path_str).load()
        print(f"[OK] {definition.name} v{definition.version} - validation passed")
        print(f"    Stages: {len(definition.stages)}")
        print(f"    Roles: {len(definition.roles)}")
    except Exception as exc:
        print(f"[ERR] Validation failed: {exc}")
        sys.exit(1)


def _list_packs():
    """List available RolePacks"""
    packs_dir = Path(__file__).parent.parent / "rolepacks"
    for f in packs_dir.glob("*.yaml"):
        print(f"  [Pack] {f.stem} - {f.name}")


def _cmd_hub(args: list[str]):
    """genie hub search|list|install|uninstall"""
    if not args:
        print("Usage: genie hub <search|list|install|uninstall>")
        return

    from genie_hub import LocalRegistry, Marketplace, PackInstaller, InstallResult

    sub = args[0]
    registry = LocalRegistry()
    marketplace = Marketplace(registry)
    installer = PackInstaller()

    if sub == "search":
        query = args[1] if len(args) > 1 else ""
        results = marketplace.search(query) if query else marketplace.list_community()
        if not results:
            print("(no matching RolePacks found)")
            return
        print(f"\nSearch results ({len(results)}):\n")
        for p in results:
            installed = "[installed]" if registry.is_installed(p.name) else "[available]"
            print(f"  {p.icon} {installed} {p.name} v{p.version}")
            print(f"          {p.description}")
            if p.tags:
                print(f"          tags: {', '.join(p.tags)}")
            print()

    elif sub == "list":
        packs = registry.list_all()
        if not packs:
            print("(no RolePacks installed, try: genie hub search)")
            return
        print(f"\nInstalled RolePacks ({len(packs)}):\n")
        for p in packs:
            print(f"  {p.icon} {p.name} v{p.version}")
            print(f"          {p.description}")
            print(f"          path: {p.path}")
            print()

    elif sub == "install":
        if len(args) < 2:
            print("Usage: genie hub install <pack_name>")
            return
        name = args[1]
        pack = marketplace.get_community_pack(name)
        if pack:
            result = installer.install_from_community(pack)
        else:
            result = InstallResult(
                success=False, pack_name=name, version="?",
                error=f"Pack not found in marketplace: {name}"
            )
        if result.success:
            print(f"[OK] {result.pack_name} v{result.version} installed!")
            print(f"      {result.installed_path}")
        else:
            print(f"[ERR] {result.error}")

    elif sub == "uninstall":
        if len(args) < 2:
            print("Usage: genie hub uninstall <pack_name>")
            return
        result = installer.uninstall(args[1])
        if result.success:
            print(f"[OK] {result.pack_name} uninstalled")
        else:
            print(f"[ERR] {result.error}")

    else:
        print(f"Unknown sub-command: hub {sub}")
        print("Available: hub search|list|install|uninstall")




def _cmd_pipeline(args: list[str]):
    """genie pipeline run <steps.yaml>"""
    if not args or args[0] not in ("run",):
        print("Usage: genie pipeline run <steps.yaml>")
        print()
        print("Steps YAML format:")
        print("  steps:")
        print('    - pack: code')
        print('      goal: "Build a todo app"')
        print('    - pack: pack')
        print('      goal: "Create audit RolePack for the project"')
        return

    if len(args) < 2:
        print("Usage: genie pipeline run <steps.yaml>")
        return

    from genie_engine.pipeline.executor import PipelineExecutor
    import yaml

    steps_path = Path(args[1])
    if not steps_path.exists():
        print(f"Steps file not found: {steps_path}")
        return

    try:
        data = yaml.safe_load(steps_path.read_text(encoding="utf-8"))
        raw_steps = data.get("steps", [])
    except Exception as exc:
        print(f"Failed to parse steps YAML: {exc}")
        return

    if not raw_steps:
        print("No steps defined in YAML")
        return

    # Resolve pack names to paths
    steps: list[tuple[str, str]] = []
    for s in raw_steps:
        pack_name = s.get("pack", "")
        goal = s.get("goal", "")
        pack_path = _find_pack(pack_name)
        if not pack_path:
            print(f"Pack not found: {pack_name}")
            return
        steps.append((str(pack_path), goal))

    print(f"\n[Pipeline] Running {len(steps)} steps:\n")
    for i, (path, goal) in enumerate(steps):
        print(f"  {i+1}. [{Path(path).stem}] {goal}")
    print()

    executor = PipelineExecutor(steps)
    result = asyncio.run(executor.execute())

    print(f"\n{'='*50}")
    if result.all_passed:
        print("Pipeline: ALL PASSED")
    else:
        passed = sum(1 for s in result.steps if s.is_success)
        print(f"Pipeline: {passed}/{len(result.steps)} passed")
    print(f"Total cost: ${result.total_cost_usd:.4f}")
    for i, step in enumerate(result.steps):
        icon = "[OK]" if step.is_success else "[ERR]"
        print(f"  {icon} Step {i+1}: {step.status} ({step.total_duration_seconds:.1f}s)")

def _cmd_compare(args: list[str]):
    """genie compare <pack> <goal> [--models model1,model2,...]"""
    if len(args) < 2:
        print("Usage: genie compare <pack> <goal> [--models m1,m2,...]")
        print('Example: genie compare code "Build a todo app" --models mock,deepseek')
        return

    pack_name = args[0]
    goal = args[1]
    models = ["mock"]

    # Parse --models flag
    for i, a in enumerate(args):
        if a == "--models" and i + 1 < len(args):
            models = [m.strip() for m in args[i + 1].split(",")]
            break

    pack_path = _find_pack(pack_name)
    if not pack_path:
        print(f"RolePack not found: {pack_name}")
        return

    from genie_engine.compare.runner import ProviderComparator

    print(f"\n[Compare] Running '{goal}' with {len(models)} models: {', '.join(models)}\n")

    comparator = ProviderComparator(pack_path)
    report = asyncio.run(comparator.compare(goal, models))

    print(report.summary)
    print()

    for run in report.runs:
        icon = "[OK]" if run.model in report.models_passed else "[ERR]"
        if run.error:
            print(f"  {icon} {run.model}: ERROR — {run.error}")
        elif run.result:
            stages_ok = sum(1 for s in run.result.stages if s.status == "completed")
            print(f"  {icon} {run.model}: {stages_ok}/{len(run.result.stages)} stages, {run.duration_seconds:.1f}s, ${run.cost_usd:.4f}")

def _find_pack(name: str) -> Path | None:
    """Find RolePack file by name"""
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