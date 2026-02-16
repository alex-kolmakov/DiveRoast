"""Phoenix tracing initialization. Call init_tracing() at app startup."""

from phoenix.otel import register

from src.config import settings

_tracer = None


def init_tracing():
    global _tracer
    tracer_provider = register(
        project_name="diveroast",
        endpoint=settings.PHOENIX_COLLECTOR_ENDPOINT,
        auto_instrument=True,  # auto-instruments google-genai
    )
    _tracer = tracer_provider.get_tracer("diveroast")
    return _tracer


def get_tracer():
    global _tracer
    if _tracer is None:
        _tracer = init_tracing()
    return _tracer
