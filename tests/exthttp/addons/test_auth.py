from base64 import b64encode
from functools import partial
from typing import Any

from extapi.http.addons.auth import (
    BearerAuthAddon,
    StaticBasicAuthAddon,
    StaticBearerAuthAddon,
)
from extapi.http.types import RequestData, Response
from tests.exthttp._helpers import DummyBackendResponse


class TestBearerAuthAddon:
    async def test_sync_partial(self, request_simple: RequestData):
        def getter(arg: str) -> str:
            return arg

        addon = BearerAuthAddon[Any](partial(getter, arg="test"))
        await addon.before_request(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["Authorization"] == "Bearer test"

    async def test_async_partial(self, request_simple: RequestData):
        async def getter(arg: str) -> str:
            return arg

        addon = BearerAuthAddon[Any](partial(getter, arg="test"))
        await addon.before_request(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["Authorization"] == "Bearer test"

    async def test_sync_func(self, request_simple: RequestData):
        def getter() -> str:
            return "test"

        addon = BearerAuthAddon[Any](getter)
        await addon.before_request(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["Authorization"] == "Bearer test"

    async def test_async_func(self, request_simple: RequestData):
        async def getter() -> str:
            return "test"

        addon = BearerAuthAddon[Any](getter)
        await addon.before_request(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["Authorization"] == "Bearer test"

    async def test_sync_callable(self, request_simple: RequestData):
        class Getter:
            def __call__(self) -> str:
                return "test"

        addon = BearerAuthAddon[Any](Getter())
        await addon.before_request(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["Authorization"] == "Bearer test"

    async def test_async_callable(self, request_simple: RequestData):
        class Getter:
            async def __call__(self) -> str:
                return "test"

        addon = BearerAuthAddon[Any](Getter())
        await addon.before_request(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["Authorization"] == "Bearer test"

    async def test_need_retry_200(self, request_simple: RequestData):
        def getter() -> str:
            return "test"  # pragma: no cover

        addon = BearerAuthAddon[Any](getter)
        need_retry, timeout = await addon.need_retry(
            Response(
                method=request_simple.method,
                url=request_simple.url,
                status=200,
                backend_response=DummyBackendResponse(),
            )
        )

        assert need_retry is False
        assert timeout is None

    async def test_need_retry_401(self, request_simple: RequestData):
        def getter() -> str:
            return "test"  # pragma: no cover

        addon = BearerAuthAddon[Any](getter)
        need_retry, timeout = await addon.need_retry(
            Response(
                method=request_simple.method,
                url=request_simple.url,
                status=401,
                backend_response=DummyBackendResponse(),
            )
        )

        assert need_retry is True
        assert timeout is None


class TestStaticBearerAuthAddon:
    async def test_ok(self, request_simple: RequestData):
        addon = StaticBearerAuthAddon[Any]("test-token")
        await addon.before_request(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["Authorization"] == "Bearer test-token"

    async def test_need_retry(self, request_simple: RequestData):
        addon = StaticBearerAuthAddon[Any]("test-token")
        need_retry, timeout = await addon.need_retry(
            Response(
                method=request_simple.method,
                url=request_simple.url,
                status=401,
                backend_response=DummyBackendResponse(),
            )
        )

        assert need_retry is False
        assert timeout is None


class TestStaticBasicAuthAddon:
    async def test_ok(self, request_simple: RequestData):
        login = "test-login"
        password = "test-password"
        creds = b64encode(f"{login}:{password}".encode("utf-8")).decode("utf-8")

        addon = StaticBasicAuthAddon[Any](login=login, password=password)
        await addon.before_request(request_simple)

        assert request_simple.headers is not None
        assert request_simple.headers["Authorization"] == f"Basic {creds}"

    async def test_need_retry(self, request_simple: RequestData):
        login = "test-login"
        password = "test-password"

        addon = StaticBasicAuthAddon[Any](login=login, password=password)
        need_retry, timeout = await addon.need_retry(
            Response(
                method=request_simple.method,
                url=request_simple.url,
                status=401,
                backend_response=DummyBackendResponse(),
            )
        )

        assert need_retry is False
        assert timeout is None
