"""Provider 注册表。"""

from genie_engine.core.exceptions import ProviderError
from genie_engine.providers.base import LLMProvider


def _get_registry() -> dict[str, type[LLMProvider]]:
    from genie_engine.providers.mock import MockProvider
    from genie_engine.providers.deepseek import DeepSeekProvider

    return {
        "mock": MockProvider,
        "deepseek": DeepSeekProvider,
        # 暂未实现的 provider 兜底到 mock
        "gpt4": MockProvider,
        "claude": MockProvider,
        "local": MockProvider,
    }


class ProviderRegistry:
    @staticmethod
    def get(name: str, **kwargs) -> LLMProvider:
        registry = _get_registry()
        if name not in registry:
            raise ProviderError(
                f"未注册的 Provider: '{name}'。可用: {list(registry.keys())}"
            )
        return registry[name](**kwargs)

    @staticmethod
    def list_all() -> list[str]:
        return list(_get_registry().keys())