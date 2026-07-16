"""LLM provider selection — the API key must match the base-URL provider.

Regression for the production bug where both DEEPSEEK_API_KEY and
NVIDIA_NIM_API_KEY were set: _base_url() chose api.deepseek.com but
_api_key() preferred the NIM key, so every LLM call sent an nvapi- key
to DeepSeek, got 401, and silently fell back to template narratives.
"""

from __future__ import annotations

import pytest

from rehearse import llm

_PROVIDER_VARS = [
    "REHEARSE_LLM_API_KEY",
    "REHEARSE_LLM_BASE_URL",
    "REHEARSE_LLM_PRIMARY",
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_API_BASE",
    "NVIDIA_NIM_API_KEY",
    "NVIDIA_API_KEY",
    "NVIDIA_NIM_API_BASE",
    "NVIDIA_API_BASE",
    "OPENAI_API_KEY",
]


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    for var in _PROVIDER_VARS:
        monkeypatch.delenv(var, raising=False)


def test_both_keys_set_deepseek_url_gets_deepseek_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek-test")
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    assert "deepseek.com" in llm._base_url()
    assert llm._api_key() == "sk-deepseek-test"


def test_both_keys_set_nim_primary_gets_nim_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek-test")
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    monkeypatch.setenv("REHEARSE_LLM_PRIMARY", "nim")
    assert "nvidia" in llm._base_url()
    assert llm._api_key() == "nvapi-test"


def test_only_nim_key(monkeypatch):
    monkeypatch.setenv("NVIDIA_NIM_API_KEY", "nvapi-test")
    assert "nvidia" in llm._base_url()
    assert llm._api_key() == "nvapi-test"


def test_only_deepseek_key(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek-test")
    assert "deepseek.com" in llm._base_url()
    assert llm._api_key() == "sk-deepseek-test"


def test_explicit_key_wins(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-deepseek-test")
    monkeypatch.setenv("REHEARSE_LLM_API_KEY", "explicit-key")
    assert llm._api_key() == "explicit-key"
