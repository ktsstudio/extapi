import asyncio
import itertools
import logging
from collections.abc import Iterable
from types import EllipsisType
from typing import Generic, TypeVar

from extapi.http.abc import AbstractExecutor, Addon, Retryable
from extapi.http.types import ExecuteError, HttpExecuteError, RequestData, Response

from ..addons.log import LoggingAddon
from ..addons.retry import Retry5xxAddon, Retry429Addon
from .wrapped import WrappedExecutor

T = TypeVar("T", covariant=True)


def get_default_addons() -> list[Addon[T] | Retryable[T]]:
    return [
        Retry5xxAddon(),
        Retry429Addon(),
        LoggingAddon(),
    ]


class RetryableExecutor(WrappedExecutor[T], Generic[T]):
    __slots__ = (
        "_logger",
        "_max_retries",
        "_retry_sleep_timeout",
        "_log_retries",
        "_addons",
        "_retry_addons",
    )

    def __init__(
        self,
        executor: AbstractExecutor[T],
        *,
        max_retries: int = 3,
        retry_sleep_timeout: float = 3.0,
        log_retries: bool = True,
        addons: Iterable[Addon[T] | Retryable[T]] = (),
        default_addons: Iterable[Addon[T] | Retryable[T]] | EllipsisType = ...,
    ):
        assert max_retries > 0

        super().__init__(executor)
        self._logger = logging.getLogger("extapi.executor.retry")
        self._max_retries = max_retries
        self._retry_sleep_timeout = retry_sleep_timeout
        self._log_retries = log_retries

        if default_addons is ...:
            default_addons = get_default_addons()

        addons = list(addons)

        self._addons: list[Addon[T]] = [
            addon
            for addon in itertools.chain(addons, default_addons)
            if isinstance(addon, Addon)
        ]
        self._retry_addons: list[Retryable[T]] = [
            addon
            for addon in itertools.chain(addons, default_addons)
            if isinstance(addon, Retryable)
        ]

    async def _before_request(self, request: RequestData):
        for addon in self._addons:
            await addon.before_request(request)

    async def _process_response(
        self, request: RequestData, response: Response[T]
    ) -> Response[T]:
        for addon in self._addons:
            response = await addon.process_response(request, response)
        return response

    async def _process_error(self, request: RequestData, error: Exception) -> None:
        for addon in self._addons:
            await addon.process_error(request, error)

    async def _need_retry(self, response: Response[T]) -> tuple[bool, float | None]:
        for addon in self._retry_addons:
            need_retry, timeout = await addon.need_retry(response)
            if need_retry:
                return need_retry, timeout
        return False, None

    async def execute(self, request: RequestData) -> Response[T]:
        last_exc: Exception | None = None
        response: Response | None = None

        original_headers = request.headers
        for retry in range(self._max_retries):
            request.headers = (
                original_headers.copy() if original_headers is not None else None
            )

            await self._before_request(request)

            retry_sleep_timeout = self._retry_sleep_timeout
            need_retry = False

            try:
                if self._log_retries and retry > 0:
                    self._logger.warning(
                        "retry #%d/%d of request %s %s",
                        retry + 1,
                        self._max_retries,
                        request.method,
                        str(request.url),
                    )

                response = await super().execute(request)
                response = await self._process_response(request, response)

                need_retry, retry_timeout = await self._need_retry(response)
                if need_retry and retry_timeout is not None:
                    retry_sleep_timeout = retry_timeout

            except TimeoutError as e:
                need_retry = True
                last_exc = e
                response = None
                retry_sleep_timeout = 0

            except HttpExecuteError as e:
                await self._process_error(request, e)
                raise e

            except Exception as e:
                need_retry = True
                last_exc = e
                response = None

            if not need_retry:
                break

            if last_exc is not None:
                try:
                    await self._process_error(request, last_exc)
                except Exception as e:
                    self._logger.error(
                        "error post-processing request execution error %s(%s): %s",
                        type(last_exc).__name__,
                        last_exc,
                        e,
                    )

            if retry >= self._max_retries - 1:
                break

            if retry_sleep_timeout > 0:
                await asyncio.sleep(retry_sleep_timeout)

        if response is not None:
            return response

        if last_exc is not None:
            raise ExecuteError(
                f"request failed after {self._max_retries} retries: {type(last_exc).__name__}({str(last_exc)})"
            ) from last_exc
        else:  # pragma: no cover
            raise ExecuteError(f"request failed after {self._max_retries} retries")
