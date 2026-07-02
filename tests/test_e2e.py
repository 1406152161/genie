"""端到端测试 — 验证完整项目生成"""

import pytest
from pathlib import Path

from genie_engine.core.engine import GenieEngine
from genie_engine.core.workspace import Workspace


class TestEndToEnd:
    @pytest.mark.asyncio
    async def test_code_rolepack_generates_project(self, tmp_path):
        """跑 code.rolepack，验证生成了真实项目文件"""
        pack_path = Path(__file__).parent.parent / "rolepacks" / "code.rolepack.yaml"
        engine = GenieEngine(pack_path)
        engine.workspace = Workspace(tmp_path / "e2e")

        result = await engine.execute("做一个小说写作AI工具", model="mock")

        assert result.status == "completed"
        assert len(result.stages) == 4

        # 验证 stage 名称
        stage_ids = [s.stage_id for s in result.stages]
        assert "understand" in stage_ids
        assert "design" in stage_ids
        assert "build" in stage_ids
        assert "verify" in stage_ids

        # 验证产出目录中有文件
        ws = engine.workspace
        all_files = list(ws.base.rglob("*"))

        # 至少有文件被创建（不是空目录）
        py_files = [f for f in all_files if f.suffix == ".py" and f.is_file()]
        assert len(py_files) > 0, f"应该有 Python 文件被生成，但只有: {all_files}"

        # 应该有 .genie 内部状态
        assert (ws.genie_dir / "state.json").exists()
        assert (ws.genie_dir / "research" / "report.json").exists()

    @pytest.mark.asyncio
    async def test_mock_backend_creates_project_files(self, tmp_path):
        """模拟 Backend Builder 产出，验证多文件保存"""
        from genie_engine.core.role_factory import Role
        from genie_engine.schemas.rolepack import RoleDef

        ws = Workspace(tmp_path / "backend_test")
        ws.init("test")

        role = Role(
            "backend",
            RoleDef(
                name="backend",
                system_prompt="你是后端工程师...",
                output_files=["backend/**"],
                model="mock",
            ),
            ws,
        )

        output = await role.run()

        assert output.status == "completed"
        # Backend builder 应该创建多个文件
        assert len(output.files_created) >= 3

        # 验证主要文件存在
        assert ws.file_exists("backend/main.py")
        assert ws.file_exists("backend/requirements.txt")
        assert ws.file_exists("backend/app/models/novel.py")

        # 验证文件内容有意义
        main_content = ws.read_file("backend/main.py")
        assert "FastAPI" in main_content
        assert "uvicorn" in main_content

    @pytest.mark.asyncio
    async def test_mock_frontend_creates_project_files(self, tmp_path):
        """模拟 Frontend Builder 产出，验证多文件保存"""
        from genie_engine.core.role_factory import Role
        from genie_engine.schemas.rolepack import RoleDef

        ws = Workspace(tmp_path / "frontend_test")
        ws.init("test")

        role = Role(
            "frontend",
            RoleDef(
                name="frontend",
                system_prompt="你是前端工程师...",
                output_files=["frontend/**"],
                model="mock",
            ),
            ws,
        )

        output = await role.run()

        assert output.status == "completed"
        assert len(output.files_created) >= 2
        assert ws.file_exists("frontend/src/App.tsx")
        assert ws.file_exists("frontend/vite.config.ts")
