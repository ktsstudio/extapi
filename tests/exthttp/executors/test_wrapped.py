import pytest

from extapi.http.executors.wrapped import WrappedExecutor, unwrap_executor
from extapi.http.types import RequestData
from tests.exthttp._helpers import DummyExecutor


class TestWrappedExecutor:
    async def test_wrapped_executor(self, request_simple: RequestData):
        base = DummyExecutor(200)
        executor = WrappedExecutor(base)

        resp = await executor.execute(request_simple)
        assert resp.status == 200
        assert resp.url == request_simple.url


class TestGetBackend:
    async def test_unwrap_bare(self, request_simple: RequestData):
        base = DummyExecutor(200)

        backend = unwrap_executor(base)
        assert backend is base

    async def test_unwrap_wrapped(self, request_simple: RequestData):
        base = DummyExecutor(200)
        executor = WrappedExecutor(base)

        backend = unwrap_executor(executor)
        assert backend is base

    async def test_unwrap_wrapped_multi(self, request_simple: RequestData):
        base = DummyExecutor(200)
        executor = base.generalize()
        for _ in range(100):
            executor = WrappedExecutor(executor)

        backend = unwrap_executor(executor)
        assert backend is base

    async def test_unwrap_wrapped_cycle(self, request_simple: RequestData):
        base = DummyExecutor(200)
        executor = base

        executor1 = WrappedExecutor(executor)
        executor2 = WrappedExecutor(executor1)
        executor1._executor = executor2

        with pytest.raises(RuntimeError) as err:
            unwrap_executor(executor2)
        assert str(err.value) == "Circular reference in executors detected"
