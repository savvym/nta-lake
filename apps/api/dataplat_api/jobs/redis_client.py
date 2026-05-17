"""Redis + RQ Queue 单例（spec rq-worker-skeleton-20260517 AC-3）。

env `DATAPLAT_REDIS_URL`（默认 `redis://localhost:6379/0`）。
Queue 名固定 `default`（MVP；多 queue 留 follow-up）。
"""

from __future__ import annotations

import os

import redis
from rq import Queue

_DEFAULT_REDIS_URL = "redis://localhost:6379/0"
_DEFAULT_QUEUE_NAME = "default"

_redis: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        url = os.environ.get("DATAPLAT_REDIS_URL", _DEFAULT_REDIS_URL)
        _redis = redis.Redis.from_url(url)
    return _redis


def get_queue(name: str = _DEFAULT_QUEUE_NAME) -> Queue:
    return Queue(name, connection=get_redis())
