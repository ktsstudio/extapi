import asyncio
import logging
import time
from collections import deque

from .abc import RateLimiter


class LocalRateLimiter(RateLimiter):
    __slots__ = (
        "_rate_limit",
        "_rate_limit_window_seconds",
        "_logger",
        "_deque",
    )

    def __init__(
        self,
        *,
        rate_limit: int = 0,
        rate_limit_window_seconds: int = 1,
    ) -> None:
        self._rate_limit = rate_limit
        self._rate_limit_window_seconds = rate_limit_window_seconds
        self._logger = logging.getLogger("extapi.rate_limiter.local")
        self._deque: deque[float] = deque(maxlen=rate_limit)

    async def rate_limit(self):
        if self._rate_limit <= 0:
            return

        if not self._deque.maxlen:
            return

        now = time.monotonic()

        if len(self._deque) < self._deque.maxlen:
            self._deque.append(now)
            return

        frame = now - self._deque.popleft()
        sleep_seconds = self._rate_limit_window_seconds - frame

        if sleep_seconds > 0:
            execute_at = now + sleep_seconds
            self._deque.append(execute_at)
            self._logger.debug(
                "sleeping for %.2fs in order to satisfy rate limit %d within %d seconds",
                sleep_seconds,
                self._rate_limit,
                self._rate_limit_window_seconds,
            )
            await asyncio.sleep(sleep_seconds)
        else:
            self._deque.append(now)
