from backend.providers.base_provider import BaseProvider
from backend.providers.claude_provider import ClaudeProvider
from backend.providers.openai_provider import OpenAIProvider
from backend.providers.gemini_provider import GeminiProvider
from backend.providers.deepseek_provider import DeepSeekProvider
from backend.providers.minimax_provider import MiniMaxProvider
from backend.providers.qwen_provider import QwenProvider
from backend.providers.grok_provider import GrokProvider
from backend.providers.ollama_provider import OllamaProvider
from backend.config.models_config import get_provider_for_model

_PROVIDER_CLASSES = {
    "anthropic": ClaudeProvider,
    "openai": OpenAIProvider,
    "google": GeminiProvider,
    "deepseek": DeepSeekProvider,
    "minimax": MiniMaxProvider,
    "qwen": QwenProvider,
    "xai": GrokProvider,
    "ollama": OllamaProvider,
}


def create_provider(model: str) -> BaseProvider:
    provider_name = get_provider_for_model(model)
    provider_class = _PROVIDER_CLASSES[provider_name]
    return provider_class(model)
