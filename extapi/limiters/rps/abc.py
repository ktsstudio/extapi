import abc
from typing import Self


class RateLimiter(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    async def limit_rps(self):
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
        return
