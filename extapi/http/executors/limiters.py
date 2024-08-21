from typing import TypeVar

from extapi.http.abc import AbstractExecutor
from extapi.http.types import RequestData, Response
from extapi.limiters.concurrency.abc import ConcurrencyLimiter
from extapi.limiters.rps.abc import RateLimiter

from .wrapped import WrappedExecutor

T = TypeVar("T", covariant=True)


class ConcurrencyLimitedExecutor(WrappedExecutor[T]):
    __slots__ = ("_concurrency_limiter",)

    def __init__(
        self,
        executor: AbstractExecutor[T],
        *,
        concurrency_limiter: ConcurrencyLimiter,
    ):
        super().__init__(executor)
        self._concurrency_limiter = concurrency_limiter

    async def execute(self, request: RequestData) -> Response[T]:
        async with self._concurrency_limiter.get_semaphore():
            return await super().execute(request)


class RateLimitedExecutor(WrappedExecutor[T]):
    __slots__ = ("_rate_limiter",)

    def __init__(
        self,
        executor: AbstractExecutor[T],
        *,
        rate_limiter: RateLimiter,
    ):
        super().__init__(executor)
        self._rate_limiter = rate_limiter

    async def execute(self, request: RequestData) -> Response[T]:
        await self._rate_limiter.rate_limit()
        return await super().execute(request)
