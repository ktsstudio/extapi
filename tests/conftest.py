from collections.abc import AsyncIterable
from typing import Any

import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from multidict import CIMultiDict
from yarl import URL

from extapi.http.types import RequestData, Response
from tests.exthttp._helpers import DummyBackendResponse


@pytest.fixture
def request_simple() -> RequestData:
    return RequestData(
        method="GET",
        url=URL("https://example.com"),
    )


@pytest.fixture
def request_filled() -> RequestData:
    return RequestData(
        method="GET",
        url=URL("https://example.com/some/path"),
        headers=CIMultiDict({"X-Test-Header-1": "one", "X-Test-Header-2": "two"}),
        params={"param1": "one", "param2": "two"},
        json={"json1": "one", "json2": "two"},
        timeout=10.0,
        kwargs={"extra1": "test"},
    )


@pytest.fixture
def response_simple(request_simple: RequestData) -> Response[Any]:
    return Response(
        method=request_simple.method,
        url=request_simple.url,
        status=200,
        backend_response=DummyBackendResponse(),
        _data=b"",
    )


@pytest.fixture
async def dummy_server(
    aiohttp_unused_port, aiohttp_server
) -> AsyncIterable[TestServer]:
    app = web.Application()

    async def get(request):
        return web.json_response({"status": "ok"}, headers=request.headers)

    app.router.add_get("/get", get)

    server = await aiohttp_server(app, port=aiohttp_unused_port())
    yield server
