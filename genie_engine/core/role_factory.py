"""角色工厂 — 从 RoleDef 创建 Role 实例。"""

import asyncio
import logging
import time
from pathlib import Path

from genie_engine.core.workspace import Workspace
from genie_engine.providers.base import LLMProvider, Message
from genie_engine.providers.registry import ProviderRegistry
from genie_engine.schemas.rolepack import RoleDef
from genie_engine.schemas.result import RoleOutput
from genie_engine.core.exceptions import RoleExecutionError

logger = logging.getLogger(__name__)


class Role:
    """一个可执行的角色实例。

    封装了角色的 System Prompt、输入上下文读取、LLM 调用、产出保存。
    """

    def __init__(self, name: str, definition: RoleDef, workspace: Workspace):
        self.name = name
        self.defn = definition
        self.workspace = workspace
        self.provider = ProviderRegistry.get(definition.model)

    async def run(self) -> RoleOutput:
        """执行此角色。

        流程: 读输入 → 调LLM → 写输出
        """
        start = time.monotonic()
        try:
            context = self._load_context()
            prompt = self._build_prompt(context)
            response = await self._call_llm(prompt)
            self._save_outputs(response.content)

            return RoleOutput(
                role_name=self.name,
                status="completed",
                files_created=self.defn.output_files,
                duration_seconds=round(time.monotonic() - start, 2),
            )
        except Exception as exc:
            logger.error("角色 %s 执行失败: %s", self.name, exc)
            return RoleOutput(
                role_name=self.name,
                status="failed",
                error=str(exc),
                duration_seconds=round(time.monotonic() - start, 2),
            )

    def _load_context(self) -> str:
        """从工作空间读取输入文件内容"""
        parts = [f"# 任务上下文\n\n目标: {self.workspace.get_state().goal}"]
        for path in self.defn.input_files:
            if self.workspace.file_exists(path):
                content = self.workspace.read_file(path)
                parts.append(f"\n--- {path} ---\n{content}")
        return "\n".join(parts)

    def _build_prompt(self, context: str) -> str:
        """构建发送给 LLM 的完整 prompt"""
        return f"""{self.defn.system_prompt}

---

{context}

---

请按上述要求执行你的任务，并输出结果。"""

    async def _call_llm(self, prompt: str) -> "ProviderResponse":
        """调用 LLM"""
        messages = [Message(role="user", content=prompt)]
        return await self.provider.chat(messages)

    def _save_outputs(self, content: str) -> None:
        """保存产出到工作空间"""
        for path in self.defn.output_files:
            self.workspace.write_file(path, content)


class RoleFactory:
    """从 RoleDef 创建 Role 实例"""

    def __init__(self, role_defs: dict[str, RoleDef], workspace: Workspace):
        self.defs = role_defs
        self.workspace = workspace

    def create(self, name: str) -> Role:
        if name not in self.defs:
            raise ValueError(f"未定义的角色: {name}")
        return Role(name, self.defs[name], self.workspace)
