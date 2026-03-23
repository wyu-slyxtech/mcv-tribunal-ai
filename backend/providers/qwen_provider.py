from backend.providers.openai_provider import OpenAIProvider


class QwenProvider(OpenAIProvider):
    def __init__(self, model: str):
        super().__init__(
            model,
            api_key_env="QWEN_API_KEY",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
