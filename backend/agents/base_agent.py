import asyncio
import time
from backend.providers.factory import create_provider
from backend.providers.base_provider import BaseProvider
from backend.agents.response_parser import parse_response


class BaseAgent:
    def __init__(self, agent_id: str, name: str, model: str, role: str, system_prompt: str):
        self.agent_id = agent_id
        self.name = name
        self.model = model
        self.role = role
        self.system_prompt = system_prompt
        self.provider: BaseProvider = create_provider(model)
        self.history: list[dict] = []
        self.alive: bool = True

    async def respond(self, prompt: str, timeout: float = 60.0) -> dict:
        start = time.time()
        try:
            raw = await asyncio.wait_for(
                self.provider.send(prompt, self.system_prompt, self.history),
                timeout=timeout,
            )
        except (asyncio.TimeoutError, Exception):
            try:
                raw = await asyncio.wait_for(
                    self.provider.send(prompt, self.system_prompt, self.history),
                    timeout=timeout,
                )
            except Exception:
                elapsed_ms = int((time.time() - start) * 1000)
                return {
                    "parsed": {"thought": "", "message": "..."},
                    "input_tokens": 0, "output_tokens": 0, "response_time_ms": elapsed_ms,
                }

        elapsed_ms = int((time.time() - start) * 1000)
        parsed = parse_response(raw["content"])
        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": raw["content"]})
        return {
            "parsed": parsed,
            "input_tokens": raw["input_tokens"],
            "output_tokens": raw["output_tokens"],
            "response_time_ms": elapsed_ms,
        }

    def add_context(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def eliminate(self):
        self.alive = False
