"""文件范围限制 — 角色只能写被授权的目录。"""

from pathlib import Path

from genie_engine.core.exceptions import FileScopeViolation


class FileScope:
    """限制角色的文件操作权限。

    每个角色在 RolePack 中声明 file_scope，
    此对象在角色执行时校验每次文件写入。
    """

    def __init__(self, allowed_paths: list[str]):
        self.allowed: list[Path] = [Path(p) for p in allowed_paths]

    def can_write(self, target: str | Path) -> bool:
        """检查 target 是否在允许写入的范围内"""
        if not self.allowed:
            return True  # 空列表 = 无限制 (Director)
        target_path = Path(target).resolve()
        return any(
            str(target_path).startswith(str(a.resolve()))
            or str(target_path).startswith(str(Path.cwd() / a))
            for a in self.allowed
        )

    def can_read(self, target: str | Path) -> bool:
        """读取权限比写入宽松"""
        target_str = str(target)
        # 允许读 .genie/ 和任何 allowed 路径
        return ".genie" in target_str or self.can_write(target)

    def validate_write(self, target: str | Path) -> None:
        """写入前校验，不通过则抛异常"""
        if not self.can_write(target):
            raise FileScopeViolation(
                f"写入被拒绝: '{target}' 不在允许的范围内: {self.allowed}"
            )

    def validate_read(self, target: str | Path) -> None:
        """读取前校验"""
        if not self.can_read(target):
            raise FileScopeViolation(
                f"读取被拒绝: '{target}' 不在允许的范围内"
            )
