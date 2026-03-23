import os

from openai import AsyncOpenAI

from backend.providers.base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(
        self,
        model: str,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str | None = None,
    ):
        super().__init__(model)
        self._api_key_env = api_key_env
        self._base_url = base_url
        self._client: AsyncOpenAI | None = None

    @property
    def client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=os.getenv(self._api_key_env),
                base_url=self._base_url,
            )
        return self._client

    async def send(
        self,
        prompt: str,
        system_prompt: str,
        history: list[dict] | None = None,
    ) -> dict:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1024,
        )
        usage = response.usage
        return {
            "content": response.choices[0].message.content,
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        }
