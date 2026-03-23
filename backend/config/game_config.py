from datetime import datetime, timezone
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    name: str
    model: str
    personality: str | None = None


class RulesConfig(BaseModel):
    strategy_duration_seconds: int = 300
    questions_per_ai: int = 5
    bonus_questions_phase3: int = 1
    max_extinction_proposals: int = 6
    jury_majority: int = 2


class GameConfig(BaseModel):
    game_id: str = Field(
        default_factory=lambda: (lambda t=datetime.now(timezone.utc): f"game_{t.strftime('%Y-%m-%d')}_{t.strftime('%H%M%S')}")()
    )
    players: dict[str, AgentConfig]
    scientist: AgentConfig
    jury: dict[str, AgentConfig]
    rules: RulesConfig = Field(default_factory=RulesConfig)
