from typing import Any

from multidict import CIMultiDict

from extapi.http.types import BackendResponseProtocol, Response
from tests.exthttp._helpers import DummyBackendResponse


class TestResponse:
    async def test_has_data(self):
        response = Response(
            url="example.com",
            status=200,
            backend_response=DummyBackendResponse(b"some-data"),
        )

        assert response.status == 200
        assert response.headers == CIMultiDict()
        assert await response.read() == b"some-data"

    async def test_has_data_double(self):
        response = Response(
            url="example.com",
            status=200,
            backend_response=DummyBackendResponse(b"some-data"),
        )

        assert response.status == 200
        assert response.headers == CIMultiDict()
        assert response._data is None
        assert await response.read() == b"some-data"
        assert response._data is not None
        assert await response.read() == b"some-data"

    async def test_ctx_mgr_not_closable(self):
        response = Response[Any](
            url="example.com", status=200, backend_response=DummyBackendResponse()
        )

        async with response as resp:
            assert resp is response

    async def test_ctx_mgr_closable_inherited(self):
        called = False

        class _Resp(BackendResponseProtocol[bytes]):
            def original(self) -> bytes:
                return b""

            async def close(self) -> None:
                nonlocal called
                called = True

            async def read(self) -> bytes:
                return b""  # pragma: no cover

        response = Response[Any](
            url="example.com", status=200, backend_response=_Resp()
        )

        async with response as resp:
            assert resp is response
            assert isinstance(resp.backend_response, _Resp)

        assert called is True

    async def test_ctx_mgr_closable_not_inherited(self):
        called = False

        class _Resp:
            def original(self) -> bytes:
                return b""

            async def close(self) -> None:
                nonlocal called
                called = True

            async def read(self) -> bytes:
                return b""  # pragma: no cover

        response = Response[Any](
            url="example.com", status=200, backend_response=_Resp()
        )

        async with response as resp:
            assert resp is response
            assert isinstance(resp.backend_response, _Resp)

        assert called is True
