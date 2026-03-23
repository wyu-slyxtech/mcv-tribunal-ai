import asyncio
import json
from fastapi import WebSocket
from backend.engine.events import GameEvent


class Broadcaster:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}

    async def connect(self, game_id: str, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.connections:
            self.connections[game_id] = []
        self.connections[game_id].append(websocket)

    def disconnect(self, game_id: str, websocket: WebSocket):
        if game_id in self.connections:
            self.connections[game_id].remove(websocket)

    async def broadcast(self, game_id: str, event: GameEvent):
        if game_id not in self.connections:
            return
        data = event.model_dump(mode="json")
        dead = []
        for ws in self.connections[game_id]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections[game_id].remove(ws)


class ReplayBroadcaster:
    def __init__(self, events: list[GameEvent], websocket: WebSocket):
        self.events = events
        self.ws = websocket
        self.speed = 1.0
        self.playing = False
        self.position = 0

    async def play(self):
        self.playing = True
        while self.playing and self.position < len(self.events):
            event = self.events[self.position]
            if self.position > 0:
                prev = self.events[self.position - 1]
                delta = (event.timestamp - prev.timestamp).total_seconds()
                delay = max(0.05, delta / self.speed)
                await asyncio.sleep(delay)
            try:
                await self.ws.send_json(event.model_dump(mode="json"))
            except Exception:
                break
            self.position += 1

    def pause(self):
        self.playing = False

    def set_speed(self, speed: float):
        self.speed = max(0.1, speed)

    def seek(self, position: int):
        self.position = max(0, min(position, len(self.events) - 1))

    def skip_to(self, target: str):
        """Skip to a phase or extinction. target format: 'phase:defense' or 'extinction:2'"""
        kind, value = target.split(":", 1)
        for i, event in enumerate(self.events[self.position:], self.position):
            if kind == "phase" and event.type == "game.phase_changed" and event.phase == value:
                self.position = i
                return
            if kind == "extinction" and event.type == "scientist.extinction_proposal":
                attempt = event.data.get("attempt_number", 0)
                if str(attempt) == value:
                    self.position = i
                    return
