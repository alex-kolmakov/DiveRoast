"""Phoenix tracing initialization. Call init_tracing() at app startup."""

import logging

from src.config import settings

logger = logging.getLogger(__name__)

_tracer = None


def _noop_tracer():
    """Return a no-op tracer when Phoenix is unavailable."""
    from opentelemetry.trace import NoOpTracer

    return NoOpTracer()


def init_tracing():
    global _tracer
    try:
        from phoenix.otel import register

        tracer_provider = register(
            project_name="diveroast",
            endpoint=settings.PHOENIX_COLLECTOR_ENDPOINT,
            auto_instrument=True,  # auto-instruments google-genai
        )
        _tracer = tracer_provider.get_tracer("diveroast")
    except Exception:
        logger.warning("Phoenix tracing unavailable, using no-op tracer", exc_info=True)
        _tracer = _noop_tracer()
    return _tracer


def get_tracer():
    global _tracer
    if _tracer is None:
        _tracer = init_tracing()
    return _tracer
