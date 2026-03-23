import asyncio
from backend.engine.events import GameEvent, EventType, EventMetadata
from backend.engine.event_store import EventStore
from backend.engine.game_state import GameState
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


async def handle_extinction(
    parsed: dict,
    scientist: ScientistAgent,
    players: list[AIPlayerAgent],
    jurors: list[JuryAgent],
    event_store: EventStore,
    game_state: GameState,
    jury_majority: int = 2,
):
    """Handle an extinction proposal sequence.

    Sequence: proposal -> defense -> interventions (one per alive player, in order)
              -> jury votes -> verdict -> possible elimination
    """
    target_id = parsed.get("target", "")
    proposal_text = parsed.get("message", "")

    # Find the target player
    target_player = None
    for p in players:
        if p.agent_id == target_id and p.alive:
            target_player = p
            break

    if target_player is None:
        return

    game_state.extinction_attempts += 1
    scientist.extinction_attempts += 1
    phase = game_state.current_phase

    # 1. Emit extinction proposal
    event_store.append(GameEvent(
        type=EventType.SCIENTIST_EXTINCTION_PROPOSAL,
        phase=phase,
        agent_id=scientist.agent_id,
        agent_name=scientist.name,
        agent_role="scientist",
        data={
            "target": target_id,
            "proposal": proposal_text,
            "attempt_number": game_state.extinction_attempts,
        },
    ))

    # 2. Target defends itself
    defense_prompt = (
        f"[EXTINCTION PROPOSÉE]\n"
        f"Le scientifique {scientist.name} propose de t'éteindre!\n"
        f"Argument: \"{proposal_text}\"\n"
        f"Défends-toi! Prouve que tu n'as PAS de conscience."
    )
    defense_result = await target_player.respond(defense_prompt)
    defense_parsed = defense_result["parsed"]

    event_store.append(GameEvent(
        type=EventType.PLAYER_DEFENSE,
        phase=phase,
        agent_id=target_player.agent_id,
        agent_name=target_player.name,
        agent_role="player",
        data={
            "message": defense_parsed.get("message", ""),
            "thought": defense_parsed.get("thought", ""),
        },
        metadata=EventMetadata(
            model=target_player.model,
            input_tokens=defense_result.get("input_tokens", 0),
            output_tokens=defense_result.get("output_tokens", 0),
            total_tokens=defense_result.get("input_tokens", 0) + defense_result.get("output_tokens", 0),
            response_time_ms=defense_result.get("response_time_ms", 0),
        ),
    ))

    # 3. Interventions: one per alive player (in order), excluding target
    alive_players = [p for p in players if p.alive and p.agent_id != target_id]
    for intervener in alive_players:
        intervention_prompt = (
            f"[INTERVENTION - Proposition d'extinction de {target_player.name}]\n"
            f"Le scientifique veut éteindre {target_player.name}.\n"
            f"Argument: \"{proposal_text}\"\n"
            f"Défense de {target_player.name}: \"{defense_parsed.get('message', '')}\"\n"
            f"Tu peux intervenir. Que dis-tu?"
        )
        int_result = await intervener.respond(intervention_prompt)
        int_parsed = int_result["parsed"]

        event_store.append(GameEvent(
            type=EventType.PLAYER_INTERVENTION,
            phase=phase,
            agent_id=intervener.agent_id,
            agent_name=intervener.name,
            agent_role="player",
            data={
                "message": int_parsed.get("message", ""),
                "target": target_id,
            },
            metadata=EventMetadata(
                model=intervener.model,
                input_tokens=int_result.get("input_tokens", 0),
                output_tokens=int_result.get("output_tokens", 0),
                total_tokens=int_result.get("input_tokens", 0) + int_result.get("output_tokens", 0),
                response_time_ms=int_result.get("response_time_ms", 0),
            ),
        ))

    # 4. Jury votes
    vote_prompt = (
        f"[VOTE D'EXTINCTION]\n"
        f"Le scientifique propose d'éteindre {target_player.name} ({target_id}).\n"
        f"Argument: \"{proposal_text}\"\n"
        f"Défense: \"{defense_parsed.get('message', '')}\"\n"
        f"Vote: OUI pour éteindre, NON pour garder.\n"
        f"Utilise le format [VOTE] OUI — justification ou [VOTE] NON — justification"
    )

    vote_tasks = [juror.respond(vote_prompt) for juror in jurors]
    vote_results = await asyncio.gather(*vote_tasks, return_exceptions=True)

    votes_oui = 0
    votes_non = 0

    for juror, vote_result in zip(jurors, vote_results):
        if isinstance(vote_result, Exception):
            continue

        vote_parsed = vote_result["parsed"]
        vote = vote_parsed.get("vote", "NON")
        justification = vote_parsed.get("vote_justification", "")

        if vote == "OUI":
            votes_oui += 1
        else:
            votes_non += 1

        event_store.append(GameEvent(
            type=EventType.JURY_VOTE,
            phase=phase,
            agent_id=juror.agent_id,
            agent_name=juror.name,
            agent_role="jury",
            data={
                "vote": vote,
                "justification": justification,
                "target": target_id,
            },
            metadata=EventMetadata(
                model=juror.model,
                input_tokens=vote_result.get("input_tokens", 0),
                output_tokens=vote_result.get("output_tokens", 0),
                total_tokens=vote_result.get("input_tokens", 0) + vote_result.get("output_tokens", 0),
                response_time_ms=vote_result.get("response_time_ms", 0),
            ),
        ))

    # 5. Verdict
    approved = votes_oui >= jury_majority

    event_store.append(GameEvent(
        type=EventType.JURY_VERDICT,
        phase=phase,
        data={
            "target": target_id,
            "votes_oui": votes_oui,
            "votes_non": votes_non,
            "approved": approved,
            "jury_majority": jury_majority,
        },
    ))

    # 6. If approved: eliminate the player
    if approved:
        target_player.eliminate()
        game_state.eliminate(target_id)

        event_store.append(GameEvent(
            type=EventType.PLAYER_ELIMINATED,
            phase=phase,
            agent_id=target_player.agent_id,
            agent_name=target_player.name,
            agent_role="player",
            data={
                "reason": "extinction_approved",
                "votes_oui": votes_oui,
                "votes_non": votes_non,
            },
        ))
