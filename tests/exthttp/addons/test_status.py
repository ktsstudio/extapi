from typing import Any

import pytest
from yarl import URL

from extapi.http.addons.status import StatusValidationAddon
from extapi.http.types import HttpExecuteError, RequestData, Response
from tests.exthttp._helpers import DummyBackendResponse


class TestStatusValidationAddon:
    @pytest.mark.parametrize("status", [200, 201])
    async def test_ok_status_default(self, request_simple: RequestData, status: int):
        response = Response(
            method="GET",
            url=URL("http://example.com"),
            status=status,
            backend_response=DummyBackendResponse(),
        )
        addon = StatusValidationAddon[Any]()
        processed_response = await addon.process_response(request_simple, response)
        assert processed_response is response

    @pytest.mark.parametrize("status", [400, 403])
    async def test_ok_status_custom(self, request_simple: RequestData, status: int):
        response = Response(
            method="GET",
            url=URL("http://example.com"),
            status=status,
            backend_response=DummyBackendResponse(),
        )
        addon = StatusValidationAddon[Any](expected_statuses=[400, 403])
        processed_response = await addon.process_response(request_simple, response)
        assert processed_response is response

    @pytest.mark.parametrize("status", [400, 500, 307, 201])
    async def test_error_status(self, request_simple: RequestData, status: int):
        response = Response(
            method="GET",
            url=URL("http://example.com"),
            status=status,
            backend_response=DummyBackendResponse(),
        )
        addon = StatusValidationAddon[Any](expected_statuses=[200])

        with pytest.raises(HttpExecuteError) as err:
            await addon.process_response(request_simple, response)

        assert err.value.response is response
