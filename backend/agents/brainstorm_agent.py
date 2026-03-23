from backend.agents.base_agent import BaseAgent
from backend.agents.prompts import BRAINSTORM_SYSTEM_PROMPT


class BrainstormAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, model: str, personality: str):
        system_prompt = BRAINSTORM_SYSTEM_PROMPT.format(name=name, personality=personality)
        super().__init__(agent_id, name, model, "brainstormer", system_prompt)
        self.personality = personality
