from dataclasses import dataclass, field
from typing import (
    Any,
    Generic,
    Literal,
    Protocol,
    Self,
    TypeVar,
    runtime_checkable,
)

from multidict import CIMultiDict
from yarl import URL

HttpMethod = Literal["GET", "POST", "PUT", "PATCH", "DELETE"] | str
StrOrURL = str | URL


@dataclass(slots=True, kw_only=True)
class RequestData:
    method: HttpMethod
    url: StrOrURL
    params: dict[str, Any] | None = None
    json: Any = None
    data: Any = None
    headers: CIMultiDict | None = None
    timeout: Any | float | None = None
    kwargs: dict[str, Any] = field(default_factory=dict)


T = TypeVar("T", covariant=True)


@runtime_checkable
class BackendResponseProtocol(Protocol[T]):
    def original(self) -> T: ...
    async def close(self) -> None: ...
    async def read(self) -> bytes: ...


@dataclass(kw_only=True)
class Response(Generic[T]):
    url: StrOrURL
    status: int
    headers: CIMultiDict = field(default_factory=lambda: CIMultiDict())
    backend_response: BackendResponseProtocol[T]

    _data: bytes | None = None

    async def read(self) -> bytes:
        if self._data is not None:
            return self._data

        self._data = await self.backend_response.read()
        return self._data

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.backend_response.close()


class ExecuteError(Exception):
    pass


class HttpExecuteError(ExecuteError):
    def __init__(self, response: Response):
        self.response = response

    def __str__(self):  # pragma: no cover
        return (
            f"HTTPExecuteError(url={self.response.url}, status={self.response.status})"
        )
