"""dataplat-worker 进程入口（spec rq-worker-skeleton-20260517 AC-10）。

连 Redis（env `DATAPLAT_REDIS_URL`，默认 redis://localhost:6379/0）+ 启
RQ Worker(['default']).work() 阻塞循环；MVP 默认 fork 模式，subprocess 隔离
推后到 follow-up `adapter-subprocess-isolation-*`。
"""

from __future__ import annotations

import logging
import os
import sys

from redis import Redis
from rq import Queue, Worker

_logger = logging.getLogger("dataplat.worker")

_DEFAULT_REDIS_URL = "redis://localhost:6379/0"
_DEFAULT_QUEUE_NAME = "default"


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("DATAPLAT_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    url = os.environ.get("DATAPLAT_REDIS_URL", _DEFAULT_REDIS_URL)
    queue_name = os.environ.get("DATAPLAT_QUEUE_NAME", _DEFAULT_QUEUE_NAME)
    conn = Redis.from_url(url)
    queue = Queue(queue_name, connection=conn)
    worker = Worker([queue], connection=conn)
    _logger.info("dataplat-worker 启动 connection=%s queue=%s", url, queue_name)
    worker.work()
    return 0


if __name__ == "__main__":
    sys.exit(main())
