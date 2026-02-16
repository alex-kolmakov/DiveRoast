from google import genai

from src.config import settings


def get_client() -> genai.Client:
    """Return a configured Google GenAI client."""
    return genai.Client(api_key=settings.GEMINI_API_KEY)
