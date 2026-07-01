"""RolePack 加载器 — YAML→校验→RolePackDefinition。"""

import yaml
from pathlib import Path

from genie_engine.core.exceptions import PackLoadError
from genie_engine.schemas.rolepack import RolePackDefinition
from genie_engine.schemas.validator import SchemaValidator


class PackLoader:
    """加载并校验 RolePack YAML 文件。

    职责:
    1. 读取 YAML
    2. JSON Schema 校验
    3. 逻辑一致性校验
    4. 返回类型化的 RolePackDefinition
    """

    def __init__(self, path: Path | str):
        self.path = Path(path)
        self.validator = SchemaValidator()

    def load(self) -> RolePackDefinition:
        """加载并校验 RolePack。

        Raises:
            PackLoadError: 文件不存在、YAML 解析失败、校验失败
        """
        if not self.path.exists():
            raise PackLoadError(f"RolePack 文件不存在: {self.path}")

        try:
            raw = yaml.safe_load(self.path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            raise PackLoadError(f"YAML 解析失败: {exc}") from exc

        if not isinstance(raw, dict):
            raise PackLoadError("RolePack YAML 根节点必须是字典")

        # Schema 校验
        errors = self.validator.validate(raw)
        if errors:
            raise PackLoadError(
                f"RolePack 校验失败 ({self.path.name}):\n" + "\n".join(f"  - {e}" for e in errors)
            )

        # 转换为类型化定义
        definition = RolePackDefinition.from_dict(raw)

        # 额外校验：stage 引用的角色必须存在
        role_errors = definition.validate_stage_roles()
        if role_errors:
            raise PackLoadError(
                f"Stage 引用了未定义的角色:\n" + "\n".join(f"  - {e}" for e in role_errors)
            )

        return definition
