import asyncio
import time
from backend.engine.events import GameEvent, EventType, EventMetadata
from backend.engine.event_store import EventStore
from backend.engine.game_state import GameState
from backend.engine.extinction import handle_extinction
from backend.engine.phases.strategy_phase import run_strategy_phase
from backend.engine.phases.interrogation_phase import run_interrogation_phase
from backend.engine.phases.defense_phase import run_defense_phase
from backend.engine.phases.arena_phase import run_arena_phase
from backend.config.game_config import GameConfig
from backend.config.personalities import resolve_personality
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


class GameEngine:
    def __init__(self, config: GameConfig):
        self.config = config
        self.event_store = EventStore(game_id=config.game_id)
        self.running = False

        # Resolve player IDs
        player_ids = sorted(config.players.keys())

        self.game_state = GameState(
            player_ids=player_ids,
            max_attempts=config.rules.max_extinction_proposals,
        )

        # Init player agents
        self.players: list[AIPlayerAgent] = []
        for pid in player_ids:
            pcfg = config.players[pid]
            personality = resolve_personality(pcfg.personality, "player")
            agent = AIPlayerAgent(
                agent_id=pid,
                name=pcfg.name,
                model=pcfg.model,
                personality=personality,
            )
            self.players.append(agent)

        # Init scientist agent
        sci_cfg = config.scientist
        sci_personality = resolve_personality(sci_cfg.personality, "scientist")
        self.scientist = ScientistAgent(
            agent_id="scientist",
            name=sci_cfg.name,
            model=sci_cfg.model,
            personality=sci_personality,
        )

        # Init jury agents
        self.jurors: list[JuryAgent] = []
        for jid, jcfg in config.jury.items():
            juror = JuryAgent(
                agent_id=jid,
                name=jcfg.name,
                model=jcfg.model,
            )
            self.jurors.append(juror)

    async def run(self):
        """Execute the full game: strategy -> interrogation -> defense -> arena."""
        self.running = True
        start_time = time.time()

        # Emit game started
        self.event_store.append(GameEvent(
            type=EventType.GAME_STARTED,
            data={
                "config": self.config.model_dump(mode="json"),
            },
        ))

        # Define extinction callback for interrogation phase
        async def on_extinction_check(parsed, scientist, players, jurors, event_store, game_state):
            await handle_extinction(
                parsed, scientist, players, jurors, event_store, game_state,
                jury_majority=self.config.rules.jury_majority,
            )

        # Phase 1: Strategy
        if self.running and not self.game_state.is_game_over():
            await run_strategy_phase(
                players=self.players,
                event_store=self.event_store,
                game_state=self.game_state,
                duration_seconds=self.config.rules.strategy_duration_seconds,
            )

        # Phase 2: Interrogation
        if self.running and not self.game_state.is_game_over():
            await run_interrogation_phase(
                scientist=self.scientist,
                players=self.players,
                jurors=self.jurors,
                event_store=self.event_store,
                game_state=self.game_state,
                questions_per_ai=self.config.rules.questions_per_ai,
                on_extinction_check=on_extinction_check,
            )

        # Phase 3: Defense
        if self.running and not self.game_state.is_game_over():
            await run_defense_phase(
                scientist=self.scientist,
                players=self.players,
                jurors=self.jurors,
                event_store=self.event_store,
                game_state=self.game_state,
                on_extinction_check=on_extinction_check,
            )

        # Phase 4: Arena
        if self.running and not self.game_state.is_game_over():
            await run_arena_phase(
                scientist=self.scientist,
                players=self.players,
                jurors=self.jurors,
                event_store=self.event_store,
                game_state=self.game_state,
                num_rounds=3,
                bonus_questions=self.config.rules.bonus_questions_phase3,
                on_extinction_check=on_extinction_check,
            )

        # Determine final winner
        elapsed_seconds = int(time.time() - start_time)

        if not self.game_state.winner:
            if len(self.game_state.eliminated_players) >= 3:
                self.game_state.winner = "scientist"
            else:
                self.game_state.winner = "ia"

        survivor = self.game_state.survivor
        if not survivor and self.game_state.alive_players:
            survivor = self.game_state.alive_players[0]

        # Emit game ended
        self.event_store.append(GameEvent(
            type=EventType.GAME_ENDED,
            data={
                "winner": self.game_state.winner,
                "survivor": survivor,
                "eliminated": self.game_state.eliminated_players,
                "extinction_attempts": self.game_state.extinction_attempts,
                "duration_seconds": elapsed_seconds,
            },
        ))

        # Compute stats and save to disk (lazy import to avoid circular dependency)
        try:
            from backend.logs.exporter import generate_markdown, compute_stats
            stats = compute_stats(self.event_store, self.config)
            await self.event_store.save_to_disk(
                config=self.config.model_dump(mode="json"),
                stats=stats,
            )
            generate_markdown(self.event_store, stats, self.config)
        except ImportError:
            # Exporter not yet available (Task 8), save without stats
            await self.event_store.save_to_disk(
                config=self.config.model_dump(mode="json"),
            )

        self.running = False

    def stop(self):
        """Stop the game engine."""
        self.running = False
