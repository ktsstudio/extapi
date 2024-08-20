import json as jsonlib
import logging
from typing import Generic, TypeVar

from extapi.http.abc import Addon
from extapi.http.types import HttpExecuteError, RequestData, Response

T = TypeVar("T")


class LoggingAddon(Addon[T], Generic[T]):
    def __init__(self):
        self._logger = logging.getLogger("extapi.http.addons.log")

    async def before_request(self, request: RequestData) -> None:
        self._logger.debug("executing request %s %s", request.method, str(request.url))

    async def process_response(
        self, request: RequestData, response: Response[T]
    ) -> Response[T]:
        logger_method = (
            self._logger.debug if response.status < 500 else self._logger.error
        )

        logger_method(
            "received response %s %s -> status=%s",
            request.method,
            str(request.url),
            response.status if response is not None else "unknown",
        )

        return response

    async def process_error(self, request: RequestData, error: Exception) -> None:
        if isinstance(error, TimeoutError):
            self._logger.error(
                "timeout error for request %s %s failed with error %s(%s)",
                request.method,
                str(request.url),
                type(error),
                str(error),
            )
        elif isinstance(error, HttpExecuteError):
            await self.process_response(request, error.response)
        else:
            self._logger.error(
                "request %s %s failed with error %s(%s)",
                request.method,
                str(request.url),
                type(error),
                error,
            )


class VerboseLoggingExecutor(LoggingAddon[T], Generic[T]):
    def __init__(
        self,
        *,
        truncate_response_data: int | None = 1024,
    ):
        super().__init__()
        self._truncate_response_data = truncate_response_data

    async def before_request(self, request: RequestData) -> None:
        json = request.json
        if json is not None:
            if isinstance(json, bytes):
                json = json.decode("utf-8")
            if not isinstance(json, str):
                json = jsonlib.dumps(json)
        self._logger.debug(
            "executing request %s %s with params=%s json=%s data=%s timeout=%s",
            request.method,
            str(request.url),
            request.params,
            json,
            request.data,
            request.timeout,
        )

    async def process_response(
        self, request: RequestData, response: Response[T]
    ) -> Response[T]:
        logger_method = (
            self._logger.debug if response.status < 500 else self._logger.error
        )

        resp_body = response.data.decode("utf-8") if response.has_data else None
        if resp_body is not None and self._truncate_response_data is not None:
            resp_body = resp_body[: self._truncate_response_data]

        logger_method(
            "received response %s %s -> status=%s headers=%s body=%s",
            request.method,
            str(request.url),
            response.status,
            response.headers,
            resp_body,
        )

        return response
