import pytest
from backend.engine.events import GameEvent, EventType, Phase


def test_event_creation():
    event = GameEvent(
        type=EventType.AGENT_THINKING,
        phase=Phase.INTERROGATION,
        agent_id="ia-1",
        agent_name="VOLT",
        agent_role="player",
        data={"content": "I need to stay calm..."},
    )
    assert event.id.startswith("evt_")
    assert event.version == 1
    assert event.type == EventType.AGENT_THINKING
    assert event.timestamp is not None


def test_event_type_enum():
    assert EventType.GAME_STARTED == "game.started"
    assert EventType.PLAYER_ELIMINATED == "player.eliminated"
    assert EventType.JURY_VERDICT == "jury.verdict"
    assert EventType.STRATEGY_MESSAGE == "strategy.message"
