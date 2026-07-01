"""测试 providers 层"""

import pytest
from genie_engine.providers.base import Message, ProviderResponse
from genie_engine.providers.registry import ProviderRegistry
from genie_engine.providers.mock import MockProvider
from genie_engine.core.exceptions import ProviderError


class TestMockProvider:
    async def test_chat_returns_response(self):
        provider = MockProvider()
        messages = [Message(role="user", content="Hello")]
        response = await provider.chat(messages)
        assert isinstance(response, ProviderResponse)
        assert response.model == "mock"

    async def test_chat_research_scenario(self):
        provider = MockProvider()
        messages = [Message(role="user", content="请做调研分析")]
        response = await provider.chat(messages)
        assert "competitors" in response.content
        assert "tech_options" in response.content

    async def test_chat_director_evaluation(self):
        provider = MockProvider()
        messages = [Message(role="user", content="请评估阶段产出是否 PASS")]
        response = await provider.chat(messages)
        assert "PASS" in response.content


class TestProviderRegistry:
    def test_get_mock(self):
        provider = ProviderRegistry.get("mock")
        assert isinstance(provider, MockProvider)

    def test_get_unknown_raises(self):
        with pytest.raises(ProviderError, match="unknown_provider"):
            ProviderRegistry.get("unknown_provider")

    def test_list_all(self):
        names = ProviderRegistry.list_all()
        assert "mock" in names
