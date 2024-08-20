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

T = TypeVar("T")


@dataclass(slots=True, kw_only=True)
class RequestData:
    method: HttpMethod
    url: StrOrURL
    params: dict[str, str] | None = None
    json: Any = None
    data: Any = None
    headers: CIMultiDict | None = None
    timeout: Any | float | None = None
    kwargs: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class Closable(Protocol):
    async def close(self) -> None: ...


@dataclass(kw_only=True)
class Response(Generic[T]):
    url: StrOrURL
    status: int
    headers: CIMultiDict = field(default_factory=lambda: CIMultiDict())
    backend_response: T
    _data: bytes | None = None

    @property
    def has_data(self) -> bool:
        return self._data is not None

    @property
    def data(self) -> bytes:
        if self._data is None:
            raise ValueError("data is not available")
        return self._data

    def set_data(self, data: bytes) -> None:
        self._data = data

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if isinstance(self.backend_response, Closable):
            await self.backend_response.close()


class ExecuteError(Exception):
    pass


class HttpExecuteError(ExecuteError):
    def __init__(self, response: Response):
        self.response = response

    def __str__(self):
        return f"HTTPExecuteError(url={self.response.url}, status={self.response.status})"  # pragma: no cover
