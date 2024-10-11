import abc
from typing import Protocol

from extapi._meta import PY311

if PY311:
    from typing import Self  # type: ignore[attr-defined]
else:
    from typing_extensions import Self


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


class ConcurrencyLimiter(Protocol):
    def get_semaphore(self) -> AbstractSemaphore: ...
