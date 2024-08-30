# pragma: no cover

import asyncio
import logging
from typing import TypeVar

from multidict import CIMultiDict

from extapi.http.addons.auth import BearerAuthAddon
from extapi.http.addons.headers import AddHeadersAddon
from extapi.http.addons.status import StatusValidationAddon
from extapi.http.backends.aiohttp import AiohttpExecutor
from extapi.http.executors.limiters import (
    ConcurrencyLimitedExecutor,
    RateLimitedExecutor,
)
from extapi.http.executors.metrics import PrometheusMetricsExecutor
from extapi.http.executors.retry import RetryableExecutor
from extapi.http.executors.trace import OpenTelemetryExecutor
from extapi.http.metrics.container import MetricsContainer
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


async def demo2():
    async with AiohttpExecutor() as base:
        # async with HttpxExecutor() as base:
        executor = base.generalize()
        executor = OpenTelemetryExecutor(executor)
        executor = PrometheusMetricsExecutor(
            executor, metrics_container=MetricsContainer(metrics_prefix="demo")
        )
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
                StatusValidationAddon((200,)),
            ],
        )

        async with await executor.get(
            "https://ifconfig.co/json"  # , path_template="/json"
        ) as response:
            print(await response.read())
            print(response.original.headers)
            # assert response.original.http_version == "HTTP/2"


asyncio.run(demo2())
