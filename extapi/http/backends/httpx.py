import abc

import httpx
from multidict import CIMultiDict

from extapi.http.abc import AbstractExecutor
from extapi.http.types import (
    BackendResponseProtocol,
    RequestData,
    Response,
)


class HttpxResponseWrap(BackendResponseProtocol[httpx.Response]):
    __slots__ = ("_original",)

    def __init__(self, response: httpx.Response):
        self._original = response

    def original(self) -> httpx.Response:
        return self._original

    async def close(self) -> None:
        return await self._original.aclose()

    async def read(self) -> bytes:
        return await self._original.aread()


_httpx_extra_kwargs = [
    "content",
    "files",
    "cookies",
    "auth",
    "follow_redirects",
    "extensions",
]


class HttpxExecutor(AbstractExecutor[httpx.Response], metaclass=abc.ABCMeta):
    __slots__ = (
        "_client",
        "_default_timeout",
    )

    def __init__(
        self,
        *,
        ssl: bool = True,
        default_timeout: float = 10.0,
        follow_redirects: bool = True,
        **kwargs,
    ):
        super().__init__()
        verify = kwargs.pop("verify", None)
        if verify is None:
            verify = ssl
        self._client = self._make_client(
            verify=verify, follow_redirects=follow_redirects, **kwargs
        )
        self._default_timeout = default_timeout

    def _make_client(self, *args, **kwargs) -> httpx.AsyncClient:
        return httpx.AsyncClient(*args, **kwargs)

    async def close(self):
        await self._client.aclose()

    async def execute(self, request: RequestData) -> Response[httpx.Response]:
        timeout = request.timeout or self._default_timeout
        url = str(request.url)

        if request.headers is None:
            httpx_headers = []
        else:
            httpx_headers = [(k, str(v)) for k, v in request.headers.items()]

        # httpx-specific kwargs
        # we need to pull them individually because
        # we may have our own custom kwargs
        httpx_kwargs = {
            key: request.kwargs[key]
            for key in _httpx_extra_kwargs
            if key in request.kwargs
        }

        response = await self._client.stream(
            method=request.method,
            url=url,
            params=request.params,
            json=request.json,
            data=request.data,
            headers=httpx_headers,
            timeout=timeout,
            **httpx_kwargs,
        ).__aenter__()

        return Response[httpx.Response](
            method=request.method,
            url=request.url,
            status=response.status_code,
            headers=CIMultiDict(response.headers),
            backend_response=HttpxResponseWrap(response),
        )
