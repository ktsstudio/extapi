from typing import Any

import aiohttp

from extapi.http.abc import AbstractExecutor
from extapi.http.types import BackendResponseProtocol, RequestData, Response


class AiohttpResponseWrap(BackendResponseProtocol[aiohttp.ClientResponse]):
    __slots__ = ("_original",)

    def __init__(self, response: aiohttp.ClientResponse):
        self._original = response

    def original(self) -> aiohttp.ClientResponse:
        return self._original

    async def close(self) -> None:
        self._original.release()
        await self._original.wait_for_close()

    async def read(self) -> bytes:
        return await self._original.read()


class AiohttpExecutor(AbstractExecutor[aiohttp.ClientResponse]):
    __slots__ = (
        "_ssl",
        "_session",
        "_default_timeout",
    )

    def __init__(
        self, *args, ssl: bool | Any = True, default_timeout: float = 10.0, **kwargs
    ):
        super().__init__()
        self._ssl = ssl
        self._session = aiohttp.ClientSession(*args, **kwargs)
        self._default_timeout = default_timeout

    async def close(self):
        await self._session.close()

    async def execute(self, request: RequestData) -> Response[aiohttp.ClientResponse]:
        timeout = request.timeout or self._default_timeout

        response = await self._session.request(
            method=request.method,
            url=request.url,
            params=request.params,
            json=request.json,
            data=request.data,
            headers=request.headers,
            timeout=timeout,  # type: ignore[arg-type]
            ssl=self._ssl,
            **request.kwargs,
        )

        return Response[aiohttp.ClientResponse](
            url=request.url,
            status=response.status,
            headers=response.headers.copy(),
            backend_response=AiohttpResponseWrap(response),
        )
