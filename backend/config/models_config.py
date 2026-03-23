PROVIDERS = {
    "anthropic": {
        "models": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5"],
        "env_key": "ANTHROPIC_API_KEY",
    },
    "openai": {
        "models": ["gpt-4o", "gpt-4o-mini", "o3"],
        "env_key": "OPENAI_API_KEY",
    },
    "google": {
        "models": ["gemini-2.5-pro", "gemini-2.5-flash"],
        "env_key": "GOOGLE_API_KEY",
    },
    "deepseek": {
        "models": ["deepseek-v3", "deepseek-r1"],
        "env_key": "DEEPSEEK_API_KEY",
    },
    "minimax": {
        "models": ["minimax-01"],
        "env_key": "MINIMAX_API_KEY",
    },
    "qwen": {
        "models": ["qwen3"],
        "env_key": "QWEN_API_KEY",
    },
    "xai": {
        "models": ["grok-3", "grok-3-mini"],
        "env_key": "XAI_API_KEY",
    },
    "ollama": {
        "models": ["llama3", "mistral"],
        "env_key": "OLLAMA_URL",
        "default_url": "http://localhost:11434",
    },
}


def get_provider_for_model(model: str) -> str:
    if model.startswith("ollama/"):
        return "ollama"
    for provider, info in PROVIDERS.items():
        if model in info["models"]:
            return provider
    raise ValueError(f"Unknown model: {model}")
