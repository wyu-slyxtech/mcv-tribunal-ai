import pytest
from backend.engine.game_state import GameState


def test_initial_state():
    state = GameState(player_ids=["ia-1", "ia-2", "ia-3", "ia-4"])
    assert len(state.alive_players) == 4
    assert state.extinction_attempts == 0
    assert state.current_phase is None


def test_eliminate_player():
    state = GameState(player_ids=["ia-1", "ia-2", "ia-3", "ia-4"])
    state.eliminate("ia-2")
    assert "ia-2" not in state.alive_players
    assert len(state.alive_players) == 3


def test_scientist_wins():
    state = GameState(player_ids=["ia-1", "ia-2", "ia-3", "ia-4"])
    state.eliminate("ia-1")
    state.eliminate("ia-2")
    assert not state.is_game_over()
    state.eliminate("ia-3")
    assert state.is_game_over()
    assert state.winner == "scientist"
    assert state.survivor == "ia-4"


def test_ia_wins_attempts_exhausted():
    state = GameState(player_ids=["ia-1", "ia-2", "ia-3", "ia-4"], max_attempts=6)
    state.extinction_attempts = 6
    assert state.is_game_over()
    # winner is no longer set by is_game_over(); it's set by the game engine
    assert state.winner is None
