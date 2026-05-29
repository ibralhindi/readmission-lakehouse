"""Configuration + secret resolution for the care-manager RAG agent.

Non-secret settings (model names, paths, the Databricks host/path/client-id)
come from a local .env. The two real secrets — the OpenAI key and the service
principal's OAuth secret — are resolved from Azure Key Vault at runtime via
DefaultAzureCredential, so nothing sensitive sits in .env or the repo.
"""

from __future__ import annotations

import os
from functools import cache, lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from dotenv import load_dotenv

if TYPE_CHECKING:
    from azure.keyvault.secrets import SecretClient

# Non-secret config still comes from .env (host, http_path, client_id, etc.).
load_dotenv()

# --- Models (both cheap; swap here if needed) ---
EMBED_MODEL = "text-embedding-3-small"
CHAT_MODEL = "gpt-4o-mini"

# --- Chroma persistence (gitignored) ---
CHROMA_DIR = Path(__file__).resolve().parents[3] / ".chroma"

# --- Collections ---
NOTES_COLLECTION = "patient_notes"
GUIDELINES_COLLECTION = "guidelines"

# --- Azure Key Vault (holds the actual secrets) ---
KEY_VAULT_URL = "https://rl-kv-3e33.vault.azure.net/"


@lru_cache(maxsize=1)
def _secret_client() -> SecretClient:
    # DefaultAzureCredential resolves identity with NO stored bootstrap secret:
    # locally it uses your `az login` session; on an Azure host it would use the
    # attached managed identity — same code, different environment. Imported
    # lazily so the module still imports when secrets are supplied via env.
    from azure.identity import DefaultAzureCredential  # noqa: PLC0415
    from azure.keyvault.secrets import SecretClient  # noqa: PLC0415

    return SecretClient(vault_url=KEY_VAULT_URL, credential=DefaultAzureCredential())


@cache
def get_secret(env_var: str, kv_name: str) -> str:
    """Resolve a secret: an explicit env var wins (handy for CI / local
    override); otherwise fetch from Key Vault. Cached for the process so we
    hit the vault at most once per secret."""
    val = os.environ.get(env_var)
    if val:
        return val
    secret = _secret_client().get_secret(kv_name).value
    if secret is None:
        raise RuntimeError(f"Key Vault secret '{kv_name}' has no value.")
    if not isinstance(secret, str):
        raise RuntimeError(f"Key Vault secret '{kv_name}' is not a string.")
    return secret


def require_openai_key() -> str:
    """Ensure OPENAI_API_KEY is available (env or Key Vault) and export it to
    the environment, since langchain-openai reads the key from there."""
    key = get_secret("OPENAI_API_KEY", "openai-api-key")
    os.environ["OPENAI_API_KEY"] = key
    return key
