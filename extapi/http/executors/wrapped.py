from typing import Generic, TypeVar

from extapi.http.abc import AbstractExecutor
from extapi.http.types import RequestData, Response

T = TypeVar("T", covariant=True)


class WrappedExecutor(AbstractExecutor[T], Generic[T]):
    __slots__ = ("_executor",)

    def __init__(self, executor: AbstractExecutor[T]):
        self._executor = executor

    async def execute(self, request: RequestData) -> Response[T]:
        return await self._executor.execute(request)


def unwrap_executor(executor: AbstractExecutor[T]) -> AbstractExecutor[T]:
    seen = set()
    while True:
        if executor in seen:
            raise RuntimeError("Circular reference in executors detected")

        if isinstance(executor, WrappedExecutor):
            seen.add(executor)
            executor = executor._executor
        else:
            return executor
