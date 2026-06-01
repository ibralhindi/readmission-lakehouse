"""Unit tests for agent configuration resolution."""

from __future__ import annotations

import importlib
from typing import Protocol, cast

import pytest

import readmission_lakehouse.agent.config as agent_config

CONFIG_ENV_VARS = ("AZURE_KEY_VAULT_URL", "DATABRICKS_CATALOG", "DATABRICKS_GOLD_SCHEMA")


class CachedSecretResolver(Protocol):
    """Callable secret resolver with the cache API added by functools.cache."""

    def __call__(self, env_var: str, kv_name: str) -> str: ...

    def cache_clear(self) -> None: ...


class ConfigModule(Protocol):
    """Subset of agent.config used by these tests."""

    KEY_VAULT_URL: str
    CATALOG: str
    GOLD_SCHEMA: str
    get_secret: CachedSecretResolver


@pytest.fixture(autouse=True)
def isolated_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep module-level config tests independent from local .env files."""
    monkeypatch.setenv("PYTHON_DOTENV_DISABLED", "1")
    for env_var in CONFIG_ENV_VARS:
        monkeypatch.delenv(env_var, raising=False)
    agent_config.get_secret.cache_clear()


def reload_config_module() -> ConfigModule:
    """Reload config after monkeypatching env vars read at import time."""
    return cast(ConfigModule, importlib.reload(agent_config))


def test_get_secret_returns_env_value_without_key_vault(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Env values win without constructing an Azure Key Vault client."""
    monkeypatch.setenv("TEST_AGENT_SECRET", "from-env")
    config = reload_config_module()

    def fail_secret_client() -> object:
        raise AssertionError("Key Vault client should not be constructed when env var is set")

    monkeypatch.setattr(config, "_secret_client", fail_secret_client)
    config.get_secret.cache_clear()

    assert config.get_secret("TEST_AGENT_SECRET", "kv-secret-name") == "from-env"


def test_environment_identifiers_use_documented_defaults_when_unset() -> None:
    """Module-level environment identifiers fall back to dev defaults."""
    config = reload_config_module()

    assert config.KEY_VAULT_URL == "https://rl-kv-3e33.vault.azure.net/"
    assert config.CATALOG == "rl_dev"
    assert config.GOLD_SCHEMA == "gold"


def test_environment_identifiers_use_env_values_when_set(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Module-level environment identifiers honor env overrides."""
    monkeypatch.setenv("AZURE_KEY_VAULT_URL", "https://example-vault.vault.azure.net/")
    monkeypatch.setenv("DATABRICKS_CATALOG", "rl_test")
    monkeypatch.setenv("DATABRICKS_GOLD_SCHEMA", "gold_test")

    config = reload_config_module()

    assert config.KEY_VAULT_URL == "https://example-vault.vault.azure.net/"
    assert config.CATALOG == "rl_test"
    assert config.GOLD_SCHEMA == "gold_test"
