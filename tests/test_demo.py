import logging
from typing import TypeVar

from multidict import CIMultiDict

from extapi.http.addons.auth import BearerAuthAddon
from extapi.http.addons.headers import AddHeadersAddon
from extapi.http.addons.log import LoggingAddon
from extapi.http.addons.retry import Retry5xxAddon, Retry429Addon
from extapi.http.addons.status import StatusValidationAddon
from extapi.http.backends.aiohttp import AiohttpExecutor
from extapi.http.executors.limiters import (
    ConcurrencyLimitedExecutor,
    RateLimitedExecutor,
)
from extapi.http.executors.retry import RetryableExecutor
from extapi.limiters.concurrency.local import LocalConcurrencyLimiter
from extapi.limiters.rps.local import LocalRateLimiter

logging.basicConfig(level=logging.DEBUG)


T = TypeVar("T")


class TestHeaders:
    async def __call__(self, headers: CIMultiDict) -> None:
        headers.add("X-Test-Header", "test")


class FooTokenGetter:
    def __call__(self) -> str:
        return "foo-bar"


async def demo2():
    async with (
        LocalRateLimiter(rate_limit=50, rate_limit_window_seconds=1) as rate_limiter,
        LocalConcurrencyLimiter(max_concurrency=100) as concurrency_limiter,
    ):
        executor = AiohttpExecutor().generalize()
        executor = RateLimitedExecutor(
            executor,
            rate_limiter=rate_limiter,
        )
        executor = ConcurrencyLimitedExecutor(
            executor,
            concurrency_limiter=concurrency_limiter,
        )
        executor = RetryableExecutor(
            executor,
            addons=[
                BearerAuthAddon(FooTokenGetter()),
                AddHeadersAddon(TestHeaders()),
                Retry5xxAddon(),
                Retry429Addon(),
                StatusValidationAddon((200,)),
                LoggingAddon(),
            ],
        )

    async with executor:
        response = await executor.get("https://ifconfig.co/json")
        print(response.data)
        print(response.backend_response.original)
        # assert response.backend_response.original.http_version == "HTTP/2"


# asyncio.run(test_demo2())
