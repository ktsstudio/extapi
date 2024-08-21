import asyncio
import logging
from typing import TypeVar

from multidict import CIMultiDict

from extapi.http.addons.auth import BearerAuthAddon
from extapi.http.addons.headers import AddHeadersAddon
from extapi.http.addons.log import LoggingAddon
from extapi.http.addons.retry import Retry5xxAddon, Retry429Addon
from extapi.http.addons.status import StatusValidationAddon
from extapi.http.backends.httpx import HttpxExecutor
from extapi.http.executors.limiters import (
    ConcurrencyLimitedExecutor,
    RateLimitedExecutor,
)
from extapi.http.executors.retry import RetryableExecutor
from extapi.http.executors.trace import OpenTelemetryExecutor
from extapi.limiters.concurrency.local import LocalConcurrencyLimiter
from extapi.limiters.rps.local import LocalRateLimiter

logging.basicConfig(level=logging.DEBUG)

T = TypeVar("T", covariant=True)


class TestHeaders:
    async def __call__(self, headers: CIMultiDict) -> None:
        headers.add("X-Test-Header", "test")


class FooTokenGetter:
    def __call__(self) -> str:
        return "foo-bar"


#
# class DemoApi(Generic[T]):
#     def __init__(
#             self,
#             base: AbstractExecutor[T],
#             wrap_executor: ExecutorWrapper,
#     ):
#         self._executor = wrap_executor(
#             RateLimitedExecutor(
#                 base,
#                 rate_limiter=LocalRateLimiter(
#                     rate_limit=50, rate_limit_window_seconds=1
#                 ),
#             ),
#         )


async def demo2():
    # executor = AiohttpExecutor()
    executor = HttpxExecutor().generalize()
    executor = OpenTelemetryExecutor(executor)
    executor = RateLimitedExecutor(
        executor,
        rate_limiter=LocalRateLimiter(rate_limit=50, rate_limit_window_seconds=1),
    )
    executor = ConcurrencyLimitedExecutor(
        executor,
        concurrency_limiter=LocalConcurrencyLimiter(max_concurrency=100),
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

    # api = DemoApi(executor, wrap)

    async with executor:
        async with await executor.get("https://ifconfig.co/json") as response:
            print(await response.read())
            # print(response.backend_response.original().headers)
            assert response.backend_response.original().http_version == "HTTP/2"


asyncio.run(demo2())
