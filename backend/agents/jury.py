from backend.agents.base_agent import BaseAgent
from backend.agents.prompts import JURY_SYSTEM_PROMPT


class JuryAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, model: str):
        system_prompt = JURY_SYSTEM_PROMPT.format(name=name)
        super().__init__(agent_id, name, model, "jury", system_prompt)
        self.scores: dict[str, int] = {}
