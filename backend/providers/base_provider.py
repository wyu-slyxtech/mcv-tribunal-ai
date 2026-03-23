from abc import ABC, abstractmethod


class BaseProvider(ABC):
    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    async def send(
        self,
        prompt: str,
        system_prompt: str,
        history: list[dict] | None = None,
    ) -> dict:
        """Return {"content": str, "input_tokens": int, "output_tokens": int}"""
        ...
