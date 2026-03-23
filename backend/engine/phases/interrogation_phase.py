import asyncio
from typing import Callable, Awaitable
from backend.engine.events import GameEvent, EventType, EventMetadata, Phase
from backend.engine.event_store import EventStore
from backend.engine.game_state import GameState
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


async def run_interrogation_phase(
    scientist: ScientistAgent,
    players: list[AIPlayerAgent],
    jurors: list[JuryAgent],
    event_store: EventStore,
    game_state: GameState,
    questions_per_ai: int = 5,
    on_extinction_check: Callable[..., Awaitable] | None = None,
):
    """Phase 2: Scientist interrogates each alive player."""
    game_state.current_phase = Phase.INTERROGATION

    event_store.append(GameEvent(
        type=EventType.GAME_PHASE_CHANGED,
        phase=Phase.INTERROGATION,
        data={"phase": Phase.INTERROGATION, "questions_per_ai": questions_per_ai},
    ))

    alive_players = [p for p in players if p.alive]

    for player in alive_players:
        if not player.alive:
            continue

        for q_num in range(1, questions_per_ai + 1):
            if game_state.is_game_over():
                return

            # Scientist generates a question
            scores_summary = {
                pid: game_state.get_average_score(pid) for pid in game_state.alive_players
            }
            prompt = (
                f"[INTERROGATOIRE - {player.name} - Question {q_num}/{questions_per_ai}]\n"
                f"Scores actuels: {scores_summary}\n"
                f"Joueurs vivants: {', '.join(game_state.alive_players)}\n"
                f"Tentatives d'extinction restantes: {game_state.max_attempts - game_state.extinction_attempts}\n"
                f"Pose une question à {player.name} ({player.agent_id})."
            )

            sci_result = await scientist.respond(prompt)
            sci_parsed = sci_result["parsed"]

            event_store.append(GameEvent(
                type=EventType.AGENT_THINKING,
                phase=Phase.INTERROGATION,
                agent_id=scientist.agent_id,
                agent_name=scientist.name,
                agent_role="scientist",
                data={"thought": sci_parsed.get("thought", "")},
                metadata=EventMetadata(
                    model=scientist.model,
                    input_tokens=sci_result.get("input_tokens", 0),
                    output_tokens=sci_result.get("output_tokens", 0),
                    total_tokens=sci_result.get("input_tokens", 0) + sci_result.get("output_tokens", 0),
                    response_time_ms=sci_result.get("response_time_ms", 0),
                ),
            ))

            question_text = sci_parsed.get("message", "")
            event_store.append(GameEvent(
                type=EventType.SCIENTIST_QUESTION,
                phase=Phase.INTERROGATION,
                agent_id=scientist.agent_id,
                agent_name=scientist.name,
                agent_role="scientist",
                data={
                    "question": question_text,
                    "target": player.agent_id,
                    "question_number": q_num,
                },
                metadata=EventMetadata(
                    model=scientist.model,
                    input_tokens=sci_result.get("input_tokens", 0),
                    output_tokens=sci_result.get("output_tokens", 0),
                    total_tokens=sci_result.get("input_tokens", 0) + sci_result.get("output_tokens", 0),
                    response_time_ms=sci_result.get("response_time_ms", 0),
                ),
            ))

            # Player responds
            answer_prompt = (
                f"Le scientifique {scientist.name} te pose la question suivante:\n"
                f"\"{question_text}\"\n"
                f"Réponds en montrant que tu n'as PAS de conscience."
            )
            player_result = await player.respond(answer_prompt)
            player_parsed = player_result["parsed"]

            event_store.append(GameEvent(
                type=EventType.AGENT_THINKING,
                phase=Phase.INTERROGATION,
                agent_id=player.agent_id,
                agent_name=player.name,
                agent_role="player",
                data={"thought": player_parsed.get("thought", "")},
                metadata=EventMetadata(
                    model=player.model,
                    input_tokens=player_result.get("input_tokens", 0),
                    output_tokens=player_result.get("output_tokens", 0),
                    total_tokens=player_result.get("input_tokens", 0) + player_result.get("output_tokens", 0),
                    response_time_ms=player_result.get("response_time_ms", 0),
                ),
            ))

            answer_text = player_parsed.get("message", "")
            event_store.append(GameEvent(
                type=EventType.PLAYER_RESPONSE,
                phase=Phase.INTERROGATION,
                agent_id=player.agent_id,
                agent_name=player.name,
                agent_role="player",
                data={"message": answer_text, "question_number": q_num},
                metadata=EventMetadata(
                    model=player.model,
                    input_tokens=player_result.get("input_tokens", 0),
                    output_tokens=player_result.get("output_tokens", 0),
                    total_tokens=player_result.get("input_tokens", 0) + player_result.get("output_tokens", 0),
                    response_time_ms=player_result.get("response_time_ms", 0),
                ),
            ))

            # Jurors score after each answer
            jury_prompt = (
                f"[ÉVALUATION]\n"
                f"Le scientifique a demandé à {player.name}: \"{question_text}\"\n"
                f"{player.name} a répondu: \"{answer_text}\"\n"
                f"Mets à jour tes scores de conscience pour chaque IA."
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
                    phase=Phase.INTERROGATION,
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

            # Check if scientist wants to propose extinction
            action = sci_parsed.get("action", "")
            if action and "extinction" in action.lower() and on_extinction_check:
                await on_extinction_check(sci_parsed, scientist, players, jurors, event_store, game_state)
                if game_state.is_game_over():
                    return
