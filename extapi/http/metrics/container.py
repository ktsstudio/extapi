from prometheus_client import REGISTRY, CollectorRegistry, Counter, Histogram

from .helpers import DEFAULT_BUCKETS, with_prefix


class MetricsContainer:
    def __init__(
        self,
        *,
        metrics_prefix: str,
        metrics_registry: CollectorRegistry = REGISTRY,
    ):
        self.requests = Counter(
            name=with_prefix("external_service_request", prefix=metrics_prefix),
            documentation="Count of external requests",
            labelnames=[
                "scheme",
                "domain",
                "port",
                "method",
                "path",
                "status",
            ],
            registry=metrics_registry,
        )

        self.requests_duration = Histogram(
            name=with_prefix(
                "external_service_request_duration_seconds", prefix=metrics_prefix
            ),
            documentation="External request duration in seconds",
            labelnames=[
                "scheme",
                "domain",
                "port",
                "method",
                "path",
                "status",
            ],
            buckets=DEFAULT_BUCKETS,
            registry=metrics_registry,
        )

        self.requests_error = Counter(
            name=with_prefix("external_service_errored_request", prefix=metrics_prefix),
            documentation="Count of errored external requests",
            labelnames=["scheme", "domain", "port", "method", "path", "error_type"],
            registry=metrics_registry,
        )

        self.requests_duration_error = Histogram(
            name=with_prefix(
                "external_service_errored_request_duration_seconds",
                prefix=metrics_prefix,
            ),
            documentation="Errored external request duration in seconds",
            labelnames=["scheme", "domain", "port", "method", "path", "error_type"],
            buckets=DEFAULT_BUCKETS,
            registry=metrics_registry,
        )
