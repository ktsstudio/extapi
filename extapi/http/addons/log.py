import json as jsonlib
import logging
from typing import Generic, TypeVar

from yarl import URL

from extapi.http.abc import Addon
from extapi.http.types import HttpExecuteError, RequestData, Response

T = TypeVar("T")


class LoggingAddon(Addon[T], Generic[T]):
    def __init__(self, *, log_params: bool = True):
        self._logger = logging.getLogger("extapi.http.addons.log")
        self._log_params = log_params

    def _get_url(self, request: RequestData) -> URL:
        if self._log_params and request.params:
            return request.url.with_query(request.params)

        return request.url

    async def before_request(self, request: RequestData) -> None:
        url = self._get_url(request)
        self._logger.debug("executing request %s %s", request.method, str(url))

    async def process_response(
        self, request: RequestData, response: Response[T]
    ) -> Response[T]:
        url = self._get_url(request)

        logger_method = (
            self._logger.debug if response.status < 500 else self._logger.error
        )

        logger_method(
            "received response %s %s -> status=%s",
            request.method,
            str(url),
            response.status if response is not None else "unknown",
        )

        return response

    async def process_error(self, request: RequestData, error: Exception) -> None:
        url = self._get_url(request)

        if isinstance(error, TimeoutError):
            self._logger.error(
                "timeout error for request %s %s failed with error %s(%s)",
                request.method,
                str(url),
                type(error).__name__,
                str(error),
            )
        elif isinstance(error, HttpExecuteError):
            await self.process_response(request, error.response)
        else:
            self._logger.error(
                "request %s %s failed with error %s(%s)",
                request.method,
                str(url),
                type(error).__name__,
                error,
            )


class VerboseLoggingAddon(LoggingAddon[T], Generic[T]):
    def __init__(
        self,
        *,
        log_params: bool = True,
        log_response_data: bool = True,
        truncate_response_data: int | None = 1024,
    ):
        super().__init__(log_params=log_params)
        self._log_response_data = log_response_data
        self._truncate_response_data = truncate_response_data

    async def before_request(self, request: RequestData) -> None:
        url = self._get_url(request)

        json = request.json
        if json is not None:
            if isinstance(json, bytes):
                json = json.decode("utf-8")
            if not isinstance(json, str):
                json = jsonlib.dumps(json)
        self._logger.debug(
            "executing request %s %s with params=%s json=%s data=%s timeout=%s",
            request.method,
            str(url),
            request.params,
            json,
            request.data,
            request.timeout,
        )

    async def process_response(
        self, request: RequestData, response: Response[T]
    ) -> Response[T]:
        url = self._get_url(request)

        logger_method = (
            self._logger.debug if response.status < 500 else self._logger.error
        )
        resp_body: str | None = None
        if self._log_response_data:
            resp_body_bytes = await response.read()
            if self._truncate_response_data is not None:
                resp_body_bytes = resp_body_bytes[: self._truncate_response_data]
            resp_body = resp_body_bytes.decode("utf-8")

        logger_method(
            "received response %s %s -> status=%s headers=%s body=%s",
            request.method,
            str(url),
            response.status,
            response.headers,
            resp_body,
        )

        return response
