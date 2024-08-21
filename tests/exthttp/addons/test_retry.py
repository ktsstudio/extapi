from typing import Any

import pytest
from multidict import CIMultiDict
from yarl import URL

from extapi.http.addons.retry import Retry5xxAddon, Retry429Addon
from extapi.http.types import Response
from tests.exthttp._helpers import DummyBackendResponse


class TestRetry5xx:
    @pytest.mark.parametrize("status", [200, 201, 301, 400, 401, 403, 404])
    async def test_ok(self, status: int):
        addon = Retry5xxAddon[Any]()

        response = Response(
            url=URL("http://example.com"),
            status=status,
            backend_response=DummyBackendResponse(),
        )
        need_retry, timeout = await addon.need_retry(response)

        assert need_retry is False
        assert timeout is None

    @pytest.mark.parametrize(
        "status", [500, 501, 502, 503, 504, 505, 506, 507, 508, 509, 510]
    )
    async def test_5xx(self, status: int):
        addon = Retry5xxAddon[Any]()

        response = Response(
            url=URL("http://example.com"),
            status=status,
            backend_response=DummyBackendResponse(),
        )

        need_retry, timeout = await addon.need_retry(response)

        assert need_retry is True
        assert timeout is None


class TestRetry429:
    async def test_ok(self, response_simple: Response[Any]):
        addon = Retry429Addon[Any]()

        need_retry, timeout = await addon.need_retry(response_simple)

        assert need_retry is False
        assert timeout is None

    async def test_429_no_header(self):
        addon = Retry429Addon[Any]()

        response = Response(
            url=URL("http://example.com"),
            status=429,
            backend_response=DummyBackendResponse(),
        )

        need_retry, timeout = await addon.need_retry(response)

        assert need_retry is True
        assert timeout is None

    async def test_429_with_header(self):
        addon = Retry429Addon[Any]()

        response = Response(
            url=URL("http://example.com"),
            status=429,
            backend_response=DummyBackendResponse(),
            headers=CIMultiDict({"retry-after": "42"}),
        )

        need_retry, timeout = await addon.need_retry(response)

        assert need_retry is True
        assert timeout == 42.0

    async def test_429_with_header_invalid(self):
        addon = Retry429Addon[Any]()

        response = Response(
            url=URL("http://example.com"),
            status=429,
            backend_response=DummyBackendResponse(),
            headers=CIMultiDict({"retry-after": "invalid-number"}),
        )

        need_retry, timeout = await addon.need_retry(response)

        assert need_retry is True
        assert timeout is None
