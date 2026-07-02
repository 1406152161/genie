"""本地 RolePack 注册表 — 扫描 + 索引 + 查询"""

import logging
from pathlib import Path

import yaml

from genie_hub.models import PackMeta, PackSource

logger = logging.getLogger(__name__)


class LocalRegistry:
    """本地 RolePack 注册表。

    扫描 rolepacks/ 目录，建立索引，支持增删改查。
    """

    def __init__(self, packs_dir: Path | str | None = None):
        if packs_dir is None:
            packs_dir = Path(__file__).parent.parent / "rolepacks"
        self.packs_dir = Path(packs_dir)
        self._cache: dict[str, PackMeta] = {}

    def scan(self) -> list[PackMeta]:
        """扫描目录，返回所有索引到的 Pack"""
        self._cache.clear()
        results: list[PackMeta] = []

        for yaml_file in self.packs_dir.glob("*.rolepack.yaml"):
            try:
                meta = self._parse_meta(yaml_file)
                self._cache[meta.name] = meta
                results.append(meta)
            except Exception as exc:
                logger.warning("跳过无效 Pack: %s — %s", yaml_file.name, exc)

        logger.info("注册表扫描完成: %d 个 Pack", len(results))
        return results

    def get(self, name: str) -> PackMeta | None:
        """按名称查询单个 Pack"""
        if not self._cache:
            self.scan()
        return self._cache.get(name)

    def list_all(self) -> list[PackMeta]:
        """列出所有已安装的 Pack"""
        return self.scan()

    def search(self, query: str) -> list[PackMeta]:
        """模糊搜索 — 按名称、描述、标签匹配"""
        all_packs = self.scan()
        q = query.lower()
        return [
            p for p in all_packs
            if q in p.name.lower()
            or q in p.description.lower()
            or any(q in t.lower() for t in p.tags)
        ]

    def is_installed(self, name: str) -> bool:
        """检查 Pack 是否已安装"""
        return self.get(name) is not None

    def _parse_meta(self, yaml_path: Path) -> PackMeta:
        """解析 RolePack YAML 提取元信息"""
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        return PackMeta(
            name=data.get("name", yaml_path.stem.replace(".rolepack", "")),
            version=data.get("version", "0.0.0"),
            description=data.get("description", ""),
            icon=data.get("icon", "📦"),
            tags=data.get("tags", []),
            source=PackSource.LOCAL,
            path=str(yaml_path.absolute()),
        )