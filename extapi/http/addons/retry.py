from typing import Generic, TypeVar

from extapi.http.abc import Retryable
from extapi.http.types import Response

T = TypeVar("T")


class Retry5xxAddon(Retryable[T], Generic[T]):
    __slots__ = ("_default_timeout",)

    def __init__(self, *, default_timeout: float | None = None):
        self._default_timeout = default_timeout

    async def need_retry(self, response: Response[T]) -> tuple[bool, float | None]:
        if response.status >= 500:
            return True, self._default_timeout

        return False, None


class Retry429Addon(Retryable[T], Generic[T]):
    __slots__ = ("_default_timeout",)

    def __init__(self, *, default_timeout: float | None = None):
        self._default_timeout = default_timeout

    async def need_retry(self, response: Response[T]) -> tuple[bool, float | None]:
        if response.status != 429:
            return False, None

        retry_after_s = response.headers.get("retry-after")
        if retry_after_s is not None:
            retry_after: float | None
            try:
                retry_after = float(retry_after_s)
            except ValueError:
                retry_after = self._default_timeout

            return True, retry_after

        return True, None
