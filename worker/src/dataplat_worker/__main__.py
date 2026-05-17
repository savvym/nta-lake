"""`python -m dataplat_worker` 入口（spec rq-worker-skeleton-20260517 AC-10）。

委托给 `main.main()`：连 Redis + 启 RQ Worker.work() 阻塞循环。
"""

from __future__ import annotations

from dataplat_worker.main import main

if __name__ == "__main__":
    raise SystemExit(main())
