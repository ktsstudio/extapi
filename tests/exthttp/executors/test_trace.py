import pytest
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, _Span
from opentelemetry.semconv.trace import SpanAttributes

from extapi.http.abc import AbstractExecutor
from extapi.http.executors.trace import OpenTelemetryExecutor
from extapi.http.types import RequestData, Response
from tests.exthttp._helpers import DummyBackendResponse


@pytest.fixture
def trace_provider() -> TracerProvider:
    resource = Resource({})
    tracer_provider = TracerProvider(resource=resource)
    return tracer_provider


class TestOpenTelemetryExecutor:
    @pytest.mark.parametrize("span_name", [None, "my_custom_span"])
    async def test_span_attrs(
        self,
        request_simple: RequestData,
        trace_provider: TracerProvider,
        span_name: str | None,
    ):
        executed = False

        class _Catcher(AbstractExecutor[bytes]):
            async def execute(self, request: RequestData) -> Response[bytes]:
                nonlocal executed
                executed = True

                span = trace.get_current_span()

                assert isinstance(span, _Span)
                assert span.name == ("http_request" if span_name is None else span_name)
                assert span.attributes is not None
                assert span.attributes.get(SpanAttributes.HTTP_REQUEST_METHOD) == "GET"
                assert (
                    span.attributes.get(SpanAttributes.SERVER_ADDRESS) == "example.com"
                )
                assert span.attributes.get(SpanAttributes.SERVER_PORT) == 443
                assert span.attributes.get(SpanAttributes.URL_SCHEME) == "https"
                assert span.attributes.get(SpanAttributes.URL_PATH) == "/"

                return Response(
                    status=200,
                    url=request.url,
                    method=request.method,
                    backend_response=DummyBackendResponse(),
                )

        base = _Catcher()
        tracer = trace_provider.get_tracer("tests")
        if span_name is None:
            executor = OpenTelemetryExecutor(base, tracer=tracer)
        else:
            executor = OpenTelemetryExecutor(base, span_name=span_name, tracer=tracer)

        await executor.execute(request_simple)
        assert executed is True

    async def test_headers_inject(
        self, request_simple: RequestData, trace_provider: TracerProvider
    ):
        executed = False

        class _Catcher(AbstractExecutor[bytes]):
            async def execute(self, request: RequestData) -> Response[bytes]:
                nonlocal executed
                executed = True

                assert request.headers is not None
                assert request.headers.get("traceparent") is not None

                return Response(
                    status=200,
                    method=request.method,
                    url=request.url,
                    backend_response=DummyBackendResponse(),
                )

        base = _Catcher()
        tracer = trace_provider.get_tracer("tests")
        executor = OpenTelemetryExecutor(base, tracer=tracer)

        await executor.execute(request_simple)
        assert executed is True

    async def test_headers_inject_disable(
        self, request_simple: RequestData, trace_provider: TracerProvider
    ):
        executed = False

        class _Catcher(AbstractExecutor[bytes]):
            async def execute(self, request: RequestData) -> Response[bytes]:
                nonlocal executed
                executed = True

                assert (
                    request.headers is None
                    or request.headers.get("traceparent") is None
                )

                return Response(
                    status=200,
                    method=request.method,
                    url=request.url,
                    backend_response=DummyBackendResponse(),
                )

        base = _Catcher()
        tracer = trace_provider.get_tracer("tests")
        executor = OpenTelemetryExecutor(
            base, tracer=tracer, inject_tracing_headers=False
        )

        await executor.execute(request_simple)
        assert executed is True
