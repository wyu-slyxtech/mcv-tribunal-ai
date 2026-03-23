import os

import ollama

from backend.providers.base_provider import BaseProvider


class OllamaProvider(BaseProvider):
    def __init__(self, model: str):
        actual_model = model.removeprefix("ollama/")
        super().__init__(actual_model)
        url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.client = ollama.AsyncClient(host=url)

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

        response = await self.client.chat(
            model=self.model,
            messages=messages,
        )
        return {
            "content": response.message.content,
            "input_tokens": response.prompt_eval_count or 0,
            "output_tokens": response.eval_count or 0,
        }
