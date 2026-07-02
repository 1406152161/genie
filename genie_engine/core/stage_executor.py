"""阶段执行器 — 按 DAG 顺序执行所有阶段。"""

import asyncio
import logging
import time

from genie_engine.core.director import Director, DirectorDecision
from genie_engine.core.role_factory import RoleFactory
from genie_engine.core.workspace import Workspace
from genie_engine.schemas.rolepack import RolePackDefinition, StageDef
from genie_engine.schemas.result import StageOutput, RoleOutput, EngineResult

logger = logging.getLogger(__name__)


class StageExecutor:
    """按定义顺序执行所有阶段。

    每个阶段内并行执行所有角色。
    每个阶段后触发 Director 检查点。
    """

    def __init__(
        self,
        definition: RolePackDefinition,
        workspace: Workspace,
    ):
        self.stages = definition.stages
        self.role_factory = RoleFactory(definition.roles, workspace)
        self.workspace = workspace
        self.director = Director(workspace)

    async def run_all(self) -> EngineResult:
        """执行所有阶段，返回最终结果。

        Q4 (断点恢复): 如果 workspace 有 resume 状态，从上次中断的阶段继续。
        Q6 (暂停/取消): 通过 CancelledError 实现优雅中断。
        """
        start_time = time.monotonic()
        stage_outputs: list[StageOutput] = []
        warnings: list[str] = []

        # Q4: 检查是否需要断点恢复
        resume_state = self.workspace.resume()
        skip_until: str | None = None
        if resume_state:
            logger.info("断点恢复: 从阶段 '%s' 继续", resume_state.current_stage)
            skip_until = resume_state.current_stage

        self.workspace.update_phase("running")

        for stage in self.stages:
            # Q4: 跳过已完成的阶段
            if skip_until and stage.id != skip_until:
                logger.info("跳过已完成阶段: %s", stage.id)
                continue
            skip_until = None

            # Q6: 检查取消
            current_state = self.workspace.get_state()
            if current_state.phase == "paused":
                # 暂停 — 保存当前状态，等待用户恢复
                self.workspace.update_phase("paused", stage.id)
                return EngineResult(
                    status="paused",
                    stages=stage_outputs,
                    warnings=warnings,
                )

            logger.info("开始阶段: %s (%s)", stage.id, stage.name)
            self.workspace.update_phase("running", stage.id)

            # 检查点
            checkpoint_decision = await self.director.checkpoint(stage)
            if checkpoint_decision == DirectorDecision.ASK_USER:
                # 留给外部处理（CLI/Web 显示问题并等待用户输入）
                warnings.append(f"阶段 '{stage.id}' 需要用户确认")
            elif checkpoint_decision == DirectorDecision.ABORT:
                return EngineResult(status="cancelled", stages=stage_outputs)

            # 执行阶段（含重试）
            stage_result = await self._execute_stage_with_retry(stage)
            stage_outputs.append(stage_result)

            if stage_result.status == "failed" and stage.retry == 0:
                warnings.append(f"阶段 '{stage.id}' 失败且无重试")

        self.workspace.update_phase("completed")

        return EngineResult(
            status="completed",
            goal=self.workspace.get_state().goal,
            output_dir=str(self.workspace.base),
            stages=stage_outputs,
            total_duration_seconds=round(time.monotonic() - start_time, 2),
            warnings=warnings,
            started_at=self.workspace.get_state().started_at,
        )

    async def _execute_stage_with_retry(self, stage: StageDef) -> StageOutput:
        """执行一个阶段，含重试逻辑"""
        start = time.monotonic()
        last_error: str = ""

        for attempt in range(stage.retry + 1):
            if attempt > 0:
                logger.info("阶段 %s 重试 %d/%d", stage.id, attempt, stage.retry)

            try:
                role_outputs = await self._execute_stage_roles(stage)

                # Director 评估
                passed = await self.director.evaluate(stage, role_outputs)

                if passed:
                    return StageOutput(
                        stage_id=stage.id,
                        status="completed",
                        roles=[o for o in role_outputs if isinstance(o, RoleOutput)],
                        duration_seconds=round(time.monotonic() - start, 2),
                        retries=attempt,
                    )
                else:
                    last_error = f"Director 评估未通过 (attempt {attempt + 1})"

            except asyncio.CancelledError:
                logger.info("阶段 %s 被取消", stage.id)
                return StageOutput(stage_id=stage.id, status="cancelled")
            except Exception as exc:
                last_error = str(exc)
                logger.warning("阶段 %s 失败 (attempt %d): %s", stage.id, attempt + 1, exc)

        # 所有重试都用完了
        return StageOutput(
            stage_id=stage.id,
            status="failed",
            duration_seconds=round(time.monotonic() - start, 2),
            retries=stage.retry,
        )

    async def _execute_stage_roles(self, stage: StageDef) -> list[RoleOutput | Exception]:
        """并行执行一个阶段内的所有角色"""
        roles = [self.role_factory.create(name) for name in stage.parallel]

        logger.info(
            "阶段 %s: 并行执行 %d 个角色: %s",
            stage.id,
            len(roles),
            [r.name for r in roles],
        )

        results = await asyncio.gather(
            *[role.run() for role in roles],
            return_exceptions=True,
        )

        return list(results)
