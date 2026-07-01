"""Provider 抽象接口。

所有 AI Provider 必须实现此接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    """对话消息"""
    role: str        # system | user | assistant
    content: str


@dataclass  
class ToolDef:
    """工具定义"""
    name: str
    description: str
    parameters: dict[str, Any] = field(default_factory=dict)


@dataclass
class ToolCall:
    """工具调用请求"""
    name: str
    params: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderResponse:
    """Provider 返回的统一结构"""
    content: str
    tool_calls: list[ToolCall] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    model: str = ""


class LLMProvider(ABC):
    """LLM Provider 抽象基类。

    所有 AI 后端（OpenAI、DeepSeek、Anthropic、Ollama）必须实现此接口。
    """

    @abstractmethod
    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """发送对话请求，返回 assistant 的回复。

        Args:
            messages: 对话历史
            tools: 可用的工具列表（可选）
            **kwargs: Provider 特定参数

        Returns:
            ProviderResponse: 统一响应结构

        Raises:
            ProviderError: 通用错误
            ProviderAuthError: 认证失败
            ProviderTimeoutError: 超时
            ProviderBadRequestError: 参数错误
        """
        ...
