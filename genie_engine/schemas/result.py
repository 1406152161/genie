"""运行结果数据定义 — 引擎执行后的输出结构。"""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class CostRecord:
    """单次 LLM 调用成本记录"""
    provider: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    timestamp: str = ""


@dataclass
class RoleOutput:
    """单个角色的执行结果"""
    role_name: str
    status: str              # completed | failed | skipped
    files_created: list[str] = field(default_factory=list)
    error: str | None = None
    duration_seconds: float = 0.0


@dataclass
class StageOutput:
    """单个阶段的执行结果"""
    stage_id: str
    status: str              # completed | failed | skipped | aborted
    roles: list[RoleOutput] = field(default_factory=list)
    duration_seconds: float = 0.0
    retries: int = 0


@dataclass
class CostEstimate:
    """运行前成本预估"""
    model: str
    estimated_calls: int
    estimated_cost_usd: float
    worst_case_usd: float


@dataclass
class EngineResult:
    """GenieEngine.execute() 的返回值"""
    status: str              # completed | failed | aborted | cancelled
    goal: str = ""
    output_dir: str = ""
    summary: str = ""
    stages: list[StageOutput] = field(default_factory=list)
    total_cost_usd: float = 0.0
    total_duration_seconds: float = 0.0
    warnings: list[str] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""

    @property
    def is_success(self) -> bool:
        return self.status == "completed"


@dataclass
class PipelineResult:
    """多 RolePack 串联的执行结果"""
    steps: list[EngineResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(s.is_success for s in self.steps)

    @property
    def total_cost_usd(self) -> float:
        return sum(s.total_cost_usd for s in self.steps)
