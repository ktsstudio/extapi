# extapi

Library for performing HTTP calls to external systems. Made to be modular, extensible and easy to use.

## Installation

To use with aiohttp backend:
```bash
pip install 'extapi[aiohttp]'
```

To use with httpx backend:
```bash
pip install 'extapi[httpx]'
```

## Quick example

Using aiohttp:

```python
import asyncio
from extapi.http.backends.aiohttp import AiohttpExecutor


async def main():
    async with AiohttpExecutor() as executor:
        async with await executor.get('https://httpbin.org/get') as response:
            print(response.status)
            print(await response.read())


asyncio.run(main())
```

Using httpx:

```python
import asyncio
from extapi.http.backends.httpx import HttpxExecutor


async def main():
    async with HttpxExecutor() as executor:
        async with await executor.get('https://httpbin.org/get') as response:
            print(response.status)
            print(await response.read())


asyncio.run(main())
```

## Features

### Retryable executor

You can use the `RetryableExecutor` class to retry requests in case of failure. It will retry the request until the maximum number of retries is reached or the request is successful.

There is also a set of additional `Addon`s to a RetyableExecutor. Usually you would probably use `RetryableExecutor` in your code base.

```python
import asyncio
from extapi.http.backends.aiohttp import AiohttpExecutor
from extapi.http.executors.retry import RetryableExecutor


async def main():
    async with AiohttpExecutor() as backend:
        executor = RetryableExecutor(backend, max_retries=3)

        async with await executor.get('https://httpbin.org/get') as response:
            print(response.status)
            print(await response.read())


asyncio.run(main())
```

As you can see nothing changes in terms of usage, but now we have retries in case of failure (it may be 500 errors, 401 with custom authentication and token reacquiring for example, TimeoutError, any other Exceptions). There is a default set of addons that are being added to a `RetryableExecutor`:

```python
default_addons = [
    Retry5xxAddon(),
    Retry429Addon(),
    LoggingAddon(),
]
```

First 2 retry 5xx and 429 status codes. The last one logs the request and response.

### Addons

Addons are a way to extend the functionality of an executor. They can be used to add additional functionality to the executor, like logging, retrying requests, headers passing, authentication, etc.

#### LoggingAddon

This one is simple ad just logs the fact of a request being sent and a received response.


#### VerboseLoggingAddon

This one is more verbose and logs the request and response headers and body.

#### Retry5xxAddon

This one retries the request in case of 5xx status code.

#### Retry429Addon

This one retries the request in case of 429 status code. It also waits for the `Retry-After` header if it is present in the response and waits the specified time.

#### StatusValidationAddon

This one validates the status code of the response. If the status code is not in the list of allowed status codes, it raises an exception.

#### AddHeadersAddon

This one adds headers to the request. It expects a callable or an awaitable that accepts headers in order to modify them.

In the following example we add an `X-Api-Key` header on each request (in case of errors this would be 3 requests).

_Note: the function `headers_patch` is called before each request in case of retries, so you can leverage that to add some keys rotating logic in this case, for example._

```python
import asyncio

from multidict import CIMultiDict

from extapi.http.addons.headers import AddHeadersAddon
from extapi.http.backends.aiohttp import AiohttpExecutor
from extapi.http.executors.retry import RetryableExecutor


async def headers_patch(headers: CIMultiDict):
    headers["X-Api-Key"] = "some-api-token"


async def main():
    async with AiohttpExecutor() as backend:
        executor = RetryableExecutor(backend, max_retries=3, addons=[
            AddHeadersAddon(headers_patch)
        ])

        async with await executor.get('https://httpbin.org/get') as response:
            print(await response.read())


asyncio.run(main())
```

#### BearerAuthAddon:

This one adds a `Authorization` header with a `Bearer` token. As in the previous example, you may execute some complex logic in the callable - like issuing new token in case of 401 error.

