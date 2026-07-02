"""共享工作空间 — 角色间唯一通信媒介。

目录结构:
    .genie/
    ├── state.json          ← 全局状态
    ├── research/           ← Researcher 产出
    ├── analysis/           ← Analyst 产出
    ├── design/             ← Designer 产出
    ├── review/             ← Reviewer 产出
    ├── qa/                 ← Tester 产出
    └── decisions/          ← Director 决策记录 (Q7: 决策复用)
"""

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from genie_engine.schemas.workspace import RunState
from genie_engine.core.exceptions import WorkspaceError


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Workspace:
    """共享文件系统工作空间。

    所有角色通过此对象读写文件。
    Director 通过此对象管理全局状态。
    """

    def __init__(self, base_dir: Path | str | None = None):
        if base_dir is None:
            base_dir = Path.cwd() / "genie_workspace"
        self.base = Path(base_dir)
        self.genie_dir = self.base / ".genie"

    # ─── 初始化 ───

    def init(self, goal: str, model: str = "mock", budget: float | None = None) -> None:
        """初始化一次新的 Run"""
        if self.genie_dir.exists():
            raise WorkspaceError(
                f"工作空间已存在: {self.genie_dir}。"
                f"请先清理或使用 --resume 恢复。"
            )
        self._ensure_dirs()
        state = RunState(
            goal=goal,
            model=model,
            budget=budget,
            phase="init",
            started_at=_utcnow(),
            updated_at=_utcnow(),
        )
        self.write_state(state)

    def resume(self) -> RunState | None:
        """恢复上一次 Run 的状态 (Q4: 断点恢复)"""
        state_path = self.genie_dir / "state.json"
        if not state_path.exists():
            return None
        data = json.loads(state_path.read_text(encoding="utf-8"))
        state = RunState.from_dict(data)
        if state.phase in ("completed", "failed", "cancelled"):
            return None  # 已完成的不恢复
        return state

    # ─── 状态管理 ───

    def get_state(self) -> RunState:
        """读取当前运行状态"""
        state_path = self.genie_dir / "state.json"
        if not state_path.exists():
            raise WorkspaceError("工作空间未初始化，请先调用 init()")
        return RunState.from_dict(json.loads(state_path.read_text(encoding="utf-8")))

    def write_state(self, state: RunState) -> None:
        """写入运行状态"""
        state.updated_at = _utcnow()
        state_path = self.genie_dir / "state.json"
        state_path.write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def update_phase(self, phase: str, current_stage: str = "") -> None:
        """更新当前阶段"""
        state = self.get_state()
        state.phase = phase
        state.current_stage = current_stage
        self.write_state(state)

    def record_decision(self, stage_id: str, decision: str, reason: str) -> None:
        """记录 Director 的决策 (Q7: 供后续 Run 复用)"""
        state = self.get_state()
        state.decisions.append({
            "stage": stage_id,
            "decision": decision,
            "reason": reason,
            "timestamp": _utcnow(),
        })
        # 只保留最近 50 条决策
        state.decisions = state.decisions[-50:]
        self.write_state(state)

    def get_decisions(self) -> list[dict[str, Any]]:
        """获取历史决策 (Q7: 新 Run 优先复用已有决策)"""
        state = self.get_state()
        return state.decisions

    # ─── 文件操作 ───

    def write_file(self, relative_path: str | Path, content: str) -> Path:
        """写入文件到工作空间。受 sandbox 约束。"""
        target = self.base / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target

    def read_file(self, relative_path: str | Path) -> str:
        """读取工作空间中的文件"""
        target = self.base / relative_path
        if not target.exists():
            raise WorkspaceError(f"文件不存在: {relative_path}")
        return target.read_text(encoding="utf-8")

    def file_exists(self, relative_path: str | Path) -> bool:
        return (self.base / relative_path).exists()

    # ─── 清理 ───

    def cleanup(self) -> None:
        """清理整个工作空间"""
        if self.genie_dir.exists():
            shutil.rmtree(self.genie_dir)

    def _ensure_dirs(self) -> None:
        """确保所有子目录存在"""
        dirs = ["research", "analysis", "design", "review", "qa", "decisions"]
        for d in dirs:
            (self.genie_dir / d).mkdir(parents=True, exist_ok=True)
