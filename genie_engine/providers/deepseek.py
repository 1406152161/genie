"""DeepSeek Provider — OpenAI 兼容 API"""

import logging
import os
from typing import Any

import httpx

from genie_engine.providers.base import LLMProvider, Message, ProviderResponse, ToolDef
from genie_engine.core.exceptions import (
    ProviderError,
    ProviderAuthError,
    ProviderTimeoutError,
    ProviderBadRequestError,
)

logger = logging.getLogger(__name__)

DEFAULT_BASE = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TIMEOUT = 120.0


class DeepSeekProvider(LLMProvider):
    """DeepSeek LLM Provider — 兼容 OpenAI chat/completions 协议"""

    def __init__(self, api_key: str = "", api_base: str = "", model: str = "", **kwargs):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY", "")
        self.api_base = (api_base or os.getenv("DEEPSEEK_API_BASE", DEFAULT_BASE)).rstrip("/")
        self.model = model or os.getenv("DEEPSEEK_MODEL", DEFAULT_MODEL)

    @property
    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """发送对话请求"""
        if not self.api_key:
            raise ProviderAuthError("DeepSeek API Key 未设置。设置环境变量 DEEPSEEK_API_KEY")

        payload: dict[str, Any] = {
            "model": kwargs.get("model", self.model),
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 8192),
        }

        url = f"{self.api_base}/v1/chat/completions"
        timeout = float(kwargs.get("timeout", DEFAULT_TIMEOUT))

        logger.info("DeepSeek request: model=%s messages=%d", payload["model"], len(messages))

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(url, json=payload, headers=self._headers)
        except httpx.TimeoutException as exc:
            raise ProviderTimeoutError(f"DeepSeek 请求超时 ({timeout}s)") from exc
        except httpx.HTTPError as exc:
            raise ProviderError(f"DeepSeek 网络错误: {exc}") from exc

        if response.status_code == 401:
            raise ProviderAuthError("DeepSeek 认证失败，请检查 DEEPSEEK_API_KEY")
        if response.status_code == 429:
            raise ProviderError("DeepSeek 请求频率超限，请稍后重试")
        if response.status_code == 400:
            raise ProviderBadRequestError(f"DeepSeek 请求参数错误: {response.text}")
        if response.status_code >= 500:
            raise ProviderError(f"DeepSeek 服务器错误 ({response.status_code})")

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return ProviderResponse(
                content=content,
                tokens_in=usage.get("prompt_tokens", 0),
                tokens_out=usage.get("completion_tokens", 0),
                model=data.get("model", self.model),
            )
        except (KeyError, IndexError, TypeError) as exc:
            raise ProviderError(f"DeepSeek 响应格式异常: {data}") from exc
