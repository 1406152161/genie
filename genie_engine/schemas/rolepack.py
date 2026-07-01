"""RolePack 核心数据定义 — 零依赖，纯 dataclass。"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AutonomyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CheckpointMode(str, Enum):
    AUTO = "auto"
    MANUAL = "manual"
    AUTO_TIMEOUT = "auto_timeout"


@dataclass
class RoleDef:
    name: str
    system_prompt: str
    tools: list[str] = field(default_factory=list)
    file_scope: list[str] = field(default_factory=list)
    input_files: list[str] = field(default_factory=list)
    output_files: list[str] = field(default_factory=list)
    model: str = "deepseek"
    autonomy: AutonomyLevel = AutonomyLevel.LOW
    retry: int = 1

    @classmethod
    def from_dict(cls, name: str, raw: dict[str, Any]) -> "RoleDef":
        return cls(
            name=name,
            system_prompt=raw.get("system_prompt", ""),
            tools=raw.get("tools", []),
            file_scope=raw.get("file_scope", []),
            input_files=raw.get("input_files", []),
            output_files=raw.get("output_files", []),
            model=raw.get("model", "deepseek"),
            autonomy=AutonomyLevel(raw.get("autonomy", "low")),
            retry=raw.get("retry", 1),
        )


@dataclass
class StageDef:
    id: str
    name: str
    description: str = ""
    parallel: list[str] = field(default_factory=list)
    checkpoint: str = "auto"
    retry: int = 0
    depends_on: list[str] = field(default_factory=list)

    @property
    def checkpoint_mode(self) -> CheckpointMode:
        if self.checkpoint == "auto":
            return CheckpointMode.AUTO
        if self.checkpoint == "manual":
            return CheckpointMode.MANUAL
        if self.checkpoint.startswith("auto_timeout"):
            return CheckpointMode.AUTO_TIMEOUT
        return CheckpointMode.AUTO

    @property
    def timeout_seconds(self) -> int:
        if self.checkpoint.startswith("auto_timeout"):
            try:
                return int(self.checkpoint.split("_")[-1])
            except (ValueError, IndexError):
                return 300
        return 0

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "StageDef":
        return cls(
            id=raw.get("id", ""),
            name=raw.get("name", ""),
            description=raw.get("description", ""),
            parallel=raw.get("parallel", []),
            checkpoint=raw.get("checkpoint", "auto"),
            retry=raw.get("retry", 0),
            depends_on=raw.get("depends_on", []),
        )


@dataclass
class RolePackDefinition:
    name: str
    version: str
    description: str = ""           # ← 修复1: 默认空字符串
    icon: str = "📦"
    tags: list[str] = field(default_factory=list)
    stages: list[StageDef] = field(default_factory=list)
    roles: dict[str, RoleDef] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "RolePackDefinition":
        stages = [StageDef.from_dict(s) for s in raw.get("stages", [])]
        roles = {
            name: RoleDef.from_dict(name, rdef)
            for name, rdef in raw.get("roles", {}).items()
        }
        return cls(
            name=raw.get("name", ""),
            version=raw.get("version", "0.1.0"),
            description=raw.get("description", ""),
            icon=raw.get("icon", "📦"),
            tags=raw.get("tags", []),
            stages=stages,
            roles=roles,
        )

    def get_role(self, name: str) -> RoleDef:
        if name not in self.roles:
            raise KeyError(f"角色 '{name}' 未在 RolePack '{self.name}' 中定义")
        return self.roles[name]

    def validate_stage_roles(self) -> list[str]:
        missing: list[str] = []
        for stage in self.stages:
            for role_name in stage.parallel:
                if role_name not in self.roles:
                    missing.append(f"stage.{stage.id}: 角色 '{role_name}' 未定义")
        return missing
