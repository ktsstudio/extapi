from typing import Any

import aiohttp

from extapi.http.abc import AbstractExecutor
from extapi.http.types import RequestData, Response, Closable


class AiohttpResponseWrap(Closable):
    __slots__ = ("original",)

    def __init__(self, response: aiohttp.ClientResponse):
        self.original = response

    async def close(self) -> None:
        self.original.release()
        await self.original.wait_for_close()


class AiohttpStreamingExecutor(AbstractExecutor[AiohttpResponseWrap]):
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

    async def execute(self, request: RequestData) -> Response[AiohttpResponseWrap]:
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

        return Response[AiohttpResponseWrap](
            url=request.url,
            status=response.status,
            headers=response.headers.copy(),
            backend_response=AiohttpResponseWrap(response),
        )


class AiohttpExecutor(AiohttpStreamingExecutor):
    async def execute(self, request: RequestData) -> Response[AiohttpResponseWrap]:
        resp = await super().execute(request)
        async with resp:
            resp.set_data(await resp.backend_response.original.read())
        return resp
