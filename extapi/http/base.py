from typing import Generic, TypeVar

from extapi.http.abc import AbstractExecutor
from extapi.http.types import RequestData, Response

T = TypeVar("T")


class WrappedExecutor(AbstractExecutor[T], Generic[T]):
    __slots__ = ("_executor",)

    def __init__(self, executor: AbstractExecutor[T]):
        super().__init__()
        self._executor = executor

    async def start(self) -> None:
        await self._executor.start()

    async def close(self) -> None:
        await self._executor.close()

    async def execute(self, request: RequestData) -> Response[T]:
        return await self._executor.execute(request)
