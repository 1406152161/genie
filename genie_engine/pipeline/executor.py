"""多 RolePack 串联执行器"""

import logging
from pathlib import Path

from genie_engine.core.engine import GenieEngine
from genie_engine.schemas.result import PipelineResult

logger = logging.getLogger(__name__)


class PipelineExecutor:
    """串联执行多个 RolePack。

    用法:
        steps = [
            ("rolepacks/code.rolepack.yaml", "做小说工具"),
            ("rolepacks/pack.rolepack.yaml", "为这个项目创建审计RolePack"),
        ]
        result = await PipelineExecutor(steps).execute()
    """

    def __init__(self, steps: list[tuple[str, str]]):
        """
        Args:
            steps: [(pack_path, goal), ...] — 按顺序执行的 RolePack 和目标
        """
        self.steps = steps

    async def execute(self, model: str = "mock") -> PipelineResult:
        """依次执行所有步骤，前一步的产出上下文注入后一步"""
        context: dict[str, str] = {}
        result = PipelineResult()

        for i, (pack_path, goal) in enumerate(self.steps):
            # 后续步骤注入前置上下文
            enriched_goal = goal
            if i > 0 and context:
                enriched_goal = self._enrich(goal, context)

            logger.info("Pipeline step %d/%d: %s", i + 1, len(self.steps), enriched_goal[:80])

            engine = GenieEngine(pack_path)
            step_result = await engine.execute(enriched_goal, model=model)
            result.steps.append(step_result)

            # 保存上下文供下一步使用
            if step_result.is_success:
                context[Path(pack_path).stem] = step_result.summary or step_result.goal

        return result

    def _enrich(self, goal: str, context: dict[str, str]) -> str:
        """将前置产出摘要注入后续目标"""
        parts = [goal]
        for name, summary in context.items():
            if summary:
                parts.append(f"\n[前置阶段 {name} 的产出摘要]\n{summary[:500]}")
        return "\n".join(parts)
