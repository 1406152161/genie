"""测试 schemas/rolepack.py"""

import pytest
from genie_engine.schemas.rolepack import (
    RolePackDefinition,
    StageDef,
    RoleDef,
    AutonomyLevel,
    CheckpointMode,
)


class TestRoleDef:
    def test_from_dict_minimal(self):
        raw = {"system_prompt": "You are a helpful assistant."}
        role = RoleDef.from_dict("assistant", raw)
        assert role.name == "assistant"
        assert role.system_prompt == "You are a helpful assistant."
        assert role.autonomy == AutonomyLevel.LOW
        assert role.model == "deepseek"
        assert role.retry == 1
        assert role.tools == []

    def test_from_dict_full(self):
        raw = {
            "system_prompt": "You are an architect.",
            "tools": ["file_read", "file_write"],
            "file_scope": ["backend/"],
            "input_files": [".genie/design/architecture.md"],
            "output_files": [".genie/design/api.json"],
            "model": "gpt4",
            "autonomy": "high",
            "retry": 2,
        }
        role = RoleDef.from_dict("architect", raw)
        assert role.name == "architect"
        assert role.tools == ["file_read", "file_write"]
        assert role.file_scope == ["backend/"]
        assert role.model == "gpt4"
        assert role.autonomy == AutonomyLevel.HIGH
        assert role.retry == 2


class TestStageDef:
    def test_from_dict(self):
        raw = {
            "id": "design",
            "name": "架构设计",
            "parallel": ["architect", "ux_designer"],
            "checkpoint": "auto_timeout_300",
            "retry": 1,
        }
        stage = StageDef.from_dict(raw)
        assert stage.id == "design"
        assert stage.name == "架构设计"
        assert stage.parallel == ["architect", "ux_designer"]
        assert stage.checkpoint_mode == CheckpointMode.AUTO_TIMEOUT
        assert stage.timeout_seconds == 300
        assert stage.retry == 1

    def test_checkpoint_auto(self):
        stage = StageDef(id="s1", name="t", parallel=["r1"], checkpoint="auto")
        assert stage.checkpoint_mode == CheckpointMode.AUTO
        assert stage.timeout_seconds == 0

    def test_checkpoint_manual(self):
        stage = StageDef(id="s1", name="t", parallel=["r1"], checkpoint="manual")
        assert stage.checkpoint_mode == CheckpointMode.MANUAL

    def test_checkpoint_auto_timeout_bad_format_fallback(self):
        """auto_timeout 格式异常时回退到默认 300 秒"""
        stage = StageDef(id="s1", name="t", parallel=["r1"], checkpoint="auto_timeout_bad")
        assert stage.timeout_seconds == 300


class TestRolePackDefinition:
    def test_from_dict_basic(self):
        raw = {
            "name": "Test Pack",
            "version": "1.0.0",
            "stages": [
                {"id": "s1", "name": "Stage 1", "parallel": ["r1"]}
            ],
            "roles": {
                "r1": {"system_prompt": "You do stuff."}
            },
        }
        pack = RolePackDefinition.from_dict(raw)
        assert pack.name == "Test Pack"
        assert pack.version == "1.0.0"
        assert len(pack.stages) == 1
        assert len(pack.roles) == 1

    def test_get_role_exists(self):
        pack = RolePackDefinition(
            name="Test",
            version="1.0.0",
            roles={"r1": RoleDef(name="r1", system_prompt="...")},
        )
        assert pack.get_role("r1").name == "r1"

    def test_get_role_missing_raises(self):
        pack = RolePackDefinition(name="Test", version="1.0.0")
        with pytest.raises(KeyError, match="r99"):
            pack.get_role("r99")

    def test_validate_stage_roles_all_valid(self):
        pack = RolePackDefinition(
            name="Test",
            version="1.0.0",
            stages=[StageDef(id="s1", name="t", parallel=["r1", "r2"])],
            roles={
                "r1": RoleDef(name="r1", system_prompt="..."),
                "r2": RoleDef(name="r2", system_prompt="..."),
            },
        )
        assert pack.validate_stage_roles() == []

    def test_validate_stage_roles_missing(self):
        pack = RolePackDefinition(
            name="Test",
            version="1.0.0",
            stages=[StageDef(id="s1", name="t", parallel=["r1", "r_bad"])],
            roles={"r1": RoleDef(name="r1", system_prompt="...")},
        )
        errors = pack.validate_stage_roles()
        assert len(errors) == 1
        assert "r_bad" in errors[0]
