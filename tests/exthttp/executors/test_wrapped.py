from extapi.http.executors.wrapped import WrappedExecutor
from extapi.http.types import RequestData
from tests.exthttp._helpers import DummyExecutor


class TestWrappedExecutor:
    async def test_wrapped_executor(self, request_simple: RequestData):
        base = DummyExecutor(200)
        executor = WrappedExecutor(base)

        resp = await executor.execute(request_simple)
        assert resp.status == 200
        assert resp.url == request_simple.url
