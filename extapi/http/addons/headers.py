from collections.abc import Callable
from typing import Awaitable, TypeVar

from multidict import CIMultiDict

from extapi._helpers import execute_sync_async
from extapi.http.abc import Addon
from extapi.http.types import RequestData

AsyncHeadersAdder = Callable[[CIMultiDict], Awaitable[None]]
SyncHeadersAdder = Callable[[CIMultiDict], None]

T = TypeVar("T")


class AddHeadersAddon(Addon[T]):
    __slots__ = ("_adder",)

    def __init__(
        self,
        adder: AsyncHeadersAdder | SyncHeadersAdder,
    ):
        self._adder = adder

    async def before_request(self, request: RequestData) -> None:
        request.headers = request.headers or CIMultiDict()
        await execute_sync_async(self._adder, request.headers)
