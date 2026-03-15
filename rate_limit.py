"""
Optional rate limiter for --max-requests-per-minute.
Call set_max_per_minute(N) from main; runner and judge call acquire() before each API request.
"""
import asyncio
import time
from typing import List, Optional

_max_per_minute: Optional[int] = None
_timestamps: List[float] = []
_lock = asyncio.Lock()


def set_max_per_minute(n: Optional[int]) -> None:
    global _max_per_minute
    _max_per_minute = n


def is_active() -> bool:
    return _max_per_minute is not None and _max_per_minute > 0


async def acquire() -> None:
    """Block until we're under the rate limit, then record a request."""
    if _max_per_minute is None or _max_per_minute <= 0:
        return
    async with _lock:
        now = time.monotonic()
        # Drop timestamps older than 60 seconds
        global _timestamps
        _timestamps = [t for t in _timestamps if now - t < 60.0]
        while len(_timestamps) >= _max_per_minute:
            # Sleep until the oldest request is 60s old
            wait = 60.0 - (now - _timestamps[0])
            if wait > 0:
                await asyncio.sleep(wait)
            now = time.monotonic()
            _timestamps = [t for t in _timestamps if now - t < 60.0]
        _timestamps.append(time.monotonic())
