"""pytest 配置：JWT secret 早于任何 dataplat_api 模块 import。

spec auth-scaffold-20260517 MUST FIX-2：tokens.py 每次调用都 os.getenv 读 secret，
但 conftest 仍需保 secret 存在；以 setdefault 保 idempotent（用户可 export 覆盖）。

注：本会话内之前用过 `loop_scope='module'` 试图绕 asyncpg event loop 关闭时序，
但实测会与 function-scope fixture 冲突；改回默认 function scope，每个测试用 fresh
engine 而不 dispose（test_models / test_auth 都遵循）。
"""

from __future__ import annotations

import os

os.environ.setdefault(
    "DATAPLAT_JWT_SECRET",
    "test-secret-not-prod-x32-bytes-xxxxx",
)
# NullPool 避免 asyncpg+pytest-asyncio 跨 event-loop stale connection
os.environ.setdefault("DATAPLAT_USE_NULL_POOL", "1")
