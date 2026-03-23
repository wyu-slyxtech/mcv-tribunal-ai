import pytest
from backend.providers.base_provider import BaseProvider
from backend.providers.factory import create_provider


def test_base_provider_interface():
    assert hasattr(BaseProvider, "send")


def test_create_provider_claude():
    provider = create_provider("claude-sonnet-4-6")
    assert provider.__class__.__name__ == "ClaudeProvider"


def test_create_provider_openai():
    provider = create_provider("gpt-4o")
    assert provider.__class__.__name__ == "OpenAIProvider"


def test_create_provider_gemini():
    provider = create_provider("gemini-2.5-pro")
    assert provider.__class__.__name__ == "GeminiProvider"


def test_create_provider_deepseek():
    provider = create_provider("deepseek-v3")
    assert provider.__class__.__name__ == "DeepSeekProvider"


def test_create_provider_minimax():
    provider = create_provider("minimax-01")
    assert provider.__class__.__name__ == "MiniMaxProvider"


def test_create_provider_qwen():
    provider = create_provider("qwen3")
    assert provider.__class__.__name__ == "QwenProvider"


def test_create_provider_grok():
    provider = create_provider("grok-3")
    assert provider.__class__.__name__ == "GrokProvider"


def test_create_provider_ollama():
    provider = create_provider("ollama/llama3")
    assert provider.__class__.__name__ == "OllamaProvider"


def test_create_provider_unknown():
    with pytest.raises(ValueError, match="Unknown model"):
        create_provider("unknown-model-xyz")
