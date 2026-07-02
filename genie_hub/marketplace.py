"""社区市场 — 远程 RolePack 索引与发现"""

import logging
from datetime import datetime, timezone

from genie_hub.models import CommunityIndex, PackMeta, PackSource
from genie_hub.registry import LocalRegistry

logger = logging.getLogger(__name__)

# 内置社区索引 — 随 Genie 发布，后续可通过 GitHub 更新
BUILTIN_COMMUNITY_PACKS: list[PackMeta] = [
    PackMeta(
        name="Genie Code",
        version="1.0.0",
        description="从一句话需求到完整项目交付。含10个AI角色。",
        icon="🔧",
        tags=["code", "development", "full-stack"],
        source=PackSource.BUILTIN,
        author="Genie Team",
        downloads=0,
        rating=4.8,
        remote_url="https://github.com/1406152161/genie",
    ),
    PackMeta(
        name="Genie Pack Creator",
        version="1.0.0",
        description="创建新的领域RolePack。Genie的自举机制。",
        icon="📦",
        tags=["meta", "rolepack", "creator"],
        source=PackSource.BUILTIN,
        author="Genie Team",
        downloads=0,
        rating=4.5,
        remote_url="https://github.com/1406152161/genie",
    ),
]


class Marketplace:
    """社区市场 — 发现、搜索、安装远程 RolePack"""

    def __init__(self, registry: LocalRegistry | None = None):
        self.registry = registry or LocalRegistry()
        self._community = CommunityIndex(
            packs=BUILTIN_COMMUNITY_PACKS,
            last_updated=datetime.now(timezone.utc).isoformat(),
        )

    def search(self, query: str, *, local_only: bool = False) -> list[PackMeta]:
        """搜索 Pack — 本地 + 社区"""
        results: list[PackMeta] = []

        # 本地搜索
        local = self.registry.search(query)
        results.extend(local)

        if not local_only:
            q = query.lower()
            community = [
                p for p in self._community.packs
                if q in p.name.lower()
                or q in p.description.lower()
                or any(q in t.lower() for t in p.tags)
            ]
            # 去重：本地已安装的社区包不重复显示
            installed_names = {p.name for p in local}
            results.extend(p for p in community if p.name not in installed_names)

        return results

    def list_community(self) -> list[PackMeta]:
        """列出社区市场中所有可用的 Pack"""
        return list(self._community.packs)

    def get_community_pack(self, name: str) -> PackMeta | None:
        """从社区市场获取单个 Pack 信息"""
        for p in self._community.packs:
            if p.name == name:
                return p
        return None

    def refresh(self) -> None:
        """刷新社区索引（从 GitHub 拉取最新列表）"""
        # TODO: 从 https://raw.githubusercontent.com/... 拉取最新 community_index.yaml
        logger.info("社区索引刷新: 功能预留")
        self._community.last_updated = datetime.now(timezone.utc).isoformat()