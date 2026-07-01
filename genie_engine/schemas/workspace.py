"""Workspace 状态数据定义。"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RunState:
    """一次 Run 的全局状态（对应 .genie/state.json）"""
    goal: str = ""
    model: str = "deepseek"
    budget: float | None = None
    phase: str = "init"                     # init | running | paused | completed | failed | cancelled
    current_stage: str = ""                 # 当前正在执行的阶段 id
    started_at: str = ""
    updated_at: str = ""
    stages: dict[str, Any] = field(default_factory=dict)
    decisions: list[dict[str, Any]] = field(default_factory=list)  # 记录每次决策（供 Q7 复用）
    cost: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "model": self.model,
            "budget": self.budget,
            "phase": self.phase,
            "current_stage": self.current_stage,
            "started_at": self.started_at,
            "updated_at": self.updated_at,
            "stages": self.stages,
            "decisions": self.decisions,
            "cost": self.cost,
            "warnings": self.warnings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RunState":
        return cls(
            goal=data.get("goal", ""),
            model=data.get("model", "deepseek"),
            budget=data.get("budget"),
            phase=data.get("phase", "init"),
            current_stage=data.get("current_stage", ""),
            started_at=data.get("started_at", ""),
            updated_at=data.get("updated_at", ""),
            stages=data.get("stages", {}),
            decisions=data.get("decisions", []),
            cost=data.get("cost", {}),
            warnings=data.get("warnings", []),
        )


@dataclass
class SnapshotInfo:
    """断点恢复快照信息（Q4：用户选择继续时读取）"""
    run_id: str = ""
    phase: str = ""
    current_stage: str = ""
    completed_stages: list[str] = field(default_factory=list)
    can_resume: bool = False
    resume_from: str = ""  # 从哪个 stage 开始
