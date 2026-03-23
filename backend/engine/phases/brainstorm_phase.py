import asyncio
import time
from backend.engine.events import GameEvent, EventType, EventMetadata, Phase
from backend.engine.event_store import EventStore
from backend.agents.brainstorm_agent import BrainstormAgent
from backend.agents.prompts import BRAINSTORM_VOTE_PROMPT


async def run_brainstorm_debate(
    players: list[BrainstormAgent],
    event_store: EventStore,
    topic: str,
    round_num: int,
    duration_seconds: int = 180,
    sub_rounds: int = 3,
    is_running: callable = None,
):
    """Run a debate round: players discuss the topic in parallel sub-rounds."""
    event_store.append(GameEvent(
        type=EventType.GAME_PHASE_CHANGED,
        phase=Phase.BRAINSTORM_DEBATE,
        data={
            "phase": Phase.BRAINSTORM_DEBATE,
            "round": round_num,
            "duration_seconds": duration_seconds,
        },
    ))

    start_time = time.time()
    messages_history: list[str] = []

    for sub_round in range(1, sub_rounds + 1):
        if is_running and not is_running():
            break

        elapsed = time.time() - start_time
        if elapsed >= duration_seconds:
            break

        remaining = max(0, duration_seconds - elapsed)

        event_store.append(GameEvent(
            type=EventType.GAME_TIMER,
            phase=Phase.BRAINSTORM_DEBATE,
            data={
                "elapsed": int(elapsed),
                "remaining": int(remaining),
                "round": round_num,
                "sub_round": sub_round,
            },
        ))

        # Emit typing events
        for player in players:
            event_store.append(GameEvent(
                type=EventType.AGENT_TYPING,
                phase=Phase.BRAINSTORM_DEBATE,
                agent_id=player.agent_id,
                agent_name=player.name,
                agent_role="brainstormer",
            ))

        recent = messages_history[-12:] if messages_history else []
        context = "\n".join(recent) if recent else "Début du débat."

        prompt = (
            f"[BRAINSTORMING - Round {round_num}, Échange {sub_round}/{sub_rounds}]\n"
            f"SUJET: {topic}\n\n"
            f"Messages récents:\n{context}\n\n"
            f"Continue le débat. Propose, argumente ou critique les idées des autres."
        )

        tasks = [player.respond(prompt) for player in players]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for player, result in zip(players, results):
            if isinstance(result, Exception):
                continue

            parsed = result["parsed"]

            event_store.append(GameEvent(
                type=EventType.AGENT_THINKING,
                phase=Phase.BRAINSTORM_DEBATE,
                agent_id=player.agent_id,
                agent_name=player.name,
                agent_role="brainstormer",
                data={"content": parsed.get("thought", "")},
            ))

            message = parsed.get("message", "")
            messages_history.append(f"{player.name}: {message}")

            event_store.append(GameEvent(
                type=EventType.BRAINSTORM_MESSAGE,
                phase=Phase.BRAINSTORM_DEBATE,
                agent_id=player.agent_id,
                agent_name=player.name,
                agent_role="brainstormer",
                data={"content": message, "round": round_num, "sub_round": sub_round},
                metadata=EventMetadata(
                    model=player.model,
                    input_tokens=result.get("input_tokens", 0),
                    output_tokens=result.get("output_tokens", 0),
                    total_tokens=result.get("input_tokens", 0) + result.get("output_tokens", 0),
                    response_time_ms=result.get("response_time_ms", 0),
                ),
            ))

        await asyncio.sleep(1)

    return messages_history


async def run_brainstorm_vote(
    players: list[BrainstormAgent],
    event_store: EventStore,
    topic: str,
    round_num: int,
    messages_history: list[str],
    consensus_threshold: int = 3,
    is_running: callable = None,
) -> dict:
    """Run a vote round: players vote POUR/CONTRE on a consensus answer.

    Returns dict with keys: consensus (bool), votes_pour (int),
    proposed_answer (str or None), votes (list of vote details).
    """
    event_store.append(GameEvent(
        type=EventType.GAME_PHASE_CHANGED,
        phase=Phase.BRAINSTORM_VOTE,
        data={"phase": Phase.BRAINSTORM_VOTE, "round": round_num},
    ))

    recent = messages_history[-16:] if messages_history else []
    context = "\n".join(recent)

    prompt = (
        f"[VOTE - Round {round_num}]\n"
        f"SUJET: {topic}\n\n"
        f"Résumé du débat:\n{context}\n\n"
        f"{BRAINSTORM_VOTE_PROMPT}"
    )

    # Emit typing
    for player in players:
        event_store.append(GameEvent(
            type=EventType.AGENT_TYPING,
            phase=Phase.BRAINSTORM_VOTE,
            agent_id=player.agent_id,
            agent_name=player.name,
            agent_role="brainstormer",
        ))

    tasks = [player.respond(prompt) for player in players]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    votes_pour = 0
    proposed_answer = None
    votes = []

    for player, result in zip(players, results):
        if isinstance(result, Exception):
            votes.append({"agent_id": player.agent_id, "vote": "ERREUR"})
            continue

        parsed = result["parsed"]

        event_store.append(GameEvent(
            type=EventType.AGENT_THINKING,
            phase=Phase.BRAINSTORM_VOTE,
            agent_id=player.agent_id,
            agent_name=player.name,
            agent_role="brainstormer",
            data={"content": parsed.get("thought", "")},
        ))

        vote = parsed.get("vote", "CONTRE")
        justification = parsed.get("vote_justification", "")
        answer = parsed.get("proposed_answer")

        if vote == "POUR":
            votes_pour += 1
            if answer:
                proposed_answer = answer

        vote_data = {
            "vote": vote,
            "justification": justification,
            "proposed_answer": answer,
            "round": round_num,
        }
        votes.append({"agent_id": player.agent_id, **vote_data})

        event_store.append(GameEvent(
            type=EventType.BRAINSTORM_VOTE,
            phase=Phase.BRAINSTORM_VOTE,
            agent_id=player.agent_id,
            agent_name=player.name,
            agent_role="brainstormer",
            data=vote_data,
            metadata=EventMetadata(
                model=player.model,
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
                total_tokens=result.get("input_tokens", 0) + result.get("output_tokens", 0),
                response_time_ms=result.get("response_time_ms", 0),
            ),
        ))

    consensus = votes_pour >= consensus_threshold

    if consensus:
        event_store.append(GameEvent(
            type=EventType.BRAINSTORM_CONSENSUS,
            phase=Phase.BRAINSTORM_VOTE,
            data={
                "round": round_num,
                "votes_pour": votes_pour,
                "votes_total": len(players),
                "proposed_answer": proposed_answer,
                "votes": votes,
            },
        ))
    else:
        event_store.append(GameEvent(
            type=EventType.BRAINSTORM_NO_CONSENSUS,
            phase=Phase.BRAINSTORM_VOTE,
            data={
                "round": round_num,
                "votes_pour": votes_pour,
                "votes_total": len(players),
                "votes": votes,
            },
        ))

    return {
        "consensus": consensus,
        "votes_pour": votes_pour,
        "proposed_answer": proposed_answer,
        "votes": votes,
    }
