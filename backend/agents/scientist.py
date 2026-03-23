from backend.agents.base_agent import BaseAgent
from backend.agents.prompts import SCIENTIST_SYSTEM_PROMPT


class ScientistAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, model: str, personality: str):
        system_prompt = SCIENTIST_SYSTEM_PROMPT.format(name=name, personality=personality)
        super().__init__(agent_id, name, model, "scientist", system_prompt)
        self.personality = personality
        self.extinction_attempts = 0
