from __future__ import annotations

import os


def main() -> None:
    url = os.getenv("SAFETY_PLATFORM_REDIS_URL") or os.getenv("REDIS_URL")
    if not url:
        raise SystemExit("Missing SAFETY_PLATFORM_REDIS_URL (or REDIS_URL)")

    from redis import Redis
    from rq import Worker

    queue_name = os.getenv("SAFETY_PLATFORM_QUEUE_NAME", "default")
    conn = Redis.from_url(url)
    worker = Worker([queue_name], connection=conn)
    worker.work()


if __name__ == "__main__":
    main()

