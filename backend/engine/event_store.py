import json
import os
from pathlib import Path
from typing import Callable
from backend.engine.events import GameEvent, EventType


class EventStore:
    def __init__(self, game_id: str, games_dir: str = "games"):
        self.game_id = game_id
        self.games_dir = Path(games_dir)
        self.events: list[GameEvent] = []
        self._listeners: list[Callable[[GameEvent], None]] = []

    def append(self, event: GameEvent) -> GameEvent:
        self.events.append(event)
        for listener in self._listeners:
            listener(event)
        return event

    def on_event(self, callback: Callable[[GameEvent], None]):
        self._listeners.append(callback)

    def get_events_by_type(self, event_type: EventType) -> list[GameEvent]:
        return [e for e in self.events if e.type == event_type]

    def get_events_by_agent(self, agent_id: str) -> list[GameEvent]:
        return [e for e in self.events if e.agent_id == agent_id]

    def get_events_by_phase(self, phase: str) -> list[GameEvent]:
        return [e for e in self.events if e.phase == phase]

    async def save_to_disk(self, config: dict | None = None, stats: dict | None = None, result: dict | None = None):
        game_dir = self.games_dir / self.game_id
        game_dir.mkdir(parents=True, exist_ok=True)

        if config:
            (game_dir / "config.json").write_text(
                json.dumps(config, indent=2, default=str), encoding="utf-8"
            )

        events_data = {
            "game_id": self.game_id,
            "events": [e.model_dump(mode="json") for e in self.events],
        }
        if stats:
            events_data["stats"] = stats
        if result:
            events_data["result"] = result

        (game_dir / "events.json").write_text(
            json.dumps(events_data, indent=2, default=str), encoding="utf-8"
        )

    @classmethod
    def load_from_disk(cls, game_id: str, games_dir: str = "games") -> "EventStore":
        game_dir = Path(games_dir) / game_id
        events_file = game_dir / "events.json"
        data = json.loads(events_file.read_text(encoding="utf-8"))
        store = cls(game_id, games_dir)
        for e in data["events"]:
            store.events.append(GameEvent(**e))
        return store
