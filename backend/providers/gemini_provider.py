import os

from google import genai

from backend.providers.base_provider import BaseProvider


class GeminiProvider(BaseProvider):
    def __init__(self, model: str):
        super().__init__(model)
        self._client: genai.Client | None = None

    @property
    def client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        return self._client

    async def send(
        self,
        prompt: str,
        system_prompt: str,
        history: list[dict] | None = None,
    ) -> dict:
        full_prompt = prompt
        if history:
            context = "\n".join(
                f"{m['role']}: {m['content']}" for m in history
            )
            full_prompt = f"{context}\nuser: {prompt}"

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1024,
            ),
        )
        usage = response.usage_metadata
        return {
            "content": response.text,
            "input_tokens": usage.prompt_token_count if usage else 0,
            "output_tokens": usage.candidates_token_count if usage else 0,
        }
