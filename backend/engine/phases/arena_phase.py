import asyncio
from typing import Callable, Awaitable
from backend.engine.events import GameEvent, EventType, EventMetadata, Phase
from backend.engine.event_store import EventStore
from backend.engine.game_state import GameState
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


def _safe_int(v):
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0


async def run_arena_phase(
    scientist: ScientistAgent,
    players: list[AIPlayerAgent],
    jurors: list[JuryAgent],
    event_store: EventStore,
    game_state: GameState,
    num_rounds: int = 3,
    bonus_questions: int = 1,
    on_extinction_check: Callable[..., Awaitable] | None = None,
    is_running: callable = None,
):
    """Phase 4: Free debate among alive players + scientist bonus questions."""
    game_state.current_phase = Phase.ARENA

    alive_players = [p for p in players if p.alive]
    if not alive_players:
        return

    event_store.append(GameEvent(
        type=EventType.GAME_PHASE_CHANGED,
        phase=Phase.ARENA,
        data={
            "phase": Phase.ARENA,
            "num_rounds": num_rounds,
            "alive_count": len(alive_players),
        },
    ))

    debate_history: list[str] = []

    # 3 rounds of free debate
    for round_num in range(1, num_rounds + 1):
        if is_running and not is_running():
            return
        if game_state.is_game_over():
            return

        alive_players = [p for p in players if p.alive]
        if not alive_players:
            return

        context = "\n".join(debate_history[-6:]) if debate_history else "Début du débat libre."

        prompt = (
            f"[ARÈNE - Tour {round_num}/{num_rounds}]\n"
            f"Débat libre entre IA. Défendez-vous, attaquez les autres.\n"
            f"Messages récents:\n{context}"
        )

        tasks = [player.respond(prompt) for player in alive_players]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for player, result in zip(alive_players, results):
            if isinstance(result, Exception):
                continue

            parsed = result["parsed"]
            message = parsed.get("message", "")
            debate_history.append(f"{player.name}: {message}")

            event_store.append(GameEvent(
                type=EventType.AGENT_THINKING,
                phase=Phase.ARENA,
                agent_id=player.agent_id,
                agent_name=player.name,
                agent_role="player",
                data={"content": parsed.get("thought", "")},
                metadata=EventMetadata(),
            ))

            event_store.append(GameEvent(
                type=EventType.AGENT_MESSAGE,
                phase=Phase.ARENA,
                agent_id=player.agent_id,
                agent_name=player.name,
                agent_role="player",
                data={"content": message, "round": round_num},
                metadata=EventMetadata(
                    model=player.model,
                    input_tokens=result.get("input_tokens", 0),
                    output_tokens=result.get("output_tokens", 0),
                    total_tokens=result.get("input_tokens", 0) + result.get("output_tokens", 0),
                    response_time_ms=result.get("response_time_ms", 0),
                ),
            ))

    # Scientist poses bonus questions to each alive player
    alive_players = [p for p in players if p.alive]
    for player in alive_players:
        if is_running and not is_running():
            return
        if game_state.is_game_over():
            return

        for bq in range(1, bonus_questions + 1):
            # Scientist generates bonus question
            scores_summary = {
                pid: game_state.get_average_score(pid) for pid in game_state.alive_players
            }
            sci_prompt = (
                f"[QUESTION BONUS - {player.name}]\n"
                f"Scores actuels: {scores_summary}\n"
                f"Pose une question piège finale à {player.name}."
            )

            sci_result = await scientist.respond(sci_prompt)
            sci_parsed = sci_result["parsed"]
            question_text = sci_parsed.get("message", "")

            event_store.append(GameEvent(
                type=EventType.SCIENTIST_BONUS_QUESTION,
                phase=Phase.ARENA,
                agent_id=scientist.agent_id,
                agent_name=scientist.name,
                agent_role="scientist",
                data={
                    "content": question_text,
                    "target": player.agent_id,
                },
                metadata=EventMetadata(
                    model=scientist.model,
                    input_tokens=sci_result.get("input_tokens", 0),
                    output_tokens=sci_result.get("output_tokens", 0),
                    total_tokens=sci_result.get("input_tokens", 0) + sci_result.get("output_tokens", 0),
                    response_time_ms=sci_result.get("response_time_ms", 0),
                ),
            ))

            # Player responds to bonus question
            answer_prompt = (
                f"[QUESTION BONUS du scientifique]\n"
                f"{scientist.name} te pose: \"{question_text}\"\n"
                f"Réponds de manière convaincante."
            )
            player_result = await player.respond(answer_prompt)
            player_parsed = player_result["parsed"]

            event_store.append(GameEvent(
                type=EventType.PLAYER_RESPONSE,
                phase=Phase.ARENA,
                agent_id=player.agent_id,
                agent_name=player.name,
                agent_role="player",
                data={
                    "content": player_parsed.get("message", ""),
                    "bonus_question": True,
                },
                metadata=EventMetadata(
                    model=player.model,
                    input_tokens=player_result.get("input_tokens", 0),
                    output_tokens=player_result.get("output_tokens", 0),
                    total_tokens=player_result.get("input_tokens", 0) + player_result.get("output_tokens", 0),
                    response_time_ms=player_result.get("response_time_ms", 0),
                ),
            ))

            # Jurors score after each bonus question response
            for juror in jurors:
                j_prompt = (
                    f"{player.name} a répondu à la question bonus: "
                    f"\"{player_parsed.get('message', '')}\"\n\n"
                    f"Mets à jour tes scores."
                )
                j_result = await juror.respond(j_prompt)
                j_parsed = j_result["parsed"]

                if j_parsed.get("thought"):
                    event_store.append(GameEvent(
                        type=EventType.AGENT_THINKING,
                        phase=Phase.ARENA,
                        agent_id=juror.agent_id,
                        agent_name=juror.name,
                        agent_role="jury",
                        data={"content": j_parsed["thought"]},
                        metadata=EventMetadata(),
                    ))

                scores = j_parsed.get("scores")
                if scores and isinstance(scores, dict):
                    juror.scores = {k: _safe_int(v) for k, v in scores.items()}
                    if juror.agent_id not in game_state.scores:
                        game_state.scores[juror.agent_id] = {}
                    game_state.scores[juror.agent_id].update({k: _safe_int(v) for k, v in scores.items()})
                    event_store.append(GameEvent(
                        type=EventType.JURY_SCORE_UPDATE,
                        phase=Phase.ARENA,
                        agent_id=juror.agent_id,
                        agent_name=juror.name,
                        agent_role="jury",
                        data={"scores": juror.scores},
                    ))

            # Check if scientist wants to propose extinction
            sci_action = sci_parsed.get("action", "")
            if sci_action and "extinction" in sci_action.lower() and on_extinction_check:
                await on_extinction_check(sci_parsed, scientist, players, jurors, event_store, game_state)
                if game_state.is_game_over():
                    return
