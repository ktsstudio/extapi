import abc
from typing import Self


class AbstractSemaphore(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def acquire(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    async def release(self) -> None:
        raise NotImplementedError

    async def __aenter__(self) -> Self:
        await self.acquire()
        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.release()
        return None


class _DummySemaphore(AbstractSemaphore):
    async def acquire(self) -> None:
        return None

    async def release(self) -> None:
        return None


DummySemaphore = _DummySemaphore()


class ConcurrencyLimiter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def get_semaphore(self) -> AbstractSemaphore:
        raise NotImplementedError

    async def start(self) -> None:
        return None

    async def close(self) -> None:
        return None

    async def __aenter__(self) -> Self:
        await self.start()
        return self

    async def __aexit__(self, *args, **kwargs) -> None:
        await self.close()
