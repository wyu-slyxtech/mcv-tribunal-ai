from backend.providers.openai_provider import OpenAIProvider


class GrokProvider(OpenAIProvider):
    def __init__(self, model: str):
        super().__init__(
            model,
            api_key_env="XAI_API_KEY",
            base_url="https://api.x.ai/v1",
        )
