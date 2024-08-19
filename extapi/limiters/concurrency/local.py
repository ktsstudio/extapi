import asyncio

from .abc import AbstractSemaphore, ConcurrencyLimiter, DummySemaphore


class _LocalSemaphore(AbstractSemaphore):
    def __init__(self, semaphore: asyncio.Semaphore):
        self._semaphore = semaphore

    async def acquire(self) -> None:
        await self._semaphore.acquire()

    async def release(self) -> None:
        self._semaphore.release()


class LocalConcurrencyLimiter(ConcurrencyLimiter):
    __slots__ = ("_semaphore",)

    def __init__(
        self,
        max_concurrency: int | None = None,
    ) -> None:
        self._semaphore = (
            asyncio.Semaphore(max_concurrency) if max_concurrency is not None else None
        )

    def get_semaphore(self) -> AbstractSemaphore:
        return (
            _LocalSemaphore(self._semaphore)
            if self._semaphore is not None
            else DummySemaphore
        )
