"""dataplat 业务服务层。

不持 state；方法接受 session + caller context；不处理 HTTP / 不查 role
（admin 权限由 router 的 Depends 守卫）。
"""

from dataplat_api.services.repo import RepoService

__all__ = ["RepoService"]
