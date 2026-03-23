import pytest
from backend.engine.game_state import GameState


def test_extinction_attempts_limit():
    state = GameState(player_ids=["ia-1", "ia-2", "ia-3", "ia-4"], max_attempts=6)
    for i in range(6):
        state.extinction_attempts += 1
    assert state.is_game_over()
    # winner is no longer set by is_game_over(); it's set by the game engine
    assert state.winner is None


def test_three_eliminations_ends_game():
    state = GameState(player_ids=["ia-1", "ia-2", "ia-3", "ia-4"])
    state.eliminate("ia-1")
    state.eliminate("ia-2")
    assert not state.is_game_over()
    state.eliminate("ia-3")
    assert state.is_game_over()
    assert state.winner == "scientist"
    assert state.survivor == "ia-4"


def test_no_double_elimination():
    state = GameState(player_ids=["ia-1", "ia-2", "ia-3", "ia-4"])
    state.eliminate("ia-1")
    state.eliminate("ia-1")
    assert len(state.eliminated_players) == 1
