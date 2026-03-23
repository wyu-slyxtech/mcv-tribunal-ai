import pytest
from backend.config.game_config import GameConfig, AgentConfig, RulesConfig


def test_game_config_creation():
    config = GameConfig(
        players={
            "ia-1": AgentConfig(name="VOLT", model="claude-sonnet-4-6", personality="logique froide"),
            "ia-2": AgentConfig(name="ARIA", model="gpt-4o", personality="random"),
            "ia-3": AgentConfig(name="ZERO", model="gemini-2.5-pro"),
            "ia-4": AgentConfig(name="NEON", model="ollama/llama3"),
        },
        scientist=AgentConfig(name="DR. NEXUS", model="claude-opus-4-6", personality="philosophe socratique"),
        jury={
            "jury-alpha": AgentConfig(name="Alpha", model="claude-sonnet-4-6"),
            "jury-beta": AgentConfig(name="Beta", model="gpt-4o"),
            "jury-gamma": AgentConfig(name="Gamma", model="gemini-2.5-pro"),
        },
    )
    assert config.game_id.startswith("game_")
    assert len(config.players) == 4
    assert config.rules.max_extinction_proposals == 6
    assert config.rules.jury_majority == 2


def test_default_rules():
    rules = RulesConfig()
    assert rules.strategy_duration_seconds == 300
    assert rules.questions_per_ai == 5
    assert rules.bonus_questions_phase3 == 1
