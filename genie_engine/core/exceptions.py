"""Genie Engine 异常体系。"""


class GenieError(Exception):
    """所有 Genie 异常的基类"""
    pass


class PackLoadError(GenieError):
    """RolePack 加载或校验失败"""
    pass


class StageExecutionError(GenieError):
    """阶段执行失败"""
    pass


class RoleExecutionError(GenieError):
    """角色执行失败"""
    pass


class ProviderError(GenieError):
    """AI Provider 通用异常"""
    pass


class ProviderAuthError(ProviderError):
    """AI Provider 认证失败（API Key 无效）"""
    pass


class ProviderTimeoutError(ProviderError):
    """AI Provider 请求超时"""
    pass


class ProviderBadRequestError(ProviderError):
    """AI Provider 请求参数错误"""
    pass


class SandboxError(GenieError):
    """沙箱相关异常"""
    pass


class FileScopeViolation(SandboxError):
    """角色试图写入未授权目录"""
    pass


class BudgetExceededError(GenieError):
    """预算超限"""
    pass


class WorkspaceError(GenieError):
    """工作空间操作异常"""
    pass
