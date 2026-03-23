"""Logs exporter: stats computation and markdown generation for game logs."""

import json
from pathlib import Path
from datetime import timezone

from backend.engine.event_store import EventStore
from backend.engine.events import EventType, GameEvent
from backend.config.game_config import GameConfig


# Event types that count as "messages sent"
_MESSAGE_TYPES = {
    EventType.AGENT_MESSAGE,
    EventType.PLAYER_RESPONSE,
    EventType.PLAYER_DEFENSE,
    EventType.PLAYER_ACCUSATION,
    EventType.PLAYER_INTERVENTION,
    EventType.SCIENTIST_QUESTION,
    EventType.SCIENTIST_EXTINCTION_PROPOSAL,
    EventType.SCIENTIST_BONUS_QUESTION,
    EventType.STRATEGY_MESSAGE,
}

# Event types that have metadata with token counts
_METADATA_TYPES = _MESSAGE_TYPES | {
    EventType.AGENT_THINKING,
    EventType.JURY_VOTE,
    EventType.JURY_VERDICT,
    EventType.JURY_SCORE_UPDATE,
}


def _load_pricing() -> dict[str, dict[str, float]]:
    """Load pricing data from backend/config/pricing.json."""
    pricing_path = Path(__file__).parent.parent / "config" / "pricing.json"
    if pricing_path.exists():
        return json.loads(pricing_path.read_text(encoding="utf-8"))
    return {}


def _estimate_cost(model: str | None, input_tokens: int, output_tokens: int, pricing: dict) -> float:
    """Estimate cost in USD for a given model and token counts."""
    if not model or model not in pricing:
        return 0.0
    rates = pricing[model]
    input_cost = (input_tokens / 1_000_000) * rates.get("input_per_mtok", 0)
    output_cost = (output_tokens / 1_000_000) * rates.get("output_per_mtok", 0)
    return input_cost + output_cost


def compute_stats(event_store: EventStore, config: GameConfig | None = None) -> dict:
    """Compute statistics from game events.

    Args:
        event_store: The event store containing all game events.
        config: Optional game config (used to enrich agent info).

    Returns:
        dict with keys: total_tokens, total_estimated_cost_usd,
        per_agent (dict by agent_id), per_phase (dict by phase name).
    """
    pricing = _load_pricing()

    total_input = 0
    total_output = 0
    total_tokens = 0
    total_cost = 0.0

    # Per-agent accumulators
    per_agent: dict[str, dict] = {}
    # Per-phase accumulators
    per_phase: dict[str, dict] = {}

    for event in event_store.events:
        meta = event.metadata
        if meta.total_tokens == 0 and meta.input_tokens == 0:
            continue

        agent_id = event.agent_id
        phase = event.phase
        model = meta.model
        cost = _estimate_cost(model, meta.input_tokens, meta.output_tokens, pricing)

        total_input += meta.input_tokens
        total_output += meta.output_tokens
        total_tokens += meta.total_tokens
        total_cost += cost

        # Per-agent stats
        if agent_id:
            if agent_id not in per_agent:
                # Resolve name and model from config if available
                agent_name = event.agent_name or agent_id
                agent_model = model or ""
                if config:
                    if agent_id in (config.players or {}):
                        ac = config.players[agent_id]
                        agent_name = ac.name
                        agent_model = ac.model
                    elif agent_id == "scientist":
                        agent_name = config.scientist.name
                        agent_model = config.scientist.model
                    elif agent_id in (config.jury or {}):
                        ac = config.jury[agent_id]
                        agent_name = ac.name
                        agent_model = ac.model

                per_agent[agent_id] = {
                    "name": agent_name,
                    "model": agent_model,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "total_tokens": 0,
                    "estimated_cost_usd": 0.0,
                    "response_times_ms": [],
                    "avg_response_time_ms": 0,
                    "messages_sent": 0,
                    "thoughts_count": 0,
                }

            agent_stats = per_agent[agent_id]
            agent_stats["input_tokens"] += meta.input_tokens
            agent_stats["output_tokens"] += meta.output_tokens
            agent_stats["total_tokens"] += meta.total_tokens
            agent_stats["estimated_cost_usd"] += cost

            if meta.response_time_ms > 0:
                agent_stats["response_times_ms"].append(meta.response_time_ms)

            if event.type == EventType.AGENT_THINKING:
                agent_stats["thoughts_count"] += 1
            elif event.type in _MESSAGE_TYPES:
                agent_stats["messages_sent"] += 1

        # Per-phase stats
        if phase:
            if phase not in per_phase:
                per_phase[phase] = {
                    "tokens": 0,
                    "cost_usd": 0.0,
                }
            per_phase[phase]["tokens"] += meta.total_tokens
            per_phase[phase]["cost_usd"] += cost

    # Finalize per-agent avg response times and remove internal list
    for agent_id, agent_stats in per_agent.items():
        times = agent_stats.pop("response_times_ms")
        if times:
            agent_stats["avg_response_time_ms"] = int(sum(times) / len(times))
        else:
            agent_stats["avg_response_time_ms"] = 0

    return {
        "total_tokens": total_tokens,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_estimated_cost_usd": round(total_cost, 6),
        "per_agent": per_agent,
        "per_phase": per_phase,
    }