```python
import asyncio

from extapi.http.addons.auth import BearerAuthAddon
from extapi.http.backends.aiohttp import AiohttpExecutor
from extapi.http.executors.retry import RetryableExecutor


async def token_getter() -> str:
    return "some-api-token"


async def main():
    async with AiohttpExecutor() as backend:
        executor = RetryableExecutor(backend, max_retries=3, addons=[
            BearerAuthAddon(token_getter)
        ])

        async with await executor.get('https://httpbin.org/get') as response:
            print(await response.read())


asyncio.run(main())
```

##### Custom

You can also extend any existing addons or create your own. Just inherit from `Addon` and implement the `execute` method.

This is the `Addon` protocol and your custom addon has to satisfy it.
```python
@runtime_checkable
class Addon(Protocol[T]):
    async def before_request(self, request: RequestData) -> None:
        return None

    async def process_response(
        self, request: RequestData, response: Response[T]
    ) -> Response[T]:
        return response

    async def process_error(self, request: RequestData, error: Exception) -> None:
        return None
```

If you want to execute some custom logic in case of retry you would also need to satisfy a `Retryable` protocol. The `need_retry` function must return a tuple (bool, float | None) where the first element is a flag if the request should be retried and the second is a delay in seconds before the next retry if any.

```python
@runtime_checkable
class Retryable(Protocol[T_contr]):
    async def need_retry(
        self, response: Response[T_contr]
    ) -> tuple[bool, float | None]: ...
```

And as an example Retry5xxAddon:

```python
class Retry5xxAddon(Retryable[T], Generic[T]):
    async def need_retry(self, response: Response[T]) -> tuple[bool, float | None]:
        if response.status >= 500:
            return True, 1.0

        return False, None
```

### Other executors

You can create your own executor by inheriting from the `Executor` class and implementing the `execute` method. There are a couple more extra executors that modify behaviour of the initial request:

* `OpenTelemetryExecutor` — adds OpenTelemetry tracing to the request.
* `PrometheusMetricsExecutor` — tracks Prometheus metrics from the request/response.
* `ConcurrencyLimitedExecutor` - limits amount of concurrent requests that can happen simultaneously.
* `RateLimitedExecutor` — limits the amount of requests per second/minute. You can choose the window.

Let's see at the full-featured example:

```python
import asyncio

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


class TestHeaders:
    async def __call__(self, headers: CIMultiDict) -> None:
        headers.add("X-Test-Header", "test")


class FooTokenGetter:
    def __call__(self) -> str:
        return "foo-bar"


async def main():
    async with AiohttpExecutor() as base:
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

        async with await executor.get('https://httpbin.org/get') as response:
            print(await response.read())

asyncio.run(main())
```

In this example we leverage opentelemetry, metrics, rate limiting, retrying mechanics. We also add a custom header and a bearer token to the request. We also validate the status code of the response to be 200.


### What to depend on?

If you need to accept somewhere an executor in your code you may reference a `AbstractExecutor` as the most abstract class that all executors inherit from.

```python
from typing import Any, TypeVar

from extapi.http.abc import AbstractExecutor

T = TypeVar("T")

async def httpbin_get(executor: AbstractExecutor[T]) -> Any:
    async with await executor.get('https://httpbin.org/get') as response:
        return await response.json()

```

This way you may add any executor to your code, and it will work with it.


### Get an underlying backend executor

In some cases you may need to get an underlying backend executor to be sure that you may send a request in a specific format for this particular executor. You can do so like the following:

```python
import asyncio

from extapi.http.backends.aiohttp import AiohttpExecutor
from extapi.http.executors.retry import RetryableExecutor
from extapi.http.executors.wrapped import unwrap_executor


async def main():
    async with AiohttpExecutor() as backend:
        executor = RetryableExecutor(backend)

        assert isinstance(unwrap_executor(executor), AiohttpExecutor)

        # ... the rest

asyncio.run(main())
```
