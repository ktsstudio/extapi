from typing import Protocol, runtime_checkable


@runtime_checkable
class RateLimiter(Protocol):
    async def rate_limit(self): ...
