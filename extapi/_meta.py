import importlib.util

has_open_telemetry = importlib.util.find_spec("opentelemetry") is not None
