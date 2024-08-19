from typing import Any

from multidict import CIMultiDict

from extapi.http.addons.headers import AddHeadersAddon
from extapi.http.types import RequestData


class TestHeadersAddon:
    async def test_sync_func(self, request_simple: RequestData):
        def adder(headers: CIMultiDict):
            headers["X-Test"] = "test"

        addon = AddHeadersAddon[Any](adder)
        await addon.enrich(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["X-Test"] == "test"

    async def test_sync_callable(self, request_simple: RequestData):
        class Adder:
            def __call__(self, headers: CIMultiDict):
                headers["X-Test"] = "test"

        addon = AddHeadersAddon[Any](Adder())
        await addon.enrich(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["X-Test"] == "test"

    async def test_async_func(self, request_simple: RequestData):
        async def adder(headers: CIMultiDict):
            headers["X-Test"] = "test"

        addon = AddHeadersAddon[Any](adder)
        await addon.enrich(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["X-Test"] == "test"

    async def test_async_callable(self, request_simple: RequestData):
        class Adder:
            async def __call__(self, headers: CIMultiDict):
                headers["X-Test"] = "test"

        addon = AddHeadersAddon[Any](Adder())
        await addon.enrich(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["X-Test"] == "test"
