from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

from multidict import CIMultiDict

from extapi._helpers import execute_sync_async
from extapi.http.abc import Addon, Retryable
from extapi.http.types import RequestData, Response

T = TypeVar("T")


AsyncBearerTokenGetter = Callable[[], Awaitable[str]]
SyncBearerTokenGetter = Callable[[], str]


class BearerAuthAddon(Addon[T], Retryable[T], Generic[T]):
    __slots__ = ("_token_getter",)

    def __init__(
        self,
        token_getter: SyncBearerTokenGetter | AsyncBearerTokenGetter,
    ):
        self._token_getter = token_getter

    async def need_retry(self, response: Response[T]) -> tuple[bool, float | None]:
        if response.status == 401:
            return True, None
        return False, None

    async def enrich(self, request: RequestData) -> None:
        request.headers = request.headers or CIMultiDict()

        token = await execute_sync_async(self._token_getter)
        request.headers["Authorization"] = f"Bearer {token}"


class StaticBearerAuthAddon(BearerAuthAddon[T], Generic[T]):
    def __init__(self, token: str):
        super().__init__(lambda: token)

    async def need_retry(self, response: Response[T]) -> tuple[bool, float | None]:
        return False, None
