"""Hub 数据模型 — RolePack 元信息、索引、版本"""

from dataclasses import dataclass, field
from enum import Enum


class PackSource(str, Enum):
    BUILTIN = "builtin"
    LOCAL = "local"
    COMMUNITY = "community"
    REMOTE = "remote"


@dataclass
class PackMeta:
    """RolePack 元信息 — 注册表中的一条记录"""
    name: str
    version: str
    description: str
    icon: str = "📦"
    tags: list[str] = field(default_factory=list)
    source: PackSource = PackSource.LOCAL
    path: str = ""
    author: str = ""
    downloads: int = 0
    rating: float = 0.0
    compatible_genie: str = ">=0.1.0"
    remote_url: str = ""

    @property
    def id(self) -> str:
        return f"{self.name}@{self.version}"


@dataclass
class CommunityIndex:
    """社区市场索引 — YAML 文件"""
    packs: list[PackMeta] = field(default_factory=list)
    last_updated: str = ""


@dataclass
class InstallResult:
    """安装结果"""
    success: bool
    pack_name: str
    version: str
    installed_path: str = ""
    error: str = ""
    warnings: list[str] = field(default_factory=list)