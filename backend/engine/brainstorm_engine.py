import time
from backend.engine.events import GameEvent, EventType
from backend.engine.event_store import EventStore
from backend.config.game_config import BrainstormConfig
from backend.config.personalities import resolve_personality
from backend.agents.brainstorm_agent import BrainstormAgent
from backend.engine.phases.brainstorm_phase import (
    run_brainstorm_debate,
    run_brainstorm_vote,
)


class BrainstormEngine:
    def __init__(self, config: BrainstormConfig):
        self.config = config
        self.event_store = EventStore(game_id=config.game_id)
        self.running = False

        # Init brainstorm agents
        self.players: list[BrainstormAgent] = []
        for pid in sorted(config.players.keys()):
            pcfg = config.players[pid]
            personality = resolve_personality(pcfg.personality, "player")
            agent = BrainstormAgent(
                agent_id=pid,
                name=pcfg.name,
                model=pcfg.model,
                personality=personality,
            )
            self.players.append(agent)

    async def run(self):
        """Execute brainstorming session: debate + vote loops until consensus or limit."""
        self.running = True
        start_time = time.time()

        self.event_store.append(GameEvent(
            type=EventType.GAME_STARTED,
            data={
                "config": self.config.model_dump(mode="json"),
            },
        ))

        is_running = lambda: self.running
        rules = self.config.rules
        consensus_reached = False
        final_answer = None
        final_round = 0

        for round_num in range(1, rules.max_rounds + 1):
            if not self.running:
                break

            final_round = round_num

            # Debate phase
            messages_history = await run_brainstorm_debate(
                players=self.players,
                event_store=self.event_store,
                topic=self.config.topic,
                round_num=round_num,
                duration_seconds=rules.debate_round_seconds,
                sub_rounds=rules.sub_rounds_per_debate,
                is_running=is_running,
            )

            if not self.running:
                break

            # Vote phase
            vote_result = await run_brainstorm_vote(
                players=self.players,
                event_store=self.event_store,
                topic=self.config.topic,
                round_num=round_num,
                messages_history=messages_history,
                consensus_threshold=rules.consensus_threshold,
                is_running=is_running,
            )

            if vote_result["consensus"]:
                consensus_reached = True
                final_answer = vote_result["proposed_answer"]
                break

        # Emit game ended
        elapsed_seconds = int(time.time() - start_time)

        self.event_store.append(GameEvent(
            type=EventType.GAME_ENDED,
            data={
                "result": "consensus" if consensus_reached else "no_consensus",
                "final_answer": final_answer,
                "rounds_played": final_round,
                "max_rounds": rules.max_rounds,
                "duration_seconds": elapsed_seconds,
            },
        ))

        # Save to disk
        result = {
            "result": "consensus" if consensus_reached else "no_consensus",
            "final_answer": final_answer,
            "rounds_played": final_round,
        }

        try:
            from backend.logs.exporter import compute_stats
            stats = compute_stats(self.event_store, self.config)
            await self.event_store.save_to_disk(
                config=self.config.model_dump(mode="json"),
                stats=stats,
                result=result,
            )
        except Exception:
            try:
                await self.event_store.save_to_disk(
                    config=self.config.model_dump(mode="json"),
                    result=result,
                )
            except Exception:
                pass
        finally:
            self.running = False

    def stop(self):
        """Stop the brainstorm engine."""
        self.running = False
