"""进度事件总线 — 内存 fan-out。

简化版: 不依赖 Redis，纯内存实现。
供 StageExecutor 发布进度，CLI/Web 订阅进度。
"""

import asyncio
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any


class ProgressHub:
    """按资源 ID 分发进度事件。

    用法:
        hub = ProgressHub()
        hub.publish("run_123", status="design", progress=50)
        async for event in hub.subscribe("run_123"):
            print(event)
    """

    def __init__(self) -> None:
        self._queues: dict[str, list[asyncio.Queue[dict[str, Any]]]] = defaultdict(list)
        self._lock = asyncio.Lock()

    def publish(
        self,
        resource_id: str,
        *,
        status: str,
        progress: int,
        stage: str = "",
        role: str = "",
        error: str | None = None,
    ) -> None:
        """发布进度事件"""
        payload = {
            "type": "progress",
            "status": status,
            "progress": progress,
            "stage": stage,
            "role": role,
            "error": error,
            "done": status in ("completed", "failed", "cancelled"),
        }
        for queue in list(self._queues.get(resource_id, [])):
            try:
                queue.put_nowait(payload)
            except asyncio.QueueFull:
                pass

    async def subscribe(self, resource_id: str) -> AsyncIterator[dict[str, Any]]:
        """订阅进度事件"""
        queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=64)
        async with self._lock:
            self._queues[resource_id].append(queue)
        try:
            while True:
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=25.0)
                except asyncio.TimeoutError:
                    yield {"type": "heartbeat"}
                    continue
                yield event
                if event.get("done"):
                    break
        finally:
            async with self._lock:
                if queue in self._queues.get(resource_id, []):
                    self._queues[resource_id].remove(queue)


# 全局单例
_hub = ProgressHub()


def get_progress_hub() -> ProgressHub:
    return _hub
