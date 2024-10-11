import abc
from collections.abc import Mapping
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

from multidict import CIMultiDict
from yarl import URL

from extapi._meta import PY311

from .types import RequestData, Response, StrOrURL

if PY311:
    from typing import Self  # type: ignore[attr-defined]
else:
    from typing_extensions import Self

T_co = TypeVar("T_co", covariant=True)
T_contr = TypeVar("T_contr", contravariant=True)
T = TypeVar("T")


class AbstractExecutor(Generic[T_co], metaclass=abc.ABCMeta):
    async def start(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def generalize(self) -> "AbstractExecutor[T_co]":
        return self

    @abc.abstractmethod
    async def execute(
        self,
        request: RequestData,
    ) -> Response[T_co]:
        raise NotImplementedError  # pragma: no cover

    async def get(
        self,
        url: StrOrURL,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        headers: CIMultiDict | Mapping[str, Any] | None = None,
        timeout: Any | float | None = None,
        auto_read_body: bool | None = None,
        **kwargs,
    ) -> Response[T_co]:
        return await self.execute(
            RequestData(
                method="GET",
                url=URL(url) if isinstance(url, str) else url,
                params=params,
                json=json,
                data=data,
                headers=_map_headers(headers),
                timeout=timeout,
                auto_read_body=auto_read_body,
                kwargs=kwargs,
            )
        )

    async def post(
        self,
        url: StrOrURL,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        headers: CIMultiDict | Mapping[str, Any] | None = None,
        timeout: Any | float | None = None,
        auto_read_body: bool | None = None,
        **kwargs,
    ) -> Response[T_co]:
        return await self.execute(
            RequestData(
                method="POST",
                url=URL(url) if isinstance(url, str) else url,
                params=params,
                json=json,
                data=data,
                headers=_map_headers(headers),
                timeout=timeout,
                auto_read_body=auto_read_body,
                kwargs=kwargs,
            )
        )

    async def delete(
        self,
        url: StrOrURL,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        headers: CIMultiDict | Mapping[str, Any] | None = None,
        timeout: Any | float | None = None,
        auto_read_body: bool | None = None,
        **kwargs,
    ) -> Response[T_co]:
        return await self.execute(
            RequestData(
                method="DELETE",
                url=URL(url) if isinstance(url, str) else url,
                params=params,
                json=json,
                data=data,
                headers=_map_headers(headers),
                timeout=timeout,
                auto_read_body=auto_read_body,
                kwargs=kwargs,
            )
        )

    async def put(
        self,
        url: StrOrURL,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        headers: CIMultiDict | Mapping[str, Any] | None = None,
        timeout: Any | float | None = None,
        auto_read_body: bool | None = None,
        **kwargs,
    ) -> Response[T_co]:
        return await self.execute(
            RequestData(
                method="PUT",
                url=URL(url) if isinstance(url, str) else url,
                params=params,
                json=json,
                data=data,
                headers=_map_headers(headers),
                timeout=timeout,
                auto_read_body=auto_read_body,
                kwargs=kwargs,
            )
        )

    async def patch(
        self,
        url: StrOrURL,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        headers: CIMultiDict | Mapping[str, Any] | None = None,
        timeout: Any | float | None = None,
        auto_read_body: bool | None = None,
        **kwargs,
    ) -> Response[T_co]:
        return await self.execute(
            RequestData(
                method="PATCH",
                url=URL(url) if isinstance(url, str) else url,
                params=params,
                json=json,
                data=data,
                headers=_map_headers(headers),
                timeout=timeout,
                auto_read_body=auto_read_body,
                kwargs=kwargs,
            )
        )


def _map_headers(headers: CIMultiDict | Mapping[str, Any] | None) -> CIMultiDict | None:
    if headers is None:
        return None

    if isinstance(headers, CIMultiDict):
        return headers

    return CIMultiDict(headers)


@runtime_checkable
class Retryable(Protocol[T_contr]):
    async def need_retry(
        self, response: Response[T_contr]
    ) -> tuple[bool, float | None]: ...


@runtime_checkable
class Addon(Protocol[T]):
    async def before_request(self, request: RequestData) -> None:
        return None

    async def process_response(
        self, request: RequestData, response: Response[T]
    ) -> Response[T]:
        return response

    async def process_error(self, request: RequestData, error: Exception) -> None:
        return None
