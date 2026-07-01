"""Genie Engine 主入口 — 加载 Pack → 执行 → 返回结果。"""

import logging
from pathlib import Path

from genie_engine.core.pack_loader import PackLoader
from genie_engine.core.stage_executor import StageExecutor
from genie_engine.core.workspace import Workspace
from genie_engine.schemas.result import EngineResult

logger = logging.getLogger(__name__)


class GenieEngine:
    """领域无关的多 Agent 编排引擎。

    用法:
        engine = GenieEngine("code.rolepack.yaml")
        result = await engine.execute("做一个小说写作工具")
    """

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
        """执行一次完整的 RolePack 运行。

        Args:
            goal: 用户的一句话需求
            model: AI 模型选择
            budget: 预算上限 (USD)
            resume: 是否从上次中断恢复 (Q4)

        Returns:
            EngineResult: 完整的执行结果
        """
        # 加载 RolePack
        definition = self.loader.load()
        logger.info("RolePack 加载成功: %s v%s", definition.name, definition.version)

        # 初始化或恢复工作空间
        if resume:
            state = self.workspace.resume()
            if state is None:
                logger.warning("没有可恢复的状态，从头开始")
                self.workspace.init(goal, model, budget)
            else:
                logger.info("从阶段 '%s' 恢复", state.current_stage)
        else:
            self.workspace.init(goal, model, budget)

        # 执行
        executor = StageExecutor(definition, self.workspace)
        result = await executor.run_all()

        logger.info(
            "Run 完成: status=%s, stages=%d, duration=%.1fs",
            result.status,
            len(result.stages),
            result.total_duration_seconds,
        )

        return result
