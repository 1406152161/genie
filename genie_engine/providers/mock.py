"""Mock Provider — 返回预设数据，Builder角色产出完整项目"""

import json
from genie_engine.providers.base import LLMProvider, Message, ProviderResponse, ToolDef


class MockProvider(LLMProvider):
    """返回预设的模拟数据。Builder角色产出真实项目文件。"""

    async def chat(
        self, messages: list[Message], tools: list[ToolDef] | None = None, **kwargs
    ) -> ProviderResponse:
        system = messages[0].content if messages else ""
        last_msg = messages[-1].content if messages else ""

        # Director 评估
        if "PASS" in last_msg.upper() or "阶段产出" in last_msg:
            return ProviderResponse(content="PASS", tokens_in=100, tokens_out=5, model="mock")

        # Researcher
        if "研究员" in system or "调研" in last_msg:
            return self._mock_research()

        # Analyst
        if "需求分析" in system or "功能清单" in last_msg:
            return self._mock_features()

        # Architect
        if "架构师" in system or "系统架构" in system:
            return self._mock_architecture()

        # UX Designer
        if "UX" in system or "页面结构" in system:
            return self._mock_ux()

        # Backend Builder — 真写文件
        if "后端工程师" in system or "backend" in system.lower():
            return self._mock_backend_project()

        # Frontend Builder — 真写文件
        if "前端工程师" in system or "frontend" in system.lower():
            return self._mock_frontend_project()

        # Doc Writer
        if "文档工程师" in system or "doc_writer" in system:
            return self._mock_readme()

        # Reviewer / Test Runner
        if "审查" in system or "reviewer" in system:
            return ProviderResponse(content="PASS: code style ok", tokens_in=200, tokens_out=20, model="mock")
        if "测试执行" in system or "test_runner" in system:
            return ProviderResponse(content="pytest: 8 passed", tokens_in=200, tokens_out=15, model="mock")

        # Default
        return ProviderResponse(content=json.dumps({"status": "ok"}), tokens_in=50, tokens_out=20, model="mock")

    def _mock_research(self) -> ProviderResponse:
        return ProviderResponse(content=json.dumps({
            "competitors": [{"name": "OpenNovel", "strength": "多Agent", "weakness": "部署难", "stars": 1200}],
            "tech_options": [{"stack": "FastAPI+React", "pros": ["成熟", "快速"], "cons": [], "score": 9}],
            "recommendation": "FastAPI+React+SQLite+ChromaDB",
        }, ensure_ascii=False), tokens_in=200, tokens_out=300, model="mock")

    def _mock_features(self) -> ProviderResponse:
        return ProviderResponse(content=json.dumps({
            "mvp_scope": "Web端小说写作助手",
            "user_journey": "选题材→输创意→规划大纲→写作→续写→导出",
            "features": [
                {"id": "F1", "name": "题材模板", "priority": "P0", "effort": "S"},
                {"id": "F2", "name": "AI大纲规划", "priority": "P0", "effort": "L"},
                {"id": "F3", "name": "章节写作", "priority": "P0", "effort": "L"},
                {"id": "F4", "name": "人物管理", "priority": "P1", "effort": "M"},
                {"id": "F5", "name": "导出MD", "priority": "P1", "effort": "S"},
            ],
        }, ensure_ascii=False), tokens_in=200, tokens_out=250, model="mock")

    def _mock_architecture(self) -> ProviderResponse:
        return ProviderResponse(content=json.dumps({
            "tech_stack": "FastAPI + React + TypeScript + SQLite + ChromaDB",
            "backend": "FastAPI 3层: api/ services/ models/",
            "frontend": "React + Vite + TypeScript, 4 pages",
            "database": "SQLite (dev) / PostgreSQL (prod)",
            "api_endpoints": [
                "POST /api/novels", "GET /api/novels", "GET /api/novels/:id",
                "POST /api/novels/:id/chapters", "GET /api/novels/:id/export",
            ],
        }, ensure_ascii=False), tokens_in=200, tokens_out=250, model="mock")

    def _mock_ux(self) -> ProviderResponse:
        return ProviderResponse(content=json.dumps({
            "pages": [
                {"route": "/", "name": "HomePage", "desc": "题材选择+创意输入"},
                {"route": "/novel/:id", "name": "NovelPage", "desc": "写作工作台"},
                {"route": "/novel/:id/outline", "name": "OutlinePage", "desc": "大纲管理"},
                {"route": "/novel/:id/characters", "name": "CharactersPage", "desc": "人物管理"},
            ],
        }, ensure_ascii=False), tokens_in=200, tokens_out=200, model="mock")

    # ─── Builder 产出真实项目文件 ───

    def _mock_backend_project(self) -> ProviderResponse:
        """模拟 Backend Builder 产出完整后端项目"""
        files = {
            "backend/main.py": (
                "from fastapi import FastAPI\n"
                "from fastapi.middleware.cors import CORSMiddleware\n\n"
                "app = FastAPI(title='Novel Writer API')\n"
                "app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['*'], allow_headers=['*'])\n\n"
                "@app.get('/api/health')\n"
                "async def health():\n"
                "    return {'status': 'ok'}\n\n"
                "if __name__ == '__main__':\n"
                "    import uvicorn\n"
                "    uvicorn.run(app, host='0.0.0.0', port=8000)\n"
            ),
            "backend/requirements.txt": (
                "fastapi>=0.115\nuvicorn>=0.30\nsqlalchemy>=2.0\nchromadb>=0.5\npyyaml>=6.0\n"
            ),
            "backend/app/__init__.py": "# app package\n",
            "backend/app/api/__init__.py": "# api routes\n",
            "backend/app/api/novels.py": (
                "from fastapi import APIRouter\n\n"
                "router = APIRouter(prefix='/api/novels', tags=['novels'])\n\n"
                "@router.post('')\n"
                "async def create_novel():\n"
                "    return {'id': 'mock-1', 'status': 'created'}\n\n"
                "@router.get('')\n"
                "async def list_novels():\n"
                "    return []\n"
            ),
            "backend/app/models/__init__.py": "from .novel import Novel, Chapter\n",
            "backend/app/models/novel.py": (
                "from sqlalchemy import Column, String, Integer, Text\n"
                "from sqlalchemy.ext.declarative import declarative_base\n\n"
                "Base = declarative_base()\n\n"
                "class Novel(Base):\n"
                "    __tablename__ = 'novels'\n"
                "    id = Column(String, primary_key=True)\n"
                "    title = Column(String(256))\n"
                "    premise = Column(Text)\n"
                "    status = Column(String(16), default='pending')\n\n"
                "class Chapter(Base):\n"
                "    __tablename__ = 'chapters'\n"
                "    id = Column(String, primary_key=True)\n"
                "    novel_id = Column(String)\n"
                "    index = Column(Integer)\n"
                "    content = Column(Text)\n"
            ),
            "backend/.env.example": "DATABASE_URL=sqlite:///./novel_writer.db\n",
        }
        # 使用分隔符格式，让 Role 能解析并创建多个文件
        output_parts = []
        for path, content in files.items():
            output_parts.append(f"===FILE:{path}===\n{content}")
        return ProviderResponse(
            content="\n".join(output_parts),
            tokens_in=300, tokens_out=len("\n".join(output_parts)) // 4, model="mock",
        )

    def _mock_frontend_project(self) -> ProviderResponse:
        """模拟 Frontend Builder 产出完整前端项目"""
        files = {
            "frontend/src/App.tsx": (
                'import { BrowserRouter, Routes, Route, Link } from "react-router-dom";\n'
                'import HomePage from "./pages/HomePage";\n'
                'import NovelPage from "./pages/NovelPage";\n\n'
                'export default function App() {\n'
                '  return <BrowserRouter><Routes>\n'
                '    <Route path="/" element={<HomePage />} />\n'
                '    <Route path="/novel/:id" element={<NovelPage />} />\n'
                '  </Routes></BrowserRouter>;\n'
                '}\n'
            ),
            "frontend/src/pages/HomePage.tsx": (
                'import { useState } from "react";\n\n'
                'export default function HomePage() {\n'
                '  const [premise, setPremise] = useState("");\n'
                '  const createNovel = async () => {\n'
                '    await fetch("/api/novels", {method:"POST",body:JSON.stringify({premise})});\n'
                '  };\n'
                '  return <div><h1>Novel Writer</h1>'
                '<textarea value={premise} onChange={e=>setPremise(e.target.value)}/>'
                '<button onClick={createNovel}>Create</button></div>;\n'
                '}\n'
            ),
            "frontend/package.json": (
                '{"name":"novel-writer","private":true,"dependencies":{"react":"^18","react-dom":"^18","react-router-dom":"^6"},"devDependencies":{"vite":"^5","@vitejs/plugin-react":"^4","typescript":"^5"}}\n'
            ),
            "frontend/vite.config.ts": (
                'import {defineConfig} from "vite";import react from "@vitejs/plugin-react";'
                'export default defineConfig({plugins:[react()],server:{proxy:{"/api":"http://localhost:8000"}}});\n'
            ),
        }
        output_parts = []
        for path, content in files.items():
            output_parts.append(f"===FILE:{path}===\n{content}")
        return ProviderResponse(
            content="\n".join(output_parts),
            tokens_in=300, tokens_out=len("\n".join(output_parts)) // 4, model="mock",
        )

    def _mock_readme(self) -> ProviderResponse:
        return ProviderResponse(content=(
            "# Novel Writer AI\n\n"
            "AI-powered novel writing assistant.\n\n"
            "## Quick Start\n\n"
            "```bash\n"
            "cd backend && pip install -r requirements.txt && uvicorn main:app --reload\n"
            "cd frontend && npm install && npm run dev\n"
            "```\n"
        ), tokens_in=100, tokens_out=200, model="mock")
