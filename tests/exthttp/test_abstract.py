from typing import Any

import pytest
from multidict import CIMultiDict

from extapi._meta import PY311
from extapi.http.abc import AbstractExecutor, Addon
from extapi.http.types import RequestData, Response

if PY311:
    from typing import assert_type  # type: ignore[attr-defined]
else:
    from typing_extensions import assert_type


class TestAbstractExecutor:
    @pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
    async def test_methods(
        self, request_filled: RequestData, response_simple: Response[Any], method: str
    ):
        executed = False

        class _Executor(AbstractExecutor[Any]):
            async def execute(self, request: RequestData) -> Response[Any]:
                nonlocal executed
                executed = True

                request_filled.method = method.upper()
                assert request == request_filled

                return response_simple

        executor = _Executor()
        executor_method = getattr(executor, method)

        await executor_method(
            request_filled.url,
            params=request_filled.params,
            headers=request_filled.headers,
            timeout=request_filled.timeout,
            json=request_filled.json,
            data=request_filled.data,
            **request_filled.kwargs,
        )
        assert executed is True

    @pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
    async def test_methods_headers_dict(
        self, request_filled: RequestData, response_simple: Response[Any], method: str
    ):
        executed = False

        class _Executor(AbstractExecutor[Any]):
            async def execute(self, request: RequestData) -> Response[Any]:
                nonlocal executed
                executed = True

                request_filled.method = method.upper()
                assert isinstance(request.headers, CIMultiDict)
                assert request == request_filled

                return response_simple

        executor = _Executor()
        executor_method = getattr(executor, method)

        await executor_method(
            request_filled.url,
            params=request_filled.params,
            headers=dict(request_filled.headers.items())
            if request_filled.headers is not None
            else None,
            timeout=request_filled.timeout,
            json=request_filled.json,
            data=request_filled.data,
            **request_filled.kwargs,
        )
        assert executed is True

    @pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
    async def test_methods_headers_None(
        self, request_filled: RequestData, response_simple: Response[Any], method: str
    ):
        request_filled.headers = None
        executed = False

        class _Executor(AbstractExecutor[Any]):
            async def execute(self, request: RequestData) -> Response[Any]:
                nonlocal executed
                executed = True

                request_filled.method = method.upper()
                assert request == request_filled

                return response_simple

        executor = _Executor()
        executor_method = getattr(executor, method)

        await executor_method(
            request_filled.url,
            params=request_filled.params,
            headers=None,
            timeout=request_filled.timeout,
            json=request_filled.json,
            data=request_filled.data,
            **request_filled.kwargs,
        )
        assert executed is True

    async def test_execute(
        self, request_filled: RequestData, response_simple: Response[Any]
    ):
        executed = False

        class _Executor(AbstractExecutor[Any]):
            async def execute(self, request: RequestData) -> Response[Any]:
                nonlocal executed
                executed = True

                assert request == request_filled

                return response_simple

        executor = _Executor()

        await executor.execute(request_filled)
        assert executed is True

    async def test_start_close(self, response_simple: Response[Any]):
        executed_start = False
        executed_close = False

        class _Executor(AbstractExecutor[Any]):
            async def execute(self, request: RequestData) -> Response[Any]:
                return response_simple  # pragma: no cover

            async def start(self) -> None:
                await super().start()
                nonlocal executed_start
                executed_start = True

            async def close(self) -> None:
                await super().close()
                nonlocal executed_close
                executed_close = True

        executor = _Executor()

        await executor.start()
        assert executed_start is True

        await executor.close()
        assert executed_close is True

    async def test_ctx_manager(self, response_simple: Response[Any]):
        executed_start = False
        executed_close = False

        class _Executor(AbstractExecutor[Any]):
            async def execute(self, request: RequestData) -> Response[Any]:
                return response_simple  # pragma: no cover

            async def start(self) -> None:
                nonlocal executed_start
                executed_start = True

            async def close(self) -> None:
                nonlocal executed_close
                executed_close = True

        executor = _Executor()

        async with executor:
            pass

        assert executed_start is True
        assert executed_close is True

    async def test_generalize(self, response_simple: Response[Any]):
        class _Executor(AbstractExecutor[Any]):
            async def execute(self, request: RequestData) -> Response[Any]:
                return response_simple  # pragma: no cover

        base = _Executor()
        executor = base.generalize()

        assert_type(executor, AbstractExecutor[Any])
        assert isinstance(executor, AbstractExecutor)
        assert executor is base


class TestAddon:
    async def test_default_process_response(
        self, request_simple: RequestData, response_simple: Response[Any]
    ):
        class _Addon(Addon[Any]):
            async def before_request(self, request: RequestData) -> None:
                pass  # pragma: no cover

        addon = _Addon()

        response = await addon.process_response(request_simple, response_simple)
        assert response is response_simple

    async def test_default_process_error(self, request_simple: RequestData):
        class _Addon(Addon[Any]):
            async def before_request(self, request: RequestData) -> None:
                pass  # pragma: no cover

        addon = _Addon()

        result = await addon.process_error(request_simple, Exception("hi"))  # type: ignore[func-returns-value]
        assert result is None
