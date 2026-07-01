"""Genie API — FastAPI 后端入口"""

import uuid
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Genie API",
    description="Genie Engine REST API",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存存储 (后续可换 SQLite/PostgreSQL)
_runs: dict[str, dict] = {}


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


@app.post("/api/runs")
async def create_run(request: dict):
    """创建一次新的 Run"""
    run_id = str(uuid.uuid4())[:8]
    pack_name = request.get("pack", "code")
    goal = request.get("goal", "")
    model = request.get("model", "mock")

    _runs[run_id] = {
        "id": run_id,
        "pack": pack_name,
        "goal": goal,
        "model": model,
        "status": "running",
        "stages": [],
    }

    # 异步启动引擎
    import asyncio
    asyncio.create_task(_execute_run(run_id, pack_name, goal, model))

    return {"id": run_id, "status": "running"}


@app.get("/api/runs")
async def list_runs():
    return list(_runs.values())


@app.get("/api/runs/{run_id}")
async def get_run(run_id: str):
    if run_id not in _runs:
        return {"error": "not found"}, 404
    return _runs[run_id]


async def _execute_run(run_id: str, pack_name: str, goal: str, model: str):
    """后台执行引擎"""
    from genie_engine.core.engine import GenieEngine

    packs_dir = Path(__file__).parent.parent / "rolepacks"
    pack_path = packs_dir / f"{pack_name}.rolepack.yaml"

    if not pack_path.exists():
        _runs[run_id]["status"] = "failed"
        _runs[run_id]["error"] = f"RolePack not found: {pack_name}"
        return

    engine = GenieEngine(pack_path)
    result = await engine.execute(goal, model=model)

    _runs[run_id]["status"] = result.status
    _runs[run_id]["stages"] = [
        {"id": s.stage_id, "status": s.status, "duration": s.duration_seconds}
        for s in result.stages
    ]
    _runs[run_id]["duration"] = result.total_duration_seconds
    _runs[run_id]["output_dir"] = result.output_dir


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
