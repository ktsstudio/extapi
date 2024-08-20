from base64 import b64encode
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

    async def before_request(self, request: RequestData) -> None:
        if request.headers is None:
            request.headers = CIMultiDict()

        token = await execute_sync_async(self._token_getter)
        request.headers["Authorization"] = f"Bearer {token}"


class StaticBearerAuthAddon(BearerAuthAddon[T], Generic[T]):
    def __init__(self, token: str):
        super().__init__(lambda: token)

    async def need_retry(self, response: Response[T]) -> tuple[bool, float | None]:
        return False, None


class StaticBasicAuthAddon(Addon[T], Retryable[T], Generic[T]):
    __slots__ = ("_login", "_password")

    def __init__(
        self,
        *,
        login: str,
        password: str,
    ):
        self._login = login
        self._password = password
        self.__header_value = "Basic " + self._generate_auth(
            self._login, self._password
        )

    def _generate_auth(self, login: str, password: str) -> str:
        return b64encode(f"{login}:{password}".encode("utf-8")).decode("utf-8")

    async def need_retry(self, response: Response[T]) -> tuple[bool, float | None]:
        return False, None

    async def before_request(self, request: RequestData) -> None:
        if request.headers is None:
            request.headers = CIMultiDict()
        request.headers["Authorization"] = self.__header_value
