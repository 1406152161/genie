"""Mock Provider — 无 API Key 环境下返回预设数据。

用于开发、测试和 CI 环境。所有方法都不需要网络。
"""

from genie_engine.providers.base import LLMProvider, Message, ProviderResponse, ToolDef


class MockProvider(LLMProvider):
    """返回预设的模拟数据。

    支持的模拟场景通过最后一条消息的内容进行路由。
    """

    async def chat(
        self,
        messages: list[Message],
        tools: list[ToolDef] | None = None,
        **kwargs,
    ) -> ProviderResponse:
        last_msg = messages[-1].content if messages else ""

        # Director 阶段评估
        if "PASS" in last_msg.upper() or "阶段产出" in last_msg:
            return ProviderResponse(
                content="PASS",
                tokens_in=100,
                tokens_out=5,
                model="mock",
            )

        # 通用 mock 回复
        return ProviderResponse(
            content=self._mock_content(last_msg),
            tokens_in=len(last_msg) // 4,
            tokens_out=200,
            model="mock",
        )

    def _mock_content(self, prompt: str) -> str:
        """根据 prompt 内容生成对应的 mock 回复"""
        import json

        lower = prompt.lower()

        if "research" in lower or "调研" in prompt:
            return json.dumps({
                "competitors": [
                    {"name": "MockProject", "strength": "简单", "weakness": "功能少", "stars": 100},
                ],
                "tech_options": [
                    {"stack": "FastAPI+React", "pros": ["成熟", "快速"], "cons": ["前端分离"], "score": 9},
                ],
                "recommendation": "FastAPI+React",
            }, ensure_ascii=False)

        if "功能清单" in prompt or "features" in lower:
            return json.dumps({
                "mvp_scope": "Web应用",
                "user_journey": "输入→处理→输出",
                "features": [
                    {"id": "F1", "name": "核心功能", "priority": "P0", "effort": "M"},
                ],
            }, ensure_ascii=False)

        if "架构" in prompt or "architect" in lower:
            return json.dumps({
                "tech_stack": "FastAPI + React + SQLite",
                "architecture": "3层: API→Service→Model",
                "api_endpoints": ["GET /api/items", "POST /api/items"],
            }, ensure_ascii=False)

        # 默认
        return '{"status": "ok", "message": "mock response"}'
