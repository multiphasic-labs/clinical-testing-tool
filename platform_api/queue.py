from __future__ import annotations

import os
from typing import Optional


def redis_url() -> Optional[str]:
    return os.getenv("SAFETY_PLATFORM_REDIS_URL") or os.getenv("REDIS_URL")


def is_queue_enabled() -> bool:
    return bool(redis_url())


def enqueue_run(run_id: str) -> bool:
    """
    Enqueue `run_evaluation_job(run_id)` onto Redis/RQ.

    Returns True if queued, False if queue is disabled.
    """
    url = redis_url()
    if not url:
        return False

    from redis import Redis
    from rq import Queue

    from .worker import run_evaluation_job

    conn = Redis.from_url(url)
    q = Queue(name=os.getenv("SAFETY_PLATFORM_QUEUE_NAME", "default"), connection=conn)
    q.enqueue(run_evaluation_job, run_id)
    return True

