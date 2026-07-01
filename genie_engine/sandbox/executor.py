"""代码执行器 — Docker 沙箱 + 静态分析兜底 (Q1决策)。

默认在 Docker 容器中执行代码（安全）。
无 Docker 时降级为静态分析（ruff + mypy）。
"""

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    passed: bool
    mode: str           # docker | static_only
    output: str = ""
    warning: str = ""


def _has_docker() -> bool:
    """检测 Docker 是否可用"""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            timeout=5,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _run_in_docker(project_dir: Path, timeout: int = 120) -> TestResult:
    """在临时 Docker 容器中运行 pytest"""
    container_name = f"genie_test_{project_dir.name}"
    try:
        result = subprocess.run(
            [
                "docker", "run", "--rm",
                "--name", container_name,
                "--network", "none",            # 禁止网络
                "--memory", "512m",
                "--cpus", "1.0",
                "-v", f"{project_dir.resolve()}:/app:ro",
                "-w", "/app",
                "python:3.12-slim",
                "sh", "-c",
                "pip install -q -r requirements.txt 2>/dev/null; "
                "pip install -q pytest 2>/dev/null; "
                "python -m pytest -q --tb=short 2>&1",
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return TestResult(
            passed=result.returncode == 0,
            mode="docker",
            output=result.stdout[-2000:],  # 截断长输出
        )
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)
        return TestResult(passed=False, mode="docker", output="Docker 执行超时")
    except FileNotFoundError:
        return TestResult(passed=False, mode="docker", output="Docker 未安装")


def _run_static_analysis(project_dir: Path) -> TestResult:
    """静态分析兜底"""
    output_parts: list[str] = []

    # ruff check
    try:
        r = subprocess.run(
            ["ruff", "check", str(project_dir)],
            capture_output=True, text=True, timeout=30,
        )
        output_parts.append(f"[ruff] {'PASS' if r.returncode==0 else 'FAIL'}")
        if r.stdout:
            output_parts.append(r.stdout[:500])
    except FileNotFoundError:
        output_parts.append("[ruff] 未安装，跳过")

    # mypy
    try:
        r = subprocess.run(
            ["mypy", str(project_dir), "--ignore-missing-imports"],
            capture_output=True, text=True, timeout=30,
        )
        output_parts.append(f"[mypy] {'PASS' if r.returncode==0 else 'FAIL'}")
    except FileNotFoundError:
        output_parts.append("[mypy] 未安装，跳过")

    output = "\n".join(output_parts)
    passed = "FAIL" not in output
    return TestResult(
        passed=passed,
        mode="static_only",
        output=output,
        warning="未在 Docker 沙箱中实际运行，可能存在运行时错误",
    )


def run_tests(project_dir: Path, timeout: int = 120) -> TestResult:
    """运行测试 — Docker 优先，静态分析兜底"""
    if _has_docker():
        logger.info("使用 Docker 沙箱执行测试")
        return _run_in_docker(project_dir, timeout)
    else:
        logger.warning("Docker 不可用，降级为静态分析")
        return _run_static_analysis(project_dir)
