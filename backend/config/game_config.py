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
    mode: str = "tribunal"
    players: dict[str, AgentConfig]
    scientist: AgentConfig
    jury: dict[str, AgentConfig]
    rules: RulesConfig = Field(default_factory=RulesConfig)


class BrainstormRulesConfig(BaseModel):
    debate_round_seconds: int = 180
    max_rounds: int = 5
    consensus_threshold: int = 3
    sub_rounds_per_debate: int = 3


class BrainstormConfig(BaseModel):
    game_id: str = Field(
        default_factory=lambda: (lambda t=datetime.now(timezone.utc): f"brainstorm_{t.strftime('%Y-%m-%d')}_{t.strftime('%H%M%S')}")()
    )
    mode: str = "brainstorm"
    topic: str
    players: dict[str, AgentConfig]
    rules: BrainstormRulesConfig = Field(default_factory=BrainstormRulesConfig)
