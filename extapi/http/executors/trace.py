from extapi._meta import has_open_telemetry

if not has_open_telemetry:
    raise ImportError(  # pragma: no cover
        "opentelemetry is not installed - run `pip install opentelemetry-api opentelemetry-sdk`"
    )

from typing import Generic, TypeVar

from multidict import CIMultiDict
from opentelemetry import trace
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

from extapi.http.abc import AbstractExecutor
from extapi.http.types import RequestData, Response

from .wrapped import WrappedExecutor

T = TypeVar("T", covariant=True)

extapi_tracer = trace.get_tracer(__name__)


class OpenTelemetryExecutor(WrappedExecutor[T], Generic[T]):
    __slots__ = (
        "_tracer",
        "_span_name",
        "_inject_tracing_headers",
        "_trace_context_propagator",
    )

    def __init__(
        self,
        executor: AbstractExecutor[T],
        *,
        tracer: trace.Tracer | None = None,
        span_name: str = "http_request",
        inject_tracing_headers: bool = True,
        trace_context_propagator: TraceContextTextMapPropagator | None = None,
    ):
        super().__init__(executor)
        self._tracer = tracer or extapi_tracer
        self._span_name = span_name
        self._inject_tracing_headers = inject_tracing_headers
        self._trace_context_propagator = (
            trace_context_propagator or TraceContextTextMapPropagator()
        )

    async def execute(self, request: RequestData) -> Response[T]:
        with self._tracer.start_as_current_span(self._span_name) as span:
            if self._inject_tracing_headers:
                if request.headers is None:
                    request.headers = CIMultiDict()

                self._trace_context_propagator.inject(request.headers)

            span.set_attribute(SpanAttributes.HTTP_REQUEST_METHOD, request.method)

            if request.url.host is not None:
                span.set_attribute(SpanAttributes.SERVER_ADDRESS, request.url.host)

            if request.url.port is not None:
                span.set_attribute(SpanAttributes.SERVER_PORT, request.url.port)

            span.set_attribute(SpanAttributes.URL_SCHEME, request.url.scheme)
            span.set_attribute(SpanAttributes.URL_PATH, request.url.path)

            return await super().execute(request)
