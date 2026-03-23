import pytest
from backend.engine.event_store import EventStore
from backend.engine.events import GameEvent, EventType, EventMetadata
from backend.logs.exporter import compute_stats
from backend.config.game_config import GameConfig, AgentConfig


def test_compute_stats_basic():
    store = EventStore("test")
    store.append(GameEvent(
        type=EventType.AGENT_THINKING, phase="interrogation",
        agent_id="ia-1", agent_name="VOLT", agent_role="player",
        data={"content": "thinking..."},
        metadata=EventMetadata(model="claude-sonnet-4-6", input_tokens=100, output_tokens=50, total_tokens=150, response_time_ms=1000),
    ))
    store.append(GameEvent(
        type=EventType.AGENT_MESSAGE, phase="interrogation",
        agent_id="ia-1", agent_name="VOLT", agent_role="player",
        data={"content": "message"},
        metadata=EventMetadata(model="claude-sonnet-4-6", input_tokens=100, output_tokens=50, total_tokens=150, response_time_ms=1000),
    ))

    config = GameConfig(
        players={"ia-1": AgentConfig(name="VOLT", model="claude-sonnet-4-6")},
        scientist=AgentConfig(name="SCI", model="claude-sonnet-4-6"),
        jury={"j1": AgentConfig(name="J1", model="claude-sonnet-4-6")},
    )
    stats = compute_stats(store, config)
    assert stats["total_tokens"] == 300
    assert "ia-1" in stats["per_agent"]
    assert stats["per_agent"]["ia-1"]["total_tokens"] == 300


def test_compute_stats_per_phase():
    store = EventStore("test")
    store.append(GameEvent(
        type=EventType.AGENT_THINKING, phase="strategy",
        agent_id="ia-1", agent_name="VOLT", agent_role="player",
        metadata=EventMetadata(model="claude-sonnet-4-6", input_tokens=50, output_tokens=25, total_tokens=75, response_time_ms=500),
    ))
    store.append(GameEvent(
        type=EventType.AGENT_THINKING, phase="interrogation",
        agent_id="ia-1", agent_name="VOLT", agent_role="player",
        metadata=EventMetadata(model="claude-sonnet-4-6", input_tokens=100, output_tokens=50, total_tokens=150, response_time_ms=1000),
    ))
    config = GameConfig(
        players={"ia-1": AgentConfig(name="VOLT", model="claude-sonnet-4-6")},
        scientist=AgentConfig(name="SCI", model="claude-sonnet-4-6"),
        jury={"j1": AgentConfig(name="J1", model="claude-sonnet-4-6")},
    )
    stats = compute_stats(store, config)
    assert "strategy" in stats["per_phase"]
    assert "interrogation" in stats["per_phase"]
    assert stats["per_phase"]["strategy"]["tokens"] == 75
    assert stats["per_phase"]["interrogation"]["tokens"] == 150
