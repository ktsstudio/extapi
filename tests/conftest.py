from typing import Any

import pytest

from extapi.http.types import RequestData, Response


@pytest.fixture
def request_simple() -> RequestData:
    return RequestData(
        method="GET",
        url="https://example.com",
    )


@pytest.fixture
def response_simple(request_simple: RequestData) -> Response[Any]:
    return Response(
        url=request_simple.url,
        status=200,
        backend_response=None,
        _data=b"",
    )
