"""Director — 检查点决策与阶段评估。

这是唯一能与用户交互的角色。
"""

import asyncio
import logging
from datetime import datetime, timezone

from genie_engine.core.workspace import Workspace
from genie_engine.providers.base import Message
from genie_engine.providers.registry import ProviderRegistry
from genie_engine.schemas.rolepack import CheckpointMode, StageDef

logger = logging.getLogger(__name__)


class DirectorDecision(str):
    """Director 的决策结果"""
    PASS = "pass"
    FAIL = "fail"
    ASK_USER = "ask_user"
    ABORT = "abort"


class Director:
    """总指挥 — 唯一的决策者和用户接口。

    决策原则: 90%自主，只在方向性分歧时询问用户。
    """

    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        # Director 用便宜的模型做决策
        self.provider = ProviderRegistry.get("mock")

    async def checkpoint(self, stage: StageDef) -> str:
        """决定是否可以进入此阶段。

        Returns:
            "pass": 通过，继续
            "ask_user": 需要询问用户
        """
        mode = stage.checkpoint_mode

        if mode == CheckpointMode.AUTO:
            return DirectorDecision.PASS

        if mode == CheckpointMode.AUTO_TIMEOUT:
            # 自动通过，但有超时窗口供用户介入
            logger.info(
                "检查点 %s: auto_timeout (%ss)，默认通过",
                stage.id,
                stage.timeout_seconds,
            )
            return DirectorDecision.PASS

        if mode == CheckpointMode.MANUAL:
            # 必须用户确认 — 返回 ask_user
            return DirectorDecision.ASK_USER

        return DirectorDecision.PASS

    async def evaluate(self, stage: StageDef, role_outputs: list) -> bool:
        """评估阶段产出是否达标。

        策略 (Q3):
        - 使用独立的标准评估（不是简单 PASS/FAIL）
        - 标注置信度
        - 用户可通过模型选择影响评估质量
        """
        # 简单的规则评估: 所有角色都 completed 就算通过
        from genie_engine.schemas.result import RoleOutput

        for output in role_outputs:
            if isinstance(output, RoleOutput):
                if output.status == "failed":
                    logger.warning(
                        "阶段 %s: 角色 %s 失败 — %s",
                        stage.id,
                        output.role_name,
                        output.error,
                    )

        # 记录决策供后续复用
        all_completed = all(
            isinstance(o, RoleOutput) and o.status == "completed"
            for o in role_outputs
            if isinstance(o, RoleOutput)
        )

        decision = "PASS" if all_completed else "FAIL"
        self.workspace.record_decision(
            stage.id,
            decision,
            f"{sum(1 for o in role_outputs if isinstance(o, RoleOutput) and o.status=='completed')}/{len([o for o in role_outputs if isinstance(o, RoleOutput)])} 角色完成",
        )

        return all_completed

    async def formulate_question(self, stage: StageDef) -> str:
        """生成要问用户的问题"""
        return (
            f"阶段 '{stage.name}' 需要你的确认才能继续。\n"
            f"描述: {stage.description}\n"
            f"回复 'ok' 继续，或描述你需要的调整。"
        )
