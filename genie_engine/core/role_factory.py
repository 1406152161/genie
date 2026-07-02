"""角色工厂 — 从 RoleDef 创建 Role 实例。"""

import asyncio
import logging
import re
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
    """一个可执行的角色实例。"""

    def __init__(self, name: str, definition: RoleDef, workspace: Workspace):
        self.name = name
        self.defn = definition
        self.workspace = workspace
        # 优先使用 workspace state 中的全局 model
        try:
            global_model = workspace.get_state().model
        except Exception:
            global_model = None
        effective = global_model if global_model else definition.model
        self.provider = ProviderRegistry.get(effective)

    async def run(self) -> RoleOutput:
        start = time.monotonic()
        try:
            context = self._load_context()
            prompt = self._build_prompt(context)
            response = await self._call_llm(prompt)
            files_created = self._save_outputs(response.content)
            return RoleOutput(
                role_name=self.name, status="completed",
                files_created=files_created,
                duration_seconds=round(time.monotonic() - start, 2),
            )
        except Exception as exc:
            logger.error("角色 %s 执行失败: %s", self.name, exc)
            return RoleOutput(
                role_name=self.name, status="failed", error=str(exc),
                duration_seconds=round(time.monotonic() - start, 2),
            )

    def _load_context(self) -> str:
        parts = [f"# 任务上下文\n\n目标: {self.workspace.get_state().goal}"]
        for path in self.defn.input_files:
            if self.workspace.file_exists(path):
                parts.append(f"\n--- {path} ---\n{self.workspace.read_file(path)}")
        return "\n".join(parts)

    def _build_prompt(self, context: str) -> str:
        return f"""{self.defn.system_prompt}

---

{context}

---

请按上述要求执行你的任务，并输出结果。"""

    async def _call_llm(self, prompt: str) -> "ProviderResponse":
        return await self.provider.chat([Message(role="user", content=prompt)])

    def _save_outputs(self, content: str) -> list[str]:
        created: list[str] = []
        file_pattern = re.compile(r"===FILE:(.+?)===\n(.*?)(?=\n===FILE:|\Z)", re.DOTALL)
        matches = file_pattern.findall(content)
        if matches:
            for filepath, filecontent in matches:
                path = filepath.strip()
                self.workspace.write_file(path, filecontent.strip())
                created.append(path)
            logger.info("角色 %s: 创建了 %d 个文件", self.name, len(created))
        else:
            for path in self.defn.output_files:
                if "*" not in path:
                    self.workspace.write_file(path, content)
                    created.append(path)
                    break
        return created


class RoleFactory:
    def __init__(self, role_defs: dict[str, RoleDef], workspace: Workspace):
        self.defs = role_defs
        self.workspace = workspace

    def create(self, name: str) -> Role:
        if name not in self.defs:
            raise ValueError(f"未定义的角色: {name}")
        return Role(name, self.defs[name], self.workspace)