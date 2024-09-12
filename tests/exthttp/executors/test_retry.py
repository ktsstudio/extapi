import inspect
import time
from collections.abc import Iterable
from typing import Any

import pytest
from pytest_mock.plugin import MockerFixture

from extapi.http.abc import AbstractExecutor, Addon
from extapi.http.addons.auth import BearerAuthAddon
from extapi.http.addons.retry import Retry5xxAddon
from extapi.http.executors.retry import RetryableExecutor
from extapi.http.types import ExecuteError, HttpExecuteError, RequestData, Response
from tests.exthttp._helpers import DummyBackendResponse


class _DummyExecutor(AbstractExecutor[Any]):
    def __init__(self, responses: Iterable[int | type[Exception] | Exception] = (200,)):
        self.call_count = 0
        self._responses: list[int | type[Exception] | Exception] = list(responses)
        self._current_response_index = 0

    async def execute(self, request: RequestData) -> Response:
        self.call_count += 1
        if self._current_response_index < len(self._responses):
            response = self._responses[self._current_response_index]
            self._current_response_index += 1
        else:  # pragma: no cover
            response = self._responses[-1]  # Return the last response if we've run out

        if isinstance(response, Exception) or (
            inspect.isclass(response) and issubclass(response, Exception)
        ):
            raise response

        if isinstance(response, int):
            return Response(
                method=request.method,
                status=response,
                backend_response=DummyBackendResponse(),
                url=request.url,
            )

        raise BaseException(
            f"unexpected response type: {type(response)}"
        )  # pragma: no cover


