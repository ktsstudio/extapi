from typing import Any

import pytest
from multidict import CIMultiDict

from extapi.http.types import Closable, Response


class TestResponse:
    def test_no_data(self):
        response = Response[Any](url="example.com", status=200, backend_response=None)
        assert response.status == 200
        assert response.headers == CIMultiDict()
        assert response.has_data is False

        with pytest.raises(ValueError) as e:
            _ = response.data

        assert str(e.value) == "data is not available"

    def test_has_data(self):
        response = Response[Any](url="example.com", status=200, backend_response=None)

        response.set_data(b"some-data")
        assert response.status == 200
        assert response.headers == CIMultiDict()
        assert response.has_data is True
        assert response.data == b"some-data"

    async def test_ctx_mgr_not_closable(self):
        response = Response[Any](url="example.com", status=200, backend_response=None)

        async with response as resp:
            assert resp is response

    async def test_ctx_mgr_closable_inherited(self):
        called = False

        class _Resp(Closable):
            async def close(self) -> None:
                nonlocal called
                called = True

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
            async def close(self) -> None:
                nonlocal called
                called = True

        response = Response[Any](
            url="example.com", status=200, backend_response=_Resp()
        )

        async with response as resp:
            assert resp is response
            assert isinstance(resp.backend_response, _Resp)

        assert called is True
