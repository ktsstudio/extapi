from collections.abc import Callable
from typing import Any

import aiohttp

from extapi.http.abc import AbstractExecutor
from extapi.http.types import (
    DEFAULT_JSON_DECODER,
    BackendResponseProtocol,
    RequestData,
    Response,
)


class AiohttpResponseWrap(BackendResponseProtocol[aiohttp.ClientResponse]):
    __slots__ = ("_original", "_body")

    def __init__(self, response: aiohttp.ClientResponse, *, body: bytes | None = None):
        self._original = response
        self._body = body

    def original(self) -> aiohttp.ClientResponse:
        return self._original

    async def close(self) -> None:
        self._original.release()
        await self._original.wait_for_close()

    async def read(self) -> bytes:
        if self._body is not None:
            return self._body

        # if body is not supplied - delegate to original
        return await self._original.read()

    async def json(
        self,
        *,
        encoding: str | None,
        loads: Callable[[str], Any] = DEFAULT_JSON_DECODER,
    ) -> Any:
        # always delegate to original aiohttp.ClientResponse
        # because the data has already been read
        return await self._original.json(encoding=encoding, loads=loads)


_aiohttp_extra_kwargs = [
    "cookies",
    "skip_auto_headers",
    "auth",
    "allow_redirects",
    "max_redirects",
    "compress",
    "chunked",
    "expect100",
    "raise_for_status",
    "read_until_eof",
    "proxy",
    "proxy_auth",
    "server_hostname",
    "trace_request_ctx",
    "read_bufsize",
    "auto_decompress",
    "max_line_size",
    "max_field_size",
]


class AiohttpExecutor(AbstractExecutor[aiohttp.ClientResponse]):
    __slots__ = (
        "_ssl",
        "_session",
        "_default_timeout",
    )

    def __init__(
        self,
        *args,
        ssl: bool | Any = True,
        default_timeout: float = 10.0,
        auto_read_body: bool = True,
        **kwargs,
    ):
        super().__init__()
        self._ssl = ssl
        self._session = self._make_session(*args, **kwargs)
        self._default_timeout = default_timeout
        self._auto_read_body = auto_read_body

    def _make_session(self, *args, **kwargs) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(*args, **kwargs)

    async def close(self):
        await self._session.close()

    async def execute(self, request: RequestData) -> Response[aiohttp.ClientResponse]:
        timeout = request.timeout or self._default_timeout
        auto_read_body = (
            request.auto_read_body
            if request.auto_read_body is not None
            else self._auto_read_body
        )

        # aiohttp-specific kwargs
        # we need to pull them individually because
        # we may have our own custom kwargs
        aiohttp_kwargs = {
            key: request.kwargs[key]
            for key in _aiohttp_extra_kwargs
            if key in request.kwargs
        }

        response = await self._session.request(
            method=request.method,
            url=request.url,
            params=request.params,
            json=request.json,
            data=request.data,
            headers=request.headers,
            timeout=timeout,  # type: ignore[arg-type]
            ssl=self._ssl,
            **aiohttp_kwargs,
        )

        body: bytes | None = None
        if auto_read_body:
            body = await response.read()

        return Response[aiohttp.ClientResponse](
            method=request.method,
            url=request.url,
            status=response.status,
            headers=response.headers.copy(),
            backend_response=AiohttpResponseWrap(response, body=body),
        )
