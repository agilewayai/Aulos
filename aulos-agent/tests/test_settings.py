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


def test_deepseek_and_grok_require_keys():
    deepseek = Settings(AULOS_LLM_PROVIDER="deepseek", DEEPSEEK_API_KEY=None)
    with pytest.raises(ValueError, match="DEEPSEEK_API_KEY"):
        deepseek.require_live_credentials()
    grok = Settings(AULOS_LLM_PROVIDER="grok", XAI_API_KEY=None)
    with pytest.raises(ValueError, match="XAI_API_KEY"):
        grok.require_live_credentials()
