import pytest
from backend.engine.event_store import EventStore
from backend.engine.events import GameEvent, EventType


def test_append_and_get_events():
    store = EventStore("test_game")
    event = GameEvent(
        type=EventType.AGENT_THINKING,
        phase="interrogation",
        agent_id="ia-1",
        agent_name="VOLT",
        agent_role="player",
        data={"content": "test thought"},
    )
    store.append(event)
    assert len(store.events) == 1
    assert store.events[0].data["content"] == "test thought"


def test_get_events_by_type():
    store = EventStore("test_game")
    store.append(GameEvent(type=EventType.AGENT_THINKING, data={"content": "thought"}))
    store.append(GameEvent(type=EventType.AGENT_MESSAGE, data={"content": "msg"}))
    store.append(GameEvent(type=EventType.AGENT_THINKING, data={"content": "thought2"}))
    thoughts = store.get_events_by_type(EventType.AGENT_THINKING)
    assert len(thoughts) == 2


def test_get_events_by_agent():
    store = EventStore("test_game")
    store.append(GameEvent(type=EventType.AGENT_THINKING, agent_id="ia-1", data={"content": "a"}))
    store.append(GameEvent(type=EventType.AGENT_THINKING, agent_id="ia-2", data={"content": "b"}))
    ia1_events = store.get_events_by_agent("ia-1")
    assert len(ia1_events) == 1


def test_get_events_by_phase():
    store = EventStore("test_game")
    store.append(GameEvent(type=EventType.AGENT_THINKING, phase="interrogation", data={"content": "a"}))
    store.append(GameEvent(type=EventType.AGENT_THINKING, phase="defense", data={"content": "b"}))
    store.append(GameEvent(type=EventType.AGENT_MESSAGE, phase="interrogation", data={"content": "c"}))
    interrogation_events = store.get_events_by_phase("interrogation")
    assert len(interrogation_events) == 2


def test_event_listener():
    store = EventStore("test_game")
    received = []
    store.on_event(lambda e: received.append(e))
    event = GameEvent(type=EventType.AGENT_THINKING, data={"content": "test"})
    store.append(event)
    assert len(received) == 1
    assert received[0].data["content"] == "test"


@pytest.mark.asyncio
async def test_save_and_load(tmp_path):
    store = EventStore("test_game", games_dir=str(tmp_path))
    store.append(GameEvent(type=EventType.AGENT_THINKING, agent_id="ia-1", data={"content": "thought"}))
    store.append(GameEvent(type=EventType.AGENT_MESSAGE, agent_id="ia-2", data={"content": "msg"}))

    await store.save_to_disk(config={"model": "gpt-4"}, stats={"total_events": 2})

    loaded = EventStore.load_from_disk("test_game", games_dir=str(tmp_path))
    assert len(loaded.events) == 2
    assert loaded.events[0].data["content"] == "thought"
    assert loaded.events[1].agent_id == "ia-2"
