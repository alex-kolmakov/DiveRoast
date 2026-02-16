import uuid

from src.agent.conversation import DiverRoastAgent

# In-memory session store: {session_id: DiverRoastAgent}
_sessions: dict[str, DiverRoastAgent] = {}


def get_or_create_session(session_id: str | None = None) -> tuple[str, DiverRoastAgent]:
    """Get an existing session or create a new one.

    Returns (session_id, agent) tuple.
    """
    if session_id and session_id in _sessions:
        return session_id, _sessions[session_id]

    new_id = session_id or str(uuid.uuid4())
    agent = DiverRoastAgent()
    _sessions[new_id] = agent
    return new_id, agent


def get_session(session_id: str) -> DiverRoastAgent | None:
    """Get an existing session by ID, or None if not found."""
    return _sessions.get(session_id)
