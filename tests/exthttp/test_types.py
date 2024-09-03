from typing import Any

from multidict import CIMultiDict
from yarl import URL

from extapi.http.types import BackendResponseProtocol, Response
from tests.exthttp._helpers import DummyBackendResponse


class TestResponse:
    async def test_has_data(self):
        response = Response(
            method="GET",
            url=URL("example.com"),
            status=200,
            backend_response=DummyBackendResponse(b"some-data"),
        )

        assert response.status == 200
        assert response.headers == CIMultiDict()
        assert await response.read() == b"some-data"

    async def test_json(self):
        response = Response(
            method="GET",
            url=URL("example.com"),
            status=200,
            backend_response=DummyBackendResponse(b'{"a": 1, "b": [10, 20]}'),
        )

        assert response.status == 200
        assert response.headers == CIMultiDict()
        assert await response.json() == {
            "a": 1,
            "b": [10, 20],
        }

        assert await response.json(encoding="latin-1") == {
            "a": 1,
            "b": [10, 20],
        }

    async def test_has_data_double(self):
        response = Response(
            method="GET",
            url=URL("example.com"),
            status=200,
            backend_response=DummyBackendResponse(b"some-data"),
        )

        assert response.status == 200
        assert response.headers == CIMultiDict()
        assert await response.read() == b"some-data"
        assert await response.read() == b"some-data"

    async def test_ctx_mgr_not_closable(self):
        response = Response(
            method="GET",
            url=URL("example.com"),
            status=200,
            backend_response=DummyBackendResponse(),
        )

        async with response as resp:
            assert resp is response

    async def test_ctx_mgr_closable_inherited(self):
        called = False

        class _Resp(BackendResponseProtocol[bytes]):
            def original(self) -> bytes:
                return b""  # pragma: no cover

            async def close(self) -> None:
                nonlocal called
                called = True

            async def read(self) -> bytes:
                return b""  # pragma: no cover

        response = Response(
            method="GET", url=URL("example.com"), status=200, backend_response=_Resp()
        )

        async with response as resp:
            assert resp is response
            assert isinstance(resp.backend_response, _Resp)
            assert resp.original == b""

        assert called is True

    async def test_ctx_mgr_closable_not_inherited(self):
        called = False

        class _Resp:
            def original(self) -> bytes:
                return b""  # pragma: no cover

            async def close(self) -> None:
                nonlocal called
                called = True

            async def read(self) -> bytes:
                return b""  # pragma: no cover

            async def json(self, **kwargs) -> Any:
                return None  # pragma: no cover

        response = Response(
            method="GET", url=URL("example.com"), status=200, backend_response=_Resp()
        )

        async with response as resp:
            assert resp is response
            assert isinstance(resp.backend_response, _Resp)
            assert resp.original == b""

        assert called is True
