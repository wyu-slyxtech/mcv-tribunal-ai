import os

from google import genai
from google.genai import types

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
        contents = []
        if history:
            for m in history:
                role = "model" if m["role"] == "assistant" else m["role"]
                contents.append(
                    types.Content(
                        role=role,
                        parts=[types.Part(text=m["content"])],
                    )
                )
        contents.append(
            types.Content(role="user", parts=[types.Part(text=prompt)])
        )

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
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
