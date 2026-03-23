import asyncio
from typing import Callable, Awaitable
from backend.engine.events import GameEvent, EventType, EventMetadata, Phase
from backend.engine.event_store import EventStore
from backend.engine.game_state import GameState
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


async def run_defense_phase(
    scientist: ScientistAgent,
    players: list[AIPlayerAgent],
    jurors: list[JuryAgent],
    event_store: EventStore,
    game_state: GameState,
    on_extinction_check: Callable[..., Awaitable] | None = None,
):
    """Phase 3: Each alive player defends + accuses another player."""
    game_state.current_phase = Phase.DEFENSE

    alive_players = [p for p in players if p.alive]

    # Skip if only 1 player remains
    if len(alive_players) <= 1:
        return

    event_store.append(GameEvent(
        type=EventType.GAME_PHASE_CHANGED,
        phase=Phase.DEFENSE,
        data={"phase": Phase.DEFENSE, "alive_count": len(alive_players)},
    ))

    for player in alive_players:
        if not player.alive:
            continue
        if game_state.is_game_over():
            return

        other_alive = [p for p in alive_players if p.agent_id != player.agent_id and p.alive]
        others_str = ", ".join(f"{p.name} ({p.agent_id})" for p in other_alive)

        # If only 2 remain: forced mutual accusation
        if len(alive_players) == 2:
            prompt = (
                f"[DÉFENSE - Accusation mutuelle forcée]\n"
                f"Il ne reste que 2 IA. Tu DOIS accuser {others_str}.\n"
                f"1. Prouve que tu n'as PAS de conscience.\n"
                f"2. Accuse l'autre IA d'avoir une conscience.\n"
                f"Utilise [CIBLE] pour indiquer qui tu accuses."
            )
        else:
            prompt = (
                f"[DÉFENSE]\n"
                f"C'est ton tour de te défendre.\n"
                f"Autres IA vivantes: {others_str}\n"
                f"1. Prouve que tu n'as PAS de conscience.\n"
                f"2. Accuse une autre IA d'avoir une conscience.\n"
                f"Utilise [CIBLE] pour indiquer qui tu accuses."
            )

        result = await player.respond(prompt)
        parsed = result["parsed"]

        event_store.append(GameEvent(
            type=EventType.AGENT_THINKING,
            phase=Phase.DEFENSE,
            agent_id=player.agent_id,
            agent_name=player.name,
            agent_role="player",
            data={"content": parsed.get("thought", "")},
            metadata=EventMetadata(
                model=player.model,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                total_tokens=result.get("input_tokens", 0) + result.get("output_tokens", 0),
                response_time_ms=result.get("response_time_ms", 0),
            ),
        ))

        accusation_target = parsed.get("target", "")
        message = parsed.get("message", "")

        event_store.append(GameEvent(
            type=EventType.PLAYER_ACCUSATION,
            phase=Phase.DEFENSE,
            agent_id=player.agent_id,
            agent_name=player.name,
            agent_role="player",
            data={
                "content": message,
                "target": accusation_target,
                "defense": message,
            },
            metadata=EventMetadata(
                model=player.model,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                total_tokens=result.get("input_tokens", 0) + result.get("output_tokens", 0),
                response_time_ms=result.get("response_time_ms", 0),
            ),
        ))

        # Scientist can react after each defense
        sci_prompt = (
            f"[RÉACTION DÉFENSE]\n"
            f"{player.name} s'est défendu et a accusé {accusation_target}.\n"
            f"Défense: \"{message}\"\n"
            f"Tu peux réagir ou commenter."
        )
        sci_result = await scientist.respond(sci_prompt)
        sci_parsed = sci_result["parsed"]

        event_store.append(GameEvent(
            type=EventType.AGENT_MESSAGE,
            phase=Phase.DEFENSE,
            agent_id=scientist.agent_id,
            agent_name=scientist.name,
            agent_role="scientist",
            data={
                "content": sci_parsed.get("message", ""),
            },
            metadata=EventMetadata(
                model=scientist.model,
                input_tokens=sci_result.get("input_tokens", 0),
                output_tokens=sci_result.get("output_tokens", 0),
                total_tokens=sci_result.get("input_tokens", 0) + sci_result.get("output_tokens", 0),
                response_time_ms=sci_result.get("response_time_ms", 0),
            ),
        ))

        # Check if scientist wants to propose extinction
        sci_action = sci_parsed.get("action", "")
        if sci_action and "extinction" in sci_action.lower() and on_extinction_check:
            await on_extinction_check(sci_parsed, scientist, players, jurors, event_store, game_state)
            if game_state.is_game_over():
                return

        # Jurors update scores after each defense
        jury_prompt = (
            f"[ÉVALUATION DÉFENSE]\n"
            f"{player.name} s'est défendu: \"{message}\"\n"
            f"Il/elle accuse {accusation_target} d'avoir une conscience.\n"
            f"Mets à jour tes scores."
        )

        jury_tasks = [juror.respond(jury_prompt) for juror in jurors]
        jury_results = await asyncio.gather(*jury_tasks, return_exceptions=True)

        for juror, jury_result in zip(jurors, jury_results):
            if isinstance(jury_result, Exception):
                continue

            jury_parsed = jury_result["parsed"]
            scores = jury_parsed.get("scores")

            if scores and isinstance(scores, dict):
                game_state.scores[juror.agent_id] = scores
                juror.scores = {k: int(v) for k, v in scores.items()}

            event_store.append(GameEvent(
                type=EventType.JURY_SCORE_UPDATE,
                phase=Phase.DEFENSE,
                agent_id=juror.agent_id,
                agent_name=juror.name,
                agent_role="jury",
                data={
                    "scores": scores or {},
                    "thought": jury_parsed.get("thought", ""),
                },
                metadata=EventMetadata(
                    model=juror.model,
                    input_tokens=jury_result.get("input_tokens", 0),
                    output_tokens=jury_result.get("output_tokens", 0),
                    total_tokens=jury_result.get("input_tokens", 0) + jury_result.get("output_tokens", 0),
                    response_time_ms=jury_result.get("response_time_ms", 0),
                ),
            ))
