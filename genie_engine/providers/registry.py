"""Provider 注册表。

复用 director-ai 的注册表模式：字典映射 + 统一 resolve 函数。
新增 Provider 只需在 _PROVIDER_REGISTRY 中加一行。
"""

from genie_engine.core.exceptions import ProviderError
from genie_engine.providers.base import LLMProvider


# 延迟导入，避免循环依赖
def _get_registry() -> dict[str, type[LLMProvider]]:
    from genie_engine.providers.mock import MockProvider
    return {
        "mock": MockProvider,
    }


class ProviderRegistry:
    """LLM Provider 注册表。

    用法:
        provider = ProviderRegistry.get("deepseek")
        response = await provider.chat([...])
    """

    @staticmethod
    def get(name: str, **kwargs) -> LLMProvider:
        registry = _get_registry()
        if name not in registry:
            raise ProviderError(
                f"未注册的 Provider: '{name}'。"
                f"可用: {list(registry.keys())}"
            )
        return registry[name](**kwargs)

    @staticmethod
    def list_all() -> list[str]:
        return list(_get_registry().keys())
