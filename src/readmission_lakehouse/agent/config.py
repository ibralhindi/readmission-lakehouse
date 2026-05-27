"""Configuration for the care-manager RAG agent.

Loads secrets from a local .env (gitignored) and centralises model + path
choices so the rest of the package never hardcodes them.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Reads .env at the project root into the environment. The OpenAI SDK and
# langchain-openai both pick up OPENAI_API_KEY from the environment directly,
# so we never pass the key around in code.
load_dotenv()

# --- Models (both cheap; swap here if needed) ---
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

# --- Chroma persistence (gitignored) ---
CHROMA_DIR = Path(__file__).resolve().parents[3] / ".chroma"

# --- Collections ---
NOTES_COLLECTION = "patient_notes"
GUIDELINES_COLLECTION = "guidelines"


def require_openai_key() -> str:
    """Fail fast with a clear message if the key isn't set."""
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "OPENAI_API_KEY not set. Add it to .env at the project root "
            "(OPENAI_API_KEY=sk-...). The .env file is gitignored."
        )
    return key
