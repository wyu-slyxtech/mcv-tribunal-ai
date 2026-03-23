from backend.providers.openai_provider import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    def __init__(self, model: str):
        super().__init__(
            model,
            api_key_env="DEEPSEEK_API_KEY",
            base_url="https://api.deepseek.com/v1",
        )
