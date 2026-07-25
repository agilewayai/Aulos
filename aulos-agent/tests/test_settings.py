"""Settings tests."""

import pytest

from aulos_agent.config.settings import Settings


def test_default_provider_is_fake():
    settings = Settings()
    assert settings.llm_provider == "fake"


def test_openai_requires_key():
    settings = Settings(AULOS_LLM_PROVIDER="openai", OPENAI_API_KEY=None)
    with pytest.raises(ValueError, match="OPENAI_API_KEY"):
        settings.require_live_credentials()
