"""ProviderComparator — 多 Provider 并行运行 + 对比"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path

from genie_engine.core.engine import GenieEngine
from genie_engine.schemas.result import EngineResult
from genie_engine.providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


@dataclass
class ModelRun:
    """单个模型的一次运行结果"""
    model: str
    result: EngineResult | None = None
    error: str = ""
    duration_seconds: float = 0.0
    cost_usd: float = 0.0


@dataclass
class CompareReport:
    """多模型对比报告"""
    goal: str
    pack_name: str
    pack_version: str
    runs: list[ModelRun] = field(default_factory=list)
    models_passed: list[str] = field(default_factory=list)
    models_failed: list[str] = field(default_factory=list)
    fastest: str = ""
    slowest: str = ""
    total_duration: float = 0.0

    @property
    def pass_rate(self) -> float:
        total = len(self.runs)
        if total == 0:
            return 0.0
        return len(self.models_passed) / total

    @property
    def summary(self) -> str:
        lines = [
            f"Compare Report: {self.pack_name} v{self.pack_version}",
            f"Goal: {self.goal}",
            f"Models tested: {len(self.runs)}",
            f"Pass rate: {self.pass_rate:.0%} ({len(self.models_passed)}/{len(self.runs)})",
            f"Passed: {', '.join(self.models_passed) if self.models_passed else 'none'}",
            f"Failed: {', '.join(self.models_failed) if self.models_failed else 'none'}",
            f"Fastest: {self.fastest}",
            f"Slowest: {self.slowest}",
            f"Total duration: {self.total_duration:.1f}s",
        ]
        return "\n".join(lines)


class ProviderComparator:
    """多 Provider 回归测试器。

    Q3 核心功能:
    - 用不同 AI 模型运行同一个 RolePack
    - 对比产出质量、速度、成本
    - 生成对比报告
    """

    def __init__(self, pack_path: Path | str):
        self.pack_path = Path(pack_path)

    async def compare(
        self,
        goal: str,
        models: list[str],
        *,
        budget: float | None = None,
        parallel: bool = True,
    ) -> CompareReport:
        """用多个模型运行同一个 RolePack 并对比。

        Args:
            goal: 用户的一句话需求
            models: 要测试的模型列表，如 ["mock", "deepseek", "gpt4"]
            budget: 每个 run 的预算上限
            parallel: 是否并行运行（默认 True）
        """
        start = time.monotonic()

        # 加载 pack 元信息
        from genie_engine.core.pack_loader import PackLoader
        definition = PackLoader(self.pack_path).load()

        report = CompareReport(
            goal=goal,
            pack_name=definition.name,
            pack_version=definition.version,
        )

        if parallel:
            # 并行运行所有模型
            tasks = [
                self._run_single(goal, model, budget)
                for model in models
            ]
            runs = await asyncio.gather(*tasks, return_exceptions=True)
            for i, run_or_exc in enumerate(runs):
                if isinstance(run_or_exc, Exception):
                    report.runs.append(ModelRun(
                        model=models[i],
                        error=str(run_or_exc),
                    ))
                else:
                    report.runs.append(run_or_exc)
        else:
            # 串行运行
            for model in models:
                run = await self._run_single(goal, model, budget)
                report.runs.append(run)

        # 汇总
        for run in report.runs:
            if run.result and run.result.is_success:
                report.models_passed.append(run.model)
            else:
                report.models_failed.append(run.model)

        durations = [(r.model, r.duration_seconds) for r in report.runs if r.duration_seconds > 0]
        if durations:
            report.fastest = min(durations, key=lambda x: x[1])[0]
            report.slowest = max(durations, key=lambda x: x[1])[0]

        report.total_duration = round(time.monotonic() - start, 2)
        return report

    async def _run_single(
        self, goal: str, model: str, budget: float | None
    ) -> ModelRun:
        """单模型运行"""
        run = ModelRun(model=model)
        start = time.monotonic()

        try:
            # 验证 provider 可用
            available = ProviderRegistry.list_all()
            if model != "mock" and model not in available:
                run.error = f"Provider '{model}' not registered. Available: {available}"
                run.duration_seconds = round(time.monotonic() - start, 2)
                return run

            engine = GenieEngine(self.pack_path)
            # Each run gets its own isolated workspace to avoid conflicts
            import time as _time
            engine.workspace = (
                engine.workspace.__class__(
                    Path(f"genie_compare_{model}_{int(_time.monotonic() * 1000000)}")
                )
            )
            result = await engine.execute(goal, model=model, budget=budget)
            run.result = result
            run.cost_usd = result.total_cost_usd
        except Exception as exc:
            run.error = str(exc)

        run.duration_seconds = round(time.monotonic() - start, 2)
        return run