"""RolePack YAML Schema 校验器。"""

import json
from pathlib import Path
from typing import Any

ROLEPACK_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["name", "version", "stages", "roles"],
    "properties": {
        "name": {"type": "string", "minLength": 1},
        "version": {"type": "string", "pattern": r"^\d+\.\d+\.\d+(-[a-zA-Z0-9.]+)?$"},
        "description": {"type": "string"},
        "icon": {"type": "string"},
        "tags": {"type": "array", "items": {"type": "string"}},
        "stages": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "parallel"],
                "properties": {
                    "id": {"type": "string", "minLength": 1},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "parallel": {"type": "array", "minItems": 1, "items": {"type": "string"}},
                    "checkpoint": {"type": "string", "pattern": r"^(auto|manual|auto_timeout_\d+)$"},
                    "retry": {"type": "integer", "minimum": 0, "maximum": 10},
                    "depends_on": {"type": "array", "items": {"type": "string"}},
                },
            },
        },
        "roles": {
            "type": "object",
            "minProperties": 1,
            "additionalProperties": {
                "type": "object",
                "required": ["system_prompt"],
                "properties": {
                    "system_prompt": {"type": "string", "minLength": 10},
                    "tools": {"type": "array", "items": {"type": "string"}},
                    "file_scope": {"type": "array", "items": {"type": "string"}},
                    "input_files": {"type": "array", "items": {"type": "string"}},
                    "output_files": {"type": "array", "items": {"type": "string"}},
                    "model": {"type": "string"},
                    "autonomy": {"type": "string", "enum": ["low", "medium", "high"]},
                    "retry": {"type": "integer", "minimum": 0, "maximum": 5},
                },
            },
        },
    },
}


class SchemaValidator:
    def __init__(self) -> None:
        self._schema = ROLEPACK_SCHEMA

    def validate(self, data: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        try:
            from jsonschema import validate, ValidationError
        except ImportError:
            return self._basic_validate(data)

        try:
            validate(instance=data, schema=self._schema)
        except ValidationError as exc:
            errors.append(f"Schema 校验失败: {exc.message}")

        errors.extend(self._logic_validate(data))
        return errors

    def _basic_validate(self, data: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if not isinstance(data.get("name"), str) or not data["name"]:
            errors.append("缺少 name 字段")
        if not isinstance(data.get("stages"), list) or len(data["stages"]) == 0:
            errors.append("stages 必须是非空数组")
        if not isinstance(data.get("roles"), dict) or len(data["roles"]) == 0:
            errors.append("roles 必须是非空字典")
        return errors

    def _logic_validate(self, data: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        role_names = set(data.get("roles", {}).keys())

        for stage in data.get("stages", []):
            for role_name in stage.get("parallel", []):
                if role_name not in role_names:
                    errors.append(
                        f"Stage '{stage['id']}' 引用了未定义的角色: '{role_name}'"
                    )

        # file_scope 冲突检测 — 跳过 reviewer 和 test_runner 等验证角色
        # 因为它们的设计就是要修改 builder 的文件
        _VERIFY_ROLES = {"reviewer", "test_runner", "pack_validator", "regression_tester"}
        builder_scopes: dict[str, str] = {}
        for name, role in data.get("roles", {}).items():
            if name in _VERIFY_ROLES:
                continue  # ← 修复2: 验证角色可以和其他角色共享文件范围
            for scope in role.get("file_scope", []):
                if scope in builder_scopes and builder_scopes[scope] != name:
                    errors.append(
                        f"文件范围 '{scope}' 被多个角色声明: '{builder_scopes[scope]}' 和 '{name}'"
                    )
                builder_scopes[scope] = name

        return errors
