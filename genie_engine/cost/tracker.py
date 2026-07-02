"""运行时成本追踪"""

import logging
from genie_engine.schemas.result import CostRecord

logger = logging.getLogger(__name__)

# 复用 estimator 的成本数据
MODEL_COSTS: dict[str, dict[str, float]] = {
    "mock":     {"input": 0, "output": 0},
    "deepseek": {"input": 0.00014, "output": 0.00028},
    "gpt4":     {"input": 0.0025, "output": 0.01},
    "claude":   {"input": 0.003, "output": 0.015},
    "local":    {"input": 0, "output": 0},
}


class BudgetTracker:
    """运行时追踪开销，超预算时发出警告"""

    def __init__(self, budget: float | None = None):
        self.budget = budget
        self.spent: float = 0.0
        self.calls: list[CostRecord] = []

    def record(self, provider: str, model: str, tokens_in: int, tokens_out: int) -> None:
        """记录一次 LLM 调用的成本"""
        costs = MODEL_COSTS.get(provider, MODEL_COSTS["deepseek"])
        call_cost = (tokens_in * costs["input"] + tokens_out * costs["output"]) / 1000
        self.spent += call_cost
        self.calls.append(CostRecord(
            provider=provider,
            model=model,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            cost_usd=round(call_cost, 6),
        ))

    @property
    def is_over_budget(self) -> bool:
        return self.budget is not None and self.spent >= self.budget

    @property
    def total_cost(self) -> float:
        return round(self.spent, 4)

    @property
    def total_calls(self) -> int:
        return len(self.calls)

    def summary(self) -> str:
        return (
            f"Cost: ${self.total_cost:.4f} | "
            f"Calls: {self.total_calls} | "
            f"{'OVER BUDGET' if self.is_over_budget else 'within budget'}"
        )
