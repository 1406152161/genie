"""运行前成本预估"""

from genie_engine.schemas.result import CostEstimate

# 各模型成本 (USD per 1K tokens)
MODEL_COSTS = {
    "mock":     {"input": 0,        "output": 0},
    "deepseek": {"input": 0.00014,  "output": 0.00028},
    "gpt4":     {"input": 0.0025,   "output": 0.01},
    "claude":   {"input": 0.003,    "output": 0.015},
    "local":    {"input": 0,        "output": 0},
}

# 每个角色预估的平均 token 消耗
AVG_TOKENS_PER_CALL = 4000


class CostEstimator:
    """运行前给出成本预估"""

    @staticmethod
    def estimate(num_roles: int, num_stages: int, model: str = "deepseek") -> CostEstimate:
        """估算一次 Run 的成本

        Args:
            num_roles: 角色数量
            num_stages: 阶段数量
            model: 使用的模型名

        Returns:
            CostEstimate: 成本预估
        """
        cost = MODEL_COSTS.get(model, MODEL_COSTS["deepseek"])
        # 每个角色预估一次调用 + Director 每个阶段一次 + 重试余量
        estimated_calls = (num_roles + num_stages) * 1.5
        avg_tokens = AVG_TOKENS_PER_CALL

        estimated_cost = round(
            estimated_calls * avg_tokens * (cost["input"] + cost["output"]) / 1000,
            4,
        )
        worst_case = round(estimated_cost * 2.5, 4)

        return CostEstimate(
            model=model,
            estimated_calls=int(estimated_calls),
            estimated_cost_usd=estimated_cost,
            worst_case_usd=worst_case,
        )
