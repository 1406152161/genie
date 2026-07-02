"""Test ProviderComparator — multi-model regression testing"""

import pytest
from pathlib import Path

from genie_engine.compare.runner import ProviderComparator, CompareReport, ModelRun


class TestProviderComparator:

    @pytest.mark.asyncio
    async def test_compare_single_model(self, tmp_path):
        """Single model compare should produce 1 run with 100% pass"""
        pack_path = Path(__file__).parent.parent / "rolepacks" / "code.rolepack.yaml"
        comparator = ProviderComparator(pack_path)

        report = await comparator.compare(
            "Build a hello world app",
            models=["mock"],
        )

        assert isinstance(report, CompareReport)
        assert len(report.runs) == 1
        assert report.pass_rate == 1.0
        assert "mock" in report.models_passed
        assert report.pack_name == "Genie Code"

    @pytest.mark.asyncio
    async def test_compare_multi_models(self, tmp_path):
        """Multiple models compare should produce N runs"""
        pack_path = Path(__file__).parent.parent / "rolepacks" / "code.rolepack.yaml"
        comparator = ProviderComparator(pack_path)

        report = await comparator.compare(
            "Build a hello world app",
            models=["mock", "mock", "mock"],  # 3x mock = 3 independent runs
        )

        assert len(report.runs) == 3
        assert report.pass_rate == 1.0
        assert len(report.models_passed) == 3
        assert len(report.models_failed) == 0
        assert report.fastest  # should have a value
        assert report.slowest  # should have a value

    @pytest.mark.asyncio
    async def test_compare_unknown_model_reports_error(self, tmp_path):
        """Unknown model should produce error run, not crash"""
        pack_path = Path(__file__).parent.parent / "rolepacks" / "code.rolepack.yaml"
        comparator = ProviderComparator(pack_path)

        report = await comparator.compare(
            "Build a hello world app",
            models=["nonexistent_model_xyz"],
        )

        assert len(report.runs) == 1
        assert "nonexistent_model_xyz" in report.models_failed
        run = report.runs[0]
        assert run.error  # should have error message
        assert "not registered" in run.error.lower()

    @pytest.mark.asyncio
    async def test_report_summary(self):
        """CompareReport.summary should contain key fields"""
        report = CompareReport(
            goal="test",
            pack_name="TestPack",
            pack_version="1.0.0",
            runs=[
                ModelRun(model="mock", duration_seconds=1.0),
                ModelRun(model="gpt4", duration_seconds=2.0, error="timeout"),
            ],
            models_passed=["mock"],
            models_failed=["gpt4"],
            fastest="mock",
            slowest="gpt4",
            total_duration=3.0,
        )

        summary = report.summary
        assert "TestPack" in summary
        assert "50%" in summary  # pass rate
        assert "mock" in summary
        assert "gpt4" in summary