from typing import Generic

from extapi.http.abc import Retryable
from extapi.http.executors.retry import T
from extapi.http.types import Response


class Retry5xxAddon(Retryable[T], Generic[T]):
    async def need_retry(self, response: Response[T]) -> tuple[bool, float | None]:
        if response.status >= 500:
            return True, None

        return False, None


class Retry429Addon(Retryable[T], Generic[T]):
    async def need_retry(self, response: Response[T]) -> tuple[bool, float | None]:
        if response.status != 429:
            return False, None

        retry_after_s = response.headers.get("retry-after")
        if retry_after_s is not None:
            try:
                retry_after = float(retry_after_s)
            except ValueError:
                retry_after = None

            return True, retry_after

        return True, None
