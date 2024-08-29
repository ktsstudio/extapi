import warnings

from extapi._meta import has_prometheus

if not has_prometheus:
    raise ImportError(  # pragma: no cover
        "opentelemetry is not installed - run `pip install prometheus_client`"
    )

import time
from typing import Generic, TypeVar

from extapi.http.abc import AbstractExecutor
from extapi.http.types import RequestData, Response

from ..metrics.container import MetricsContainer
from .wrapped import WrappedExecutor

T = TypeVar("T", covariant=True)


class PrometheusMetricsExecutor(WrappedExecutor[T], Generic[T]):
    def __init__(
        self,
        executor: AbstractExecutor[T],
        *,
        metrics_container: MetricsContainer,
        disable_warnings: bool = False,
    ):
        super().__init__(executor)
        self._metrics_container = metrics_container
        self._disable_warnings = disable_warnings

    async def execute(self, request: RequestData) -> Response[T]:
        path_template = request.kwargs.pop("path_template", None)

        if not self._disable_warnings and path_template is None:
            warnings.warn(
                "It is highly recommended to pass `path_template` "
                "argument to the executor in order to not explode the "
                "label cardinality when path is customized on each request. "
                "For example, you may pass path_template='/some/items/<item_id>' "
                "when executing request like `GET /some/items/123`.",
                UserWarning,
                stacklevel=1,
            )

        path = path_template or request.url.path

        method = request.method.upper()
        started_at = time.monotonic()
        try:
            resp = await super().execute(request)
        except Exception as e:
            label_values = (
                request.url.scheme,
                request.url.host,
                request.url.port,
                method,
                path,
                e.__class__.__name__,
            )
            self._metrics_container.requests_error.labels(*label_values).inc()
            self._metrics_container.requests_duration_error.labels(
                *label_values
            ).observe(time.monotonic() - started_at)
            raise
        else:
            label_values = (
                request.url.scheme,
                request.url.host,
                request.url.port,
                method,
                path,
                str(resp.status),
            )
            self._metrics_container.requests.labels(*label_values).inc()
            self._metrics_container.requests_duration.labels(*label_values).observe(
                time.monotonic() - started_at
            )
            return resp
