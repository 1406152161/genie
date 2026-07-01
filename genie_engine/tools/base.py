"""工具抽象基类 + 注册表"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from genie_engine.sandbox.scope import FileScope


@dataclass
class ToolResult:
    success: bool
    data: str
    error: str = ""


class Tool(ABC):
    """角色可用的工具抽象基类"""
    name: str = ""
    description: str = ""

    @abstractmethod
    async def execute(self, params: dict[str, Any], scope: FileScope) -> ToolResult: ...


class ToolRegistry:
    """工具注册表 — 按名称获取工具实例"""
    _tools: dict[str, Tool] = {}

    @classmethod
    def register(cls, tool: Tool) -> None:
        cls._tools[tool.name] = tool

    @classmethod
    def get(cls, name: str) -> Tool:
        if name not in cls._tools:
            raise ValueError(f"未注册的工具: {name}")
        return cls._tools[name]

    @classmethod
    def get_many(cls, names: list[str]) -> list[Tool]:
        return [cls._tools[n] for n in names if n in cls._tools]

    @classmethod
    def list_all(cls) -> list[str]:
        return list(cls._tools.keys())
