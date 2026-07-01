"""测试 schemas/validator.py"""

import pytest
from genie_engine.schemas.validator import SchemaValidator


class TestSchemaValidator:
    def test_valid_rolepack(self):
        """合法的 RolePack 定义应该通过校验"""
        data = {
            "name": "Test Pack",
            "version": "1.0.0",
            "stages": [{"id": "s1", "parallel": ["r1"]}],
            "roles": {"r1": {"system_prompt": "You are a helpful test role."}},
        }
        validator = SchemaValidator()
        errors = validator.validate(data)
        assert errors == []

    def test_missing_name(self):
        data = {
            "stages": [{"id": "s1", "parallel": ["r1"]}],
            "roles": {"r1": {"system_prompt": "..."}},
        }
        validator = SchemaValidator()
        errors = validator.validate(data)
        assert len(errors) > 0

    def test_missing_stages(self):
        data = {
            "name": "Test",
            "version": "1.0.0",
            "roles": {"r1": {"system_prompt": "..."}},
        }
        validator = SchemaValidator()
        errors = validator.validate(data)
        assert len(errors) > 0

    def test_missing_roles(self):
        data = {
            "name": "Test",
            "version": "1.0.0",
            "stages": [{"id": "s1", "parallel": ["r1"]}],
        }
        validator = SchemaValidator()
        errors = validator.validate(data)
        assert len(errors) > 0

    def test_stage_references_undefined_role(self):
        data = {
            "name": "Test",
            "version": "1.0.0",
            "stages": [{"id": "s1", "parallel": ["nonexistent_role"]}],
            "roles": {"r1": {"system_prompt": "..."}},
        }
        validator = SchemaValidator()
        errors = validator.validate(data)
        assert any("nonexistent_role" in e for e in errors)

    def test_file_scope_conflict(self):
        data = {
            "name": "Test",
            "version": "1.0.0",
            "stages": [{"id": "s1", "parallel": ["r1", "r2"]}],
            "roles": {
                "r1": {"system_prompt": "...", "file_scope": ["backend/"]},
                "r2": {"system_prompt": "...", "file_scope": ["backend/"]},
            },
        }
        validator = SchemaValidator()
        errors = validator.validate(data)
        assert any("backend/" in e for e in errors)

    def test_actual_code_rolepack_passes(self):
        """验证我们自己的 code.rolepack.yaml 能通过校验"""
        import yaml
        from pathlib import Path

        pack_path = Path(__file__).parent.parent / "rolepacks" / "code.rolepack.yaml"
        data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))

        validator = SchemaValidator()
        errors = validator.validate(data)
        assert errors == [], f"code.rolepack.yaml 校验失败: {errors}"

    def test_actual_pack_rolepack_passes(self):
        """验证我们自己的 pack.rolepack.yaml 能通过校验"""
        import yaml
        from pathlib import Path

        pack_path = Path(__file__).parent.parent / "rolepacks" / "pack.rolepack.yaml"
        data = yaml.safe_load(pack_path.read_text(encoding="utf-8"))

        validator = SchemaValidator()
        errors = validator.validate(data)
        assert errors == [], f"pack.rolepack.yaml 校验失败: {errors}"
