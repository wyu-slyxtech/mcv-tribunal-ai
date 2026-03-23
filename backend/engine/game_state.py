from backend.engine.events import Phase


class GameState:
    def __init__(self, player_ids: list[str], max_attempts: int = 6):
        self.alive_players: list[str] = list(player_ids)
        self.eliminated_players: list[str] = []
        self.extinction_attempts: int = 0
        self.max_attempts: int = max_attempts
        self.current_phase: Phase | None = None
        self.scores: dict[str, dict[str, int]] = {}
        self.winner: str | None = None
        self.survivor: str | None = None

    def eliminate(self, player_id: str):
        if player_id in self.alive_players:
            self.alive_players.remove(player_id)
            self.eliminated_players.append(player_id)
            if len(self.eliminated_players) >= 3:
                self.winner = "scientist"
                self.survivor = self.alive_players[0] if self.alive_players else None

    def is_game_over(self) -> bool:
        if len(self.eliminated_players) >= 3:
            return True
        if self.extinction_attempts >= self.max_attempts:
            return True
        return False

    def get_average_score(self, player_id: str) -> float:
        if not self.scores:
            return 0.0
        total = sum(jury_scores.get(player_id, 0) for jury_scores in self.scores.values())
        return total / len(self.scores) if self.scores else 0.0
