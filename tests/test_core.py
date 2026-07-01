"""测试 core 层 — pack_loader, workspace, role_factory, director, engine"""

import json
import pytest
import tempfile
from pathlib import Path

from genie_engine.core.pack_loader import PackLoader
from genie_engine.core.workspace import Workspace
from genie_engine.core.role_factory import RoleFactory, Role
from genie_engine.core.director import Director, DirectorDecision
from genie_engine.core.engine import GenieEngine
from genie_engine.core.exceptions import PackLoadError, WorkspaceError
from genie_engine.schemas.rolepack import RolePackDefinition, StageDef, RoleDef, AutonomyLevel


# ─── PackLoader Tests ───

class TestPackLoader:
    def test_load_code_rolepack(self):
        """加载内置 code.rolepack.yaml"""
        loader = PackLoader(Path(__file__).parent.parent / "rolepacks" / "code.rolepack.yaml")
        definition = loader.load()
        assert isinstance(definition, RolePackDefinition)
        assert definition.name == "Genie Code"
        assert len(definition.stages) == 4
        assert len(definition.roles) == 12

    def test_load_pack_rolepack(self):
        """加载内置 pack.rolepack.yaml"""
        loader = PackLoader(Path(__file__).parent.parent / "rolepacks" / "pack.rolepack.yaml")
        definition = loader.load()
        assert definition.name == "Genie Pack Creator"
        assert len(definition.stages) == 3
        assert "regression_tester" in definition.roles

    def test_load_nonexistent_raises(self):
        loader = PackLoader("nonexistent.rolepack.yaml")
        with pytest.raises(PackLoadError, match="不存在"):
            loader.load()

    def test_load_missing_stage_roles(self):
        """Stage 引用了未定义的角色"""
        raw = {
            "name": "Test",
            "version": "1.0.0",
            "stages": [{"id": "s1", "parallel": ["ghost_role"]}],
            "roles": {"r1": {"system_prompt": "You are helpful."}},
        }
        import yaml
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(raw, f)
            tmp_path = f.name
        try:
            loader = PackLoader(tmp_path)
            with pytest.raises(PackLoadError, match="ghost_role"):
                loader.load()
        finally:
            Path(tmp_path).unlink()


# ─── Workspace Tests ───

class TestWorkspace:
    def test_init_and_state(self, tmp_path):
        ws = Workspace(tmp_path / "test_ws")
        ws.init("做一个测试项目", model="mock")

        state = ws.get_state()
        assert state.goal == "做一个测试项目"
        assert state.model == "mock"
        assert state.phase == "init"

    def test_init_twice_raises(self, tmp_path):
        ws = Workspace(tmp_path / "test_ws2")
        ws.init("goal")
        with pytest.raises(WorkspaceError, match="已存在"):
            ws.init("goal2")

    def test_write_and_read_file(self, tmp_path):
        ws = Workspace(tmp_path / "test_ws3")
        ws.init("test")
        ws.write_file("data/output.json", '{"key": "value"}')
        assert ws.file_exists("data/output.json")
        content = ws.read_file("data/output.json")
        assert "key" in content

    def test_record_and_get_decisions(self, tmp_path):
        ws = Workspace(tmp_path / "test_ws4")
        ws.init("test")
        ws.record_decision("design", "PASS", "架构合理")
        decisions = ws.get_decisions()
        assert len(decisions) == 1
        assert decisions[0]["stage"] == "design"

    def test_resume_nonexistent(self, tmp_path):
        ws = Workspace(tmp_path / "nonexistent")
        assert ws.resume() is None


# ─── RoleFactory Tests ───

class TestRoleFactory:
    def test_create_role(self, tmp_path):
        ws = Workspace(tmp_path / "test_rf")
        ws.init("test")
        defs = {
            "researcher": RoleDef(
                name="researcher",
                system_prompt="You research.",
                model="mock",
            )
        }
        factory = RoleFactory(defs, ws)
        role = factory.create("researcher")
        assert isinstance(role, Role)
        assert role.name == "researcher"

    def test_create_unknown_role_raises(self, tmp_path):
        ws = Workspace(tmp_path / "test_rf2")
        ws.init("test")
        factory = RoleFactory({}, ws)
        with pytest.raises(ValueError, match="unknown"):
            factory.create("unknown")

    @pytest.mark.asyncio
    async def test_role_run(self, tmp_path):
        ws = Workspace(tmp_path / "test_rf3")
        ws.init("test task")
        role = Role(
            "researcher",
            RoleDef(
                name="researcher",
                system_prompt="Reply with JSON.",
                output_files=[".genie/research/report.json"],
                model="mock",
            ),
            ws,
        )
        output = await role.run()
        assert output.status == "completed"
        assert output.role_name == "researcher"
        assert ws.file_exists(".genie/research/report.json")


# ─── Director Tests ───

class TestDirector:

    @pytest.mark.asyncio
    async def test_checkpoint_auto_passes(self, tmp_path):
        ws = Workspace(tmp_path / "test_dir2")
        ws.init("test")
        director = Director(ws)
        stage = StageDef(id="s1", name="t", parallel=["r1"], checkpoint="auto")
        decision = await director.checkpoint(stage)
        assert decision == DirectorDecision.PASS

    @pytest.mark.asyncio
    async def test_checkpoint_manual_asks_user(self, tmp_path):
        ws = Workspace(tmp_path / "test_dir3")
        ws.init("test")
        director = Director(ws)
        stage = StageDef(id="s1", name="t", parallel=["r1"], checkpoint="manual")
        decision = await director.checkpoint(stage)
        assert decision == DirectorDecision.ASK_USER

    @pytest.mark.asyncio
    async def test_evaluate_all_completed_passes(self, tmp_path):
        ws = Workspace(tmp_path / "test_dir4")
        ws.init("test")
        director = Director(ws)
        stage = StageDef(id="s1", name="t", parallel=["r1"])
        from genie_engine.schemas.result import RoleOutput
        outputs = [
            RoleOutput(role_name="r1", status="completed"),
            RoleOutput(role_name="r2", status="completed"),
        ]
        result = await director.evaluate(stage, outputs)
        assert result is True


# ─── GenieEngine Tests ───

class TestGenieEngine:
    @pytest.mark.asyncio
    async def test_execute_code_rolepack(self, tmp_path):
        """端到端: 用 code.rolepack + mock provider 跑一次"""
        pack_path = Path(__file__).parent.parent / "rolepacks" / "code.rolepack.yaml"
        engine = GenieEngine(pack_path)
        # 使用临时工作空间
        engine.workspace = Workspace(tmp_path / "e2e_test")
        result = await engine.execute("做一个测试项目", model="mock")
        assert result.status == "completed"
        assert len(result.stages) == 4  # code.rolepack 有4个阶段
