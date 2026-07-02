"""Genie Engine 主入口 — 加载 Pack → 执行 → 返回结果。"""

import logging
from pathlib import Path

from genie_engine.core.pack_loader import PackLoader
from genie_engine.core.stage_executor import StageExecutor
from genie_engine.core.workspace import Workspace
from genie_engine.schemas.result import EngineResult

logger = logging.getLogger(__name__)


class GenieEngine:
    """领域无关的多 Agent 编排引擎。"""

    def __init__(self, pack_path: Path | str):
        self.loader = PackLoader(Path(pack_path))
        self.workspace = Workspace()

    async def execute(
        self,
        goal: str,
        *,
        model: str = "mock",
        budget: float | None = None,
        resume: bool = False,
    ) -> EngineResult:
        definition = self.loader.load()
        logger.info("RolePack 加载成功: %s v%s", definition.name, definition.version)

        if resume:
            state = self.workspace.resume()
            if state is None:
                logger.warning("没有可恢复的状态，从头开始")
                self.workspace.init(goal, model, budget)
            else:
                logger.info("从阶段 '%s' 恢复", state.current_stage)
        else:
            self.workspace.init(goal, model, budget)

        executor = StageExecutor(definition, self.workspace)
        result = await executor.run_all()

        logger.info(
            "Run 完成: status=%s, stages=%d, duration=%.1fs",
            result.status,
            len(result.stages),
            result.total_duration_seconds,
        )
        return result