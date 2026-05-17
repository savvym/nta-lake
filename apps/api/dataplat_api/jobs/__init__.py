"""dataplat job 持久化 + RQ 分发（spec rq-worker-skeleton-20260517）。

模块结构：
- redis_client.py：Redis + RQ Queue 单例
- service.py：JobsService（DB CRUD）
- tasks.py：run_ingest_job（worker 调用）
"""

from dataplat_api.jobs.redis_client import get_queue, get_redis
from dataplat_api.jobs.service import JobsService

__all__ = ["JobsService", "get_queue", "get_redis"]
