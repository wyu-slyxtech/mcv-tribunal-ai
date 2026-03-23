from backend.providers.openai_provider import OpenAIProvider


class MiniMaxProvider(OpenAIProvider):
    def __init__(self, model: str):
        super().__init__(
            model,
            api_key_env="MINIMAX_API_KEY",
            base_url="https://api.minimax.chat/v1",
        )
