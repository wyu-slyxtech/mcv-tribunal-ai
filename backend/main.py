import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.config.game_config import GameConfig
from backend.config.models_config import PROVIDERS
from backend.config.personalities import PLAYER_PERSONALITIES, SCIENTIST_PERSONALITIES
from backend.engine.game_engine import GameEngine
from backend.engine.event_store import EventStore
from backend.ws.broadcaster import Broadcaster, ReplayBroadcaster

load_dotenv()

app = FastAPI(title="Tribunal IA", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

broadcaster = Broadcaster()
active_games: dict[str, GameEngine] = {}
GAMES_DIR = Path("games")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/game/create")
async def create_game(config: GameConfig):
    engine = GameEngine(config)
    active_games[config.game_id] = engine
    engine.event_store.on_event(
        lambda event: asyncio.create_task(broadcaster.broadcast(config.game_id, event))
    )
    return {"game_id": config.game_id, "status": "created"}


@app.post("/api/game/{game_id}/start")
async def start_game(game_id: str):
    engine = active_games.get(game_id)
    if not engine:
        raise HTTPException(404, "Game not found")
    if engine.running:
        raise HTTPException(400, "Game already running")
    asyncio.create_task(engine.run())
    return {"game_id": game_id, "status": "started"}


@app.post("/api/game/{game_id}/stop")
async def stop_game(game_id: str):
    engine = active_games.get(game_id)
    if not engine:
        raise HTTPException(404, "Game not found")
    engine.stop()
    return {"game_id": game_id, "status": "stopped"}


@app.get("/api/game/{game_id}/status")
async def game_status(game_id: str):
    engine = active_games.get(game_id)
    if engine:
        return {
            "game_id": game_id,
            "running": engine.running,
            "phase": engine.game_state.current_phase,
            "alive": engine.game_state.alive_players,
            "eliminated": engine.game_state.eliminated_players,
            "extinction_attempts": engine.game_state.extinction_attempts,
        }
    game_dir = GAMES_DIR / game_id
    if game_dir.exists():
        return {"game_id": game_id, "running": False, "status": "completed"}
    raise HTTPException(404, "Game not found")


@app.get("/api/game/{game_id}/events")
async def game_events(game_id: str):
    # If the game is active in memory, return live events
    engine = active_games.get(game_id)
    if engine:
        return {
            "game_id": game_id,
            "events": [e.model_dump(mode="json") for e in engine.event_store.events],
        }
    # Otherwise, read from disk
    game_dir = GAMES_DIR / game_id
    events_file = game_dir / "events.json"
    if not events_file.exists():
        raise HTTPException(404, "Events not found")
    return json.loads(events_file.read_text(encoding="utf-8"))


@app.get("/api/game/{game_id}/stats")
async def game_stats(game_id: str):
    game_dir = GAMES_DIR / game_id
    events_file = game_dir / "events.json"
    if not events_file.exists():
        raise HTTPException(404, "Stats not found")
    data = json.loads(events_file.read_text(encoding="utf-8"))
    return data.get("stats", {})


@app.get("/api/games")
async def list_games():
    games = []
    if GAMES_DIR.exists():
        for d in sorted(GAMES_DIR.iterdir(), reverse=True):
            if d.is_dir() and (d / "events.json").exists():
                data = json.loads((d / "events.json").read_text(encoding="utf-8"))
                stats = data.get("stats", {})
                result = data.get("result", {})
                events_list = data.get("events", [])
                started = events_list[0]["timestamp"] if events_list else None
                ended = events_list[-1]["timestamp"] if events_list else None
                models_used = list(set(
                    a.get("model", "") for a in stats.get("per_agent", {}).values() if a.get("model")
                ))
                games.append({
                    "game_id": d.name,
                    "result": result,
                    "started_at": started,
                    "ended_at": ended,
                    "models_used": models_used,
                    "total_tokens": stats.get("total_tokens", 0),
                    "total_cost": stats.get("total_estimated_cost_usd", 0),
                })
    return {"games": games}


@app.delete("/api/game/{game_id}")
async def delete_game(game_id: str):
    import shutil
    game_dir = GAMES_DIR / game_id
    if game_dir.exists():
        shutil.rmtree(game_dir)
    active_games.pop(game_id, None)
    return {"game_id": game_id, "status": "deleted"}


@app.get("/api/providers")
async def list_providers():
    return {"providers": PROVIDERS}


@app.get("/api/personalities")
async def list_personalities():
    return {"player": PLAYER_PERSONALITIES, "scientist": SCIENTIST_PERSONALITIES}


@app.get("/api/pricing")
async def get_pricing():
    pricing_path = Path(__file__).parent / "config" / "pricing.json"
    if pricing_path.exists():
        return json.loads(pricing_path.read_text(encoding="utf-8"))
    return {}


@app.websocket("/ws/game/{game_id}")
async def ws_game(websocket: WebSocket, game_id: str):
    await broadcaster.connect(game_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(game_id, websocket)


@app.websocket("/ws/replay/{game_id}")
async def ws_replay(websocket: WebSocket, game_id: str):
    await websocket.accept()
    store = EventStore.load_from_disk(game_id)
    await websocket.send_json({
        "type": "replay.metadata",
        "data": {"total_events": len(store.events)},
    })
    replay = ReplayBroadcaster(store.events, websocket)
    replay_task = None
    try:
        while True:
            msg = await websocket.receive_json()
            cmd = msg.get("command")
            if cmd == "play":
                if replay_task and not replay_task.done():
                    replay_task.cancel()
                replay_task = asyncio.create_task(replay.play())
            elif cmd == "pause":
                replay.pause()
                if replay_task and not replay_task.done():
                    replay_task.cancel()
                replay_task = None
            elif cmd == "speed":
                replay.set_speed(msg.get("value", 1.0))
            elif cmd == "seek":
                replay.seek(msg.get("position", 0))
            elif cmd == "skip_to":
                replay.skip_to(msg.get("target", "phase:strategy"))
            elif cmd == "step":
                direction = msg.get("direction", "forward")
                if direction == "forward" and replay.position < len(replay.events) - 1:
                    replay.position += 1
                    await websocket.send_json(replay.events[replay.position].model_dump(mode="json"))
                elif direction == "back" and replay.position > 0:
                    replay.position -= 1
                    await websocket.send_json(replay.events[replay.position].model_dump(mode="json"))
    except WebSocketDisconnect:
        replay.pause()
        if replay_task and not replay_task.done():
            replay_task.cancel()