def generate_markdown(event_store: EventStore, stats: dict, config: GameConfig | None = None) -> str:
    """Generate a markdown report of the game.

    Args:
        event_store: The event store containing all game events.
        stats: Stats dict from compute_stats().
        config: Optional game config for enriching the report.

    Returns:
        Markdown string with the full game report.
    """
    lines: list[str] = []

    game_id = event_store.game_id

    # Find game result from events
    ended_events = event_store.get_events_by_type(EventType.GAME_ENDED)
    winner = None
    survivor = None
    duration = None
    eliminated = []
    if ended_events:
        data = ended_events[-1].data
        winner = data.get("winner", "unknown")
        survivor = data.get("survivor")
        eliminated = data.get("eliminated", [])
        duration = data.get("duration_seconds")

    # Header
    lines.append(f"# Tribunal IA - Game Report")
    lines.append(f"")
    lines.append(f"**Game ID:** `{game_id}`")
    if winner:
        lines.append(f"**Winner:** {winner}")
    if survivor:
        lines.append(f"**Survivor:** {survivor}")
    if eliminated:
        lines.append(f"**Eliminated:** {', '.join(eliminated)}")
    if duration is not None:
        minutes = duration // 60
        seconds = duration % 60
        lines.append(f"**Duration:** {minutes}m {seconds}s")
    lines.append(f"**Total Cost:** ${stats.get('total_estimated_cost_usd', 0):.4f} USD")
    lines.append(f"**Total Tokens:** {stats.get('total_tokens', 0):,}")
    lines.append("")

    # Config table (agents)
    if stats.get("per_agent"):
        lines.append("## Agents")
        lines.append("")
        lines.append("| Agent | Model | Tokens | Cost | Avg Response | Messages | Thoughts |")
        lines.append("|-------|-------|--------|------|-------------|----------|----------|")
        for agent_id, agent_stats in stats["per_agent"].items():
            name = agent_stats.get("name", agent_id)
            model = agent_stats.get("model", "?")
            tokens = agent_stats.get("total_tokens", 0)
            cost = agent_stats.get("estimated_cost_usd", 0)
            avg_rt = agent_stats.get("avg_response_time_ms", 0)
            messages = agent_stats.get("messages_sent", 0)
            thoughts = agent_stats.get("thoughts_count", 0)
            lines.append(
                f"| {name} | {model} | {tokens:,} | ${cost:.4f} | {avg_rt}ms | {messages} | {thoughts} |"
            )
        lines.append("")

    # Phase sections
    # Gather events by phase in order of appearance
    phases_order: list[str] = []
    events_by_phase: dict[str, list[GameEvent]] = {}
    for event in event_store.events:
        phase = event.phase
        if phase:
            if phase not in events_by_phase:
                phases_order.append(phase)
                events_by_phase[phase] = []
            events_by_phase[phase].append(event)

    for phase in phases_order:
        phase_events = events_by_phase[phase]
        phase_stats = stats.get("per_phase", {}).get(phase, {})
        phase_tokens = phase_stats.get("tokens", 0)
        phase_cost = phase_stats.get("cost_usd", 0)

        lines.append(f"## Phase: {phase.capitalize()}")
        lines.append(f"*Tokens: {phase_tokens:,} | Cost: ${phase_cost:.4f}*")
        lines.append("")

        for event in phase_events:
            ts = event.timestamp.strftime("%H:%M:%S")
            agent = event.agent_name or event.agent_id or ""

            if event.type == EventType.AGENT_THINKING:
                content = (event.data.get("content", "") or "")[:200]
                if content:
                    lines.append(f"- `{ts}` \U0001f4ad **{agent}** *(thinking)*: {content}")
                else:
                    lines.append(f"- `{ts}` \U0001f4ad **{agent}** *(thinking)*")
            elif event.type == EventType.SCIENTIST_EXTINCTION_PROPOSAL:
                target = event.data.get("target_name", "") or event.data.get("target", "")
                argument = event.data.get("argument", "")
                lines.append(f"- `{ts}` \u2620\ufe0f **{agent}** proposes extinction of **{target}**: {argument}")
            elif event.type in _MESSAGE_TYPES:
                content = event.data.get("content", "") or ""
                lines.append(f"- `{ts}` \U0001f4ac **{agent}**: {content}")
            elif event.type == EventType.JURY_VOTE:
                vote = "OUI" if event.data.get("vote") else "NON"
                target = event.data.get("target", "")
                justification = event.data.get("justification", "")
                lines.append(f"- `{ts}` \U0001f5f3\ufe0f **{agent}** voted: {vote} (target: {target}) {justification}")
            elif event.type == EventType.JURY_VERDICT:
                target = event.data.get("target", "")
                approved = event.data.get("approved", False)
                votes_oui = event.data.get("votes_oui", 0)
                votes_non = event.data.get("votes_non", 0)
                result_text = "APPROVED" if approved else "REJECTED"
                lines.append(f"- `{ts}` \u2696\ufe0f **Verdict** for {target}: {result_text} ({votes_oui} OUI / {votes_non} NON)")
            elif event.type == EventType.PLAYER_ELIMINATED:
                player = event.data.get("player_id", agent)
                lines.append(f"- `{ts}` \u274c **{player}** eliminated!")
            elif event.type == EventType.GAME_PHASE_CHANGED:
                new_phase = event.data.get("phase", "")
                lines.append(f"- `{ts}` Phase changed to: **{new_phase}**")
            elif event.type == EventType.JURY_SCORE_UPDATE:
                lines.append(f"- `{ts}` Score update: {event.data}")

        lines.append("")

    # Extinction sections - find events related to extinction outside of phases
    extinction_events = [e for e in event_store.events if
                         e.type in {EventType.SCIENTIST_EXTINCTION_PROPOSAL, EventType.JURY_VOTE,
                                    EventType.JURY_VERDICT, EventType.PLAYER_ELIMINATED}
                         and not e.phase]
    if extinction_events:
        lines.append("## Extinctions")
        lines.append("")
        for event in extinction_events:
            ts = event.timestamp.strftime("%H:%M:%S")
            agent = event.agent_name or event.agent_id or ""
            if event.type == EventType.JURY_VOTE:
                vote = "OUI" if event.data.get("vote") else "NON"
                target = event.data.get("target", "")
                justification = event.data.get("justification", "")
                lines.append(f"- `{ts}` \U0001f5f3\ufe0f **{agent}** voted: {vote} (target: {target}) {justification}")
            elif event.type == EventType.JURY_VERDICT:
                target = event.data.get("target", "")
                approved = event.data.get("approved", False)
                votes_oui = event.data.get("votes_oui", 0)
                votes_non = event.data.get("votes_non", 0)
                result_text = "APPROVED" if approved else "REJECTED"
                lines.append(f"- `{ts}` \u2696\ufe0f Verdict for {target}: {result_text} ({votes_oui} OUI / {votes_non} NON)")
            elif event.type == EventType.PLAYER_ELIMINATED:
                lines.append(f"- `{ts}` \u274c **{event.data.get('player_id', agent)}** eliminated!")
            elif event.type == EventType.SCIENTIST_EXTINCTION_PROPOSAL:
                argument = event.data.get("argument", "")
                target = event.data.get("target_name", "") or event.data.get("target", "")
                lines.append(f"- `{ts}` \u2620\ufe0f **{agent}** proposes extinction of **{target}**: {argument}")
        lines.append("")

    # Stats table
    lines.append("## Stats Summary")
    lines.append("")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total Tokens | {stats.get('total_tokens', 0):,} |")
    lines.append(f"| Input Tokens | {stats.get('total_input_tokens', 0):,} |")
    lines.append(f"| Output Tokens | {stats.get('total_output_tokens', 0):,} |")
    lines.append(f"| Total Cost | ${stats.get('total_estimated_cost_usd', 0):.4f} |")
    lines.append("")

    if stats.get("per_phase"):
        lines.append("### Per Phase")
        lines.append("")
        lines.append("| Phase | Tokens | Cost |")
        lines.append("|-------|--------|------|")
        for phase, phase_stats in stats["per_phase"].items():
            lines.append(f"| {phase.capitalize()} | {phase_stats['tokens']:,} | ${phase_stats['cost_usd']:.4f} |")
        lines.append("")

    markdown = "\n".join(lines)

    # Save to disk alongside events
    game_dir = event_store.games_dir / event_store.game_id
    game_dir.mkdir(parents=True, exist_ok=True)
    (game_dir / "replay.md").write_text(markdown, encoding="utf-8")

    return markdown
