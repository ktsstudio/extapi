import abc
from typing import Any, Generic, Protocol, Self, TypeVar, runtime_checkable

from multidict import CIMultiDict

from .types import RequestData, Response, StrOrURL

T = TypeVar("T")


class AbstractExecutor(Generic[T], metaclass=abc.ABCMeta):
    async def start(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    def generalize(self) -> "AbstractExecutor[T]":
        return self

    @abc.abstractmethod
    async def execute(
        self,
        request: RequestData,
    ) -> Response[T]:
        raise NotImplementedError  # pragma: no cover

    async def get(
        self,
        url: StrOrURL,
        *,
        params: dict[str, str] | None = None,
        json: Any = None,
        data: Any = None,
        headers: CIMultiDict | None = None,
        timeout: Any | float | None = None,
        **kwargs,
    ) -> Response[T]:
        return await self.execute(
            RequestData(
                method="GET",
                url=url,
                params=params,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout,
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
        headers: CIMultiDict | None = None,
        timeout: Any | float | None = None,
        **kwargs,
    ) -> Response[T]:
        return await self.execute(
            RequestData(
                method="POST",
                url=url,
                params=params,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout,
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
        headers: CIMultiDict | None = None,
        timeout: Any | float | None = None,
        **kwargs,
    ) -> Response[T]:
        return await self.execute(
            RequestData(
                method="DELETE",
                url=url,
                params=params,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout,
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
        headers: CIMultiDict | None = None,
        timeout: Any | float | None = None,
        **kwargs,
    ) -> Response[T]:
        return await self.execute(
            RequestData(
                method="PUT",
                url=url,
                params=params,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout,
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
        headers: CIMultiDict | None = None,
        timeout: Any | float | None = None,
        **kwargs,
    ) -> Response[T]:
        return await self.execute(
            RequestData(
                method="PATCH",
                url=url,
                params=params,
                json=json,
                data=data,
                headers=headers,
                timeout=timeout,
                kwargs=kwargs,
            )
        )


@runtime_checkable
class Retryable(Protocol[T]):
    async def need_retry(self, response: Response[T]) -> tuple[bool, float | None]: ...


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
