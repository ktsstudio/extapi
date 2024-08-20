import abc
from collections.abc import Sequence
from typing import Any

import httpx
from multidict import CIMultiDict
from yarl import URL

from extapi.http.abc import AbstractExecutor
from extapi.http.types import Closable, RequestData, Response


class HttpxResponseWrap(Closable):
    __slots__ = ("original",)

    def __init__(self, response: httpx.Response):
        self.original = response

    async def close(self) -> None:
        return await self.original.aclose()


class _BaseHttpxExecutor(AbstractExecutor[HttpxResponseWrap], metaclass=abc.ABCMeta):
    __slots__ = (
        "_client",
        "_default_timeout",
    )

    def __init__(
        self, *, check_ssl: bool = True, default_timeout: float = 10.0, **kwargs
    ):
        super().__init__()
        verify = kwargs.pop("verify", None)
        if verify is None:
            verify = check_ssl
        self._client = httpx.AsyncClient(verify=verify, **kwargs)
        self._default_timeout = default_timeout

    async def close(self):
        await self._client.aclose()

    async def execute(self, request: RequestData) -> Response[HttpxResponseWrap]:
        timeout = request.timeout or self._default_timeout
        url = request.url

        if isinstance(url, URL):
            url = str(url)

        if request.headers is None:
            httpx_headers = []
        else:
            httpx_headers = [(k, str(v)) for k, v in request.headers.items()]

        return await self._get_response(
            method=request.method,
            url=url,
            params=request.params,
            json=request.json,
            data=request.data,
            headers=httpx_headers,
            timeout=timeout,
            **request.kwargs,
        )

    @abc.abstractmethod
    async def _get_response(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        headers: Sequence[tuple[str, str]],
        timeout: Any | float | None = None,
        **kwargs,
    ) -> Response[HttpxResponseWrap]:
        raise NotImplementedError


class HttpxExecutor(_BaseHttpxExecutor):
    async def _get_response(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        headers: Sequence[tuple[str, str]],
        timeout: Any | float | None = None,
        **kwargs,
    ) -> Response[HttpxResponseWrap]:
        response = await self._client.request(
            method=method,
            url=url,
            params=params,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout,  # type: ignore[arg-type]
            **kwargs,
        )

        result = Response[HttpxResponseWrap](
            url=url,
            status=response.status_code,
            headers=CIMultiDict(response.headers),
            backend_response=HttpxResponseWrap(response),
        )
        result.set_data(response.content)
        return result


class HttpxStreamingExecutor(_BaseHttpxExecutor):
    async def _get_response(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        headers: Sequence[tuple[str, str]],
        timeout: Any | float | None = None,
        **kwargs,
    ) -> Response[HttpxResponseWrap]:
        response = await self._client.stream(
            method=method,
            url=url,
            params=params,
            json=json,
            data=data,
            headers=headers,
            timeout=timeout,
            **kwargs,
        ).__aenter__()

        return Response[HttpxResponseWrap](
            url=url,
            status=response.status_code,
            headers=CIMultiDict(response.headers),
            backend_response=HttpxResponseWrap(response),
        )