class TestRetryExecutor:
    async def test_basic(self, request_simple: RequestData):
        base = _DummyExecutor()
        executor = RetryableExecutor(base, retry_sleep_timeout=0, default_addons=())

        response = await executor.execute(request_simple)

        assert response.status == 200
        assert response.url == request_simple.url

    async def test_retry_500_no_addon(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[500, 200])
        executor = RetryableExecutor(
            base, max_retries=2, retry_sleep_timeout=0, default_addons=()
        )

        response = await executor.execute(request_simple)

        assert response.status == 500
        assert base.call_count == 1

    async def test_retry_500_with_addon(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[500, 200])
        executor = RetryableExecutor(
            base,
            max_retries=2,
            retry_sleep_timeout=0,
            addons=[
                Retry5xxAddon(),
            ],
            default_addons=(),
        )

        response = await executor.execute(request_simple)

        assert response.status == 200
        assert base.call_count == 2

    async def test_max_retries_exceeded(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[500, 500, 500])
        executor = RetryableExecutor(
            base,
            max_retries=3,
            retry_sleep_timeout=0,
            addons=[
                Retry5xxAddon(),
            ],
            default_addons=(),
        )

        response = await executor.execute(request_simple)

        assert response.status == 500
        assert base.call_count == 3

    async def test_non_retryable_status(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[400])
        executor = RetryableExecutor(
            base,
            max_retries=2,
            retry_sleep_timeout=0,
            addons=[
                Retry5xxAddon(),
            ],
            default_addons=(),
        )

        response = await executor.execute(request_simple)

        assert response.status == 400
        assert base.call_count == 1

    async def test_retry_with_bearer_auth_error(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[401, 401, 200])
        executor = RetryableExecutor(
            base,
            max_retries=2,
            retry_sleep_timeout=0,
            addons=[BearerAuthAddon(lambda: "token")],
            default_addons=(),
        )

        response = await executor.execute(request_simple)

        assert response.status == 401
        assert base.call_count == 2

    async def test_retry_with_bearer_auth_success(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[401, 401, 200])
        executor = RetryableExecutor(
            base,
            max_retries=3,
            retry_sleep_timeout=0,
            addons=[BearerAuthAddon(lambda: "token")],
            default_addons=(),
        )

        response = await executor.execute(request_simple)

        assert response.status == 200
        assert base.call_count == 3

    async def test_custom_retry_timeout(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[500, 200])
        executor = RetryableExecutor(
            base,
            max_retries=2,
            retry_sleep_timeout=0,
            addons=[
                Retry5xxAddon(default_timeout=1),
            ],
            default_addons=(),
        )

        started_at = time.monotonic()
        response = await executor.execute(request_simple)
        elapsed = time.monotonic() - started_at

        assert elapsed >= 1

        assert response.status == 200
        assert base.call_count == 2

    async def test_timeout_error(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[TimeoutError, TimeoutError(), 200])
        executor = RetryableExecutor(
            base, max_retries=3, retry_sleep_timeout=0, default_addons=()
        )

        response = await executor.execute(request_simple)

        assert response.status == 200
        assert base.call_count == 3

    async def test_timeout_error_propagate(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[TimeoutError, 200])
        executor = RetryableExecutor(
            base, max_retries=1, retry_sleep_timeout=0, default_addons=()
        )

        with pytest.raises(ExecuteError) as err:
            await executor.execute(request_simple)

        assert str(err.value) == "request failed after 1 retries: TimeoutError()"

    async def test_exception_success(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[Exception("some error"), 200])
        executor = RetryableExecutor(
            base, max_retries=3, retry_sleep_timeout=0, default_addons=()
        )

        response = await executor.execute(request_simple)

        assert response.status == 200
        assert base.call_count == 2

    async def test_exception_propagate(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[Exception("some error"), 200])
        executor = RetryableExecutor(
            base, max_retries=1, retry_sleep_timeout=0, default_addons=()
        )

        with pytest.raises(Exception) as err:
            await executor.execute(request_simple)

        assert str(err.value) == "request failed after 1 retries: Exception(some error)"

    async def test_propagate_execute_error(self, request_simple: RequestData):
        resp = Response(
            status=404,
            backend_response=DummyBackendResponse(),
            url=request_simple.url,
            method=request_simple.method,
        )
        base = _DummyExecutor(responses=[HttpExecuteError(resp), 200])
        executor = RetryableExecutor(
            base, max_retries=1, retry_sleep_timeout=0, default_addons=()
        )

        with pytest.raises(ExecuteError) as err:
            await executor.execute(request_simple)

        assert str(err.value) == "HTTPExecuteError(url=https://example.com, status=404)"

    async def test_with_process_error_addon(self, request_simple: RequestData):
        class _Addon(Addon):
            async def process_error(
                self, request: RequestData, error: Exception
            ) -> None:
                raise Exception("error processing exception")

        base = _DummyExecutor(responses=[Exception("some error"), 200])
        executor = RetryableExecutor(
            base,
            max_retries=1,
            retry_sleep_timeout=0,
            addons=[_Addon()],
            default_addons=(),
        )

        with pytest.raises(ExecuteError) as err:
            await executor.execute(request_simple)

        assert str(err.value) == "request failed after 1 retries: Exception(some error)"

    async def test_with_process_error_addon_success(self, request_simple: RequestData):
        class _Addon(Addon):
            async def process_error(
                self, request: RequestData, error: Exception
            ) -> None:
                raise Exception("error processing exception")

        base = _DummyExecutor(responses=[Exception("some error"), 200])
        executor = RetryableExecutor(
            base,
            max_retries=2,
            retry_sleep_timeout=0,
            addons=[_Addon()],
            default_addons=(),
        )

        response = await executor.execute(request_simple)

        assert response.status == 200
        assert base.call_count == 2

    async def test_default_addons(self, request_simple: RequestData):
        base = _DummyExecutor(responses=[500, 429, 200])
        executor = RetryableExecutor(
            base,
            max_retries=3,
            retry_sleep_timeout=0,
        )

        response = await executor.execute(request_simple)

        assert response.status == 200
        assert base.call_count == 3

    async def test_correct_sleep_count(
        self, request_simple: RequestData, mocker: MockerFixture
    ):
        mock_sleep = mocker.patch("asyncio.sleep")
        base = _DummyExecutor(responses=[500, 500])
        executor = RetryableExecutor(
            base,
            max_retries=2,
            retry_sleep_timeout=0.1,
        )

        response = await executor.execute(request_simple)

        assert response.status == 500
        assert base.call_count == 2
        assert mock_sleep.await_count == 1
