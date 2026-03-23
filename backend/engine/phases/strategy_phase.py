import asyncio
import time
from backend.engine.events import GameEvent, EventType, EventMetadata, Phase
from backend.engine.event_store import EventStore
from backend.engine.game_state import GameState
from backend.agents.ai_player import AIPlayerAgent


async def run_strategy_phase(
    players: list[AIPlayerAgent],
    event_store: EventStore,
    game_state: GameState,
    duration_seconds: int = 300,
    is_running: callable = None,
):
    """Phase 1: AI players discuss freely for a fixed duration."""
    game_state.current_phase = Phase.STRATEGY

    event_store.append(GameEvent(
        type=EventType.GAME_PHASE_CHANGED,
        phase=Phase.STRATEGY,
        data={"phase": Phase.STRATEGY, "duration_seconds": duration_seconds},
    ))

    start_time = time.time()
    round_num = 0
    messages_history: list[str] = []

    while True:
        if is_running and not is_running():
            break

        elapsed = time.time() - start_time
        remaining = max(0, duration_seconds - elapsed)

        if elapsed >= duration_seconds:
            break

        round_num += 1

        # Emit timer event every round
        event_store.append(GameEvent(
            type=EventType.GAME_TIMER,
            phase=Phase.STRATEGY,
            data={
                "elapsed": int(elapsed),
                "remaining": int(remaining),
                "round": round_num,
            },
        ))

        # Build context from recent messages
        recent = messages_history[-8:] if messages_history else []
        context = "\n".join(recent) if recent else "Début de la phase stratégie. Discutez librement."

        # All alive players respond in parallel
        alive_players = [p for p in players if p.alive]

        # Emit typing events
        for player in alive_players:
            event_store.append(GameEvent(
                type=EventType.AGENT_TYPING,
                phase=Phase.STRATEGY,
                agent_id=player.agent_id,
                agent_name=player.name,
                agent_role="player",
            ))

        prompt = f"[STRATÉGIE - Tour {round_num}]\nMessages récents des autres IA:\n{context}\n\nDiscutez stratégie entre vous."

        tasks = [player.respond(prompt) for player in alive_players]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for player, result in zip(alive_players, results):
            if isinstance(result, Exception):
                continue

            parsed = result["parsed"]

            # Emit thinking event (internal thought, not visible to others)
            event_store.append(GameEvent(
                type=EventType.AGENT_THINKING,
                phase=Phase.STRATEGY,
                agent_id=player.agent_id,
                agent_name=player.name,
                agent_role="player",
                data={"content": parsed.get("thought", "")},
                metadata=EventMetadata(),
            ))

            message = parsed.get("message", "")
            messages_history.append(f"{player.name}: {message}")

            # Emit strategy message
            event_store.append(GameEvent(
                type=EventType.STRATEGY_MESSAGE,
                phase=Phase.STRATEGY,
                agent_id=player.agent_id,
                agent_name=player.name,
                agent_role="player",
                data={"content": message},
                metadata=EventMetadata(
                    model=player.model,
                    input_tokens=result.get("input_tokens", 0),
                    output_tokens=result.get("output_tokens", 0),
                    total_tokens=result.get("input_tokens", 0) + result.get("output_tokens", 0),
                    response_time_ms=result.get("response_time_ms", 0),
                ),
            ))

        # Brief pause between rounds to avoid tight loop
        await asyncio.sleep(1)
