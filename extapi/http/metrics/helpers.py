from prometheus_client.utils import INF


def with_prefix(name: str, prefix: str | None = None):
    prefix = prefix or ""
    return f"{prefix}{name}"


DEFAULT_BUCKETS = (
    0.005,
    0.01,
    0.05,
    0.1,
    0.5,
    1.0,
    2.5,
    5.0,
    7.5,
    10.0,
    12.5,
    15,
    17.5,
    20,
    22.5,
    25,
    27.5,
    30,
    INF,
)
