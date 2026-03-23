from backend.agents.base_agent import BaseAgent
from backend.agents.prompts import PLAYER_SYSTEM_PROMPT


class AIPlayerAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, model: str, personality: str):
        system_prompt = PLAYER_SYSTEM_PROMPT.format(name=name, personality=personality)
        super().__init__(agent_id, name, model, "player", system_prompt)
        self.personality = personality
