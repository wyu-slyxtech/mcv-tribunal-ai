from enum import StrEnum
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class EventType(StrEnum):
    GAME_STARTED = "game.started"
    GAME_PHASE_CHANGED = "game.phase_changed"
    GAME_ENDED = "game.ended"
    GAME_TIMER = "game.timer"
    AGENT_THINKING = "agent.thinking"
    AGENT_MESSAGE = "agent.message"
    AGENT_TYPING = "agent.typing"
    SCIENTIST_QUESTION = "scientist.question"
    SCIENTIST_EXTINCTION_PROPOSAL = "scientist.extinction_proposal"
    SCIENTIST_BONUS_QUESTION = "scientist.bonus_question"
    PLAYER_RESPONSE = "player.response"
    PLAYER_DEFENSE = "player.defense"
    PLAYER_ACCUSATION = "player.accusation"
    PLAYER_INTERVENTION = "player.intervention"
    PLAYER_ELIMINATED = "player.eliminated"
    JURY_SCORE_UPDATE = "jury.score_update"
    JURY_VOTE = "jury.vote"
    JURY_VERDICT = "jury.verdict"
    STRATEGY_MESSAGE = "strategy.message"


class Phase(StrEnum):
    STRATEGY = "strategy"
    INTERROGATION = "interrogation"
    DEFENSE = "defense"
    ARENA = "arena"


class EventMetadata(BaseModel):
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    response_time_ms: int = 0


class GameEvent(BaseModel):
    version: int = 1
    id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    phase: Phase | None = None
    agent_id: str | None = None
    agent_name: str | None = None
    agent_role: str | None = None
    data: dict = Field(default_factory=dict)
    metadata: EventMetadata = Field(default_factory=EventMetadata)
