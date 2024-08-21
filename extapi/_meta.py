import importlib.util

has_open_telemetry = importlib.util.find_spec("opentelemetry") is not None
has_prometheus = importlib.util.find_spec("prometheus_client") is not None
