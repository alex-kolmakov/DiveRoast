"""Seed Phoenix with existing prompt versions from system_prompts.py.

Usage:
    python -m src.scripts.seed_prompts

Pushes all local prompt versions to Phoenix and tags V3 as "production".
Safe to re-run — Phoenix will create new versions each time, but only the
latest tagged version matters.
"""

from phoenix.client import Client
from phoenix.client.types import PromptVersion

from src.agent.system_prompts import (
    PHOENIX_PROMPT_NAME,
    PHOENIX_PROMPT_TAG,
    PROMPT_VERSIONS,
)
from src.config import settings


def seed() -> None:
    client = Client(base_url=settings.PHOENIX_CLIENT_ENDPOINT)
    latest_version_id: str | None = None

    for ver_num in sorted(PROMPT_VERSIONS.keys()):
        pv = PROMPT_VERSIONS[ver_num]
        print(f"Pushing V{ver_num} ({pv.label})...")

        prompt = client.prompts.create(
            name=PHOENIX_PROMPT_NAME,
            version=PromptVersion(
                [{"role": "system", "content": pv.prompt}],
                model_name="gemini-3.0-flash",
            ),
            prompt_description=f"V{ver_num}: {pv.changelog}",
        )
        latest_version_id = str(prompt.id)
        print(f"  -> version_id={latest_version_id}")

    # Tag the last pushed version (V3) as production
    if latest_version_id:
        print(f"Tagging version {latest_version_id} as '{PHOENIX_PROMPT_TAG}'...")
        client.prompts.tags.create(
            prompt_version_id=latest_version_id,
            name=PHOENIX_PROMPT_TAG,
            description="Current production prompt version",
        )
        print("Done!")


if __name__ == "__main__":
    seed()
