"""RolePack 安装器 — 下载、校验、安装"""

import logging
import shutil
from pathlib import Path

import yaml

from genie_engine.schemas.validator import SchemaValidator
from genie_hub.models import InstallResult, PackMeta, PackSource

logger = logging.getLogger(__name__)


class PackInstaller:
    """RolePack 安装器。

    支持:
    - 从本地路径安装
    - 从 URL 下载安装
    - 从 GitHub 仓库安装
    """

    def __init__(self, packs_dir: Path | str | None = None):
        if packs_dir is None:
            packs_dir = Path(__file__).parent.parent / "rolepacks"
        self.packs_dir = Path(packs_dir)
        self.validator = SchemaValidator()
        self.community_dir = self.packs_dir / "community"
        self.community_dir.mkdir(parents=True, exist_ok=True)

    def install_from_path(self, source_path: Path | str) -> InstallResult:
        """从本地路径安装 RolePack"""
        source = Path(source_path)
        if not source.exists():
            return InstallResult(
                success=False,
                pack_name=source.stem,
                version="?",
                error=f"文件不存在: {source}",
            )

        try:
            data = yaml.safe_load(source.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            return InstallResult(
                success=False,
                pack_name=source.stem,
                version="?",
                error=f"YAML 解析失败: {exc}",
            )

        name = data.get("name", source.stem.replace(".rolepack", ""))
        version = data.get("version", "0.0.0")

        # Schema 校验
        errors = self.validator.validate(data)
        if errors:
            return InstallResult(
                success=False,
                pack_name=name,
                version=version,
                error=f"Schema 校验失败: {'; '.join(errors[:3])}",
                warnings=errors,
            )

        # 复制到 packs 目录
        dest_name = f"{name.lower().replace(' ', '_')}.rolepack.yaml"
        dest = self.packs_dir / dest_name
        shutil.copy2(source, dest)

        logger.info("安装成功: %s → %s", name, dest_name)
        return InstallResult(
            success=True,
            pack_name=name,
            version=version,
            installed_path=str(dest.absolute()),
        )

    def install_from_community(self, pack_meta: PackMeta) -> InstallResult:
        """从社区市场安装（下载 + 校验 + 安装）"""
        if not pack_meta.remote_url:
            return InstallResult(
                success=False,
                pack_name=pack_meta.name,
                version=pack_meta.version,
                error="该 Pack 没有提供下载地址",
            )

        # 对于内置 Pack（和 Genie 同仓库），直接检查本地是否已有
        if pack_meta.source == PackSource.BUILTIN:
            local = self.packs_dir / f"{
                pack_meta.name.lower().replace(' ', '_')
            }.rolepack.yaml"
            if local.exists():
                return InstallResult(
                    success=True,
                    pack_name=pack_meta.name,
                    version=pack_meta.version,
                    installed_path=str(local.absolute()),
                )
            return InstallResult(
                success=False,
                pack_name=pack_meta.name,
                version=pack_meta.version,
                error="内置 Pack 文件缺失，请重新安装 Genie",
            )

        # 远程安装 — TODO: 实现 HTTP 下载
        return InstallResult(
            success=False,
            pack_name=pack_meta.name,
            version=pack_meta.version,
            error="远程安装功能开发中",
        )

    def uninstall(self, name: str) -> InstallResult:
        """卸载 RolePack"""
        candidates = [
            self.packs_dir / f"{name}.rolepack.yaml",
            self.packs_dir / f"{name.lower().replace(' ', '_')}.rolepack.yaml",
            self.community_dir / f"{name}.rolepack.yaml",
        ]
        for c in candidates:
            if c.exists():
                c.unlink()
                logger.info("已卸载: %s", c.name)
                return InstallResult(success=True, pack_name=name, version="?")
        return InstallResult(
            success=False,
            pack_name=name,
            version="?",
            error=f"未找到已安装的 Pack: {name}",
        )