from backend.config.game_config import BrainstormConfig, BrainstormRulesConfig, AgentConfig
from backend.agents.brainstorm_agent import BrainstormAgent
from backend.agents.response_parser import parse_response
from backend.engine.events import EventType, Phase


def test_brainstorm_config_creation():
    config = BrainstormConfig(
        topic="Comment améliorer l'éducation ?",
        players={
            "ia-1": AgentConfig(name="ALPHA", model="gpt-4o"),
            "ia-2": AgentConfig(name="BETA", model="gpt-4o"),
            "ia-3": AgentConfig(name="GAMMA", model="gpt-4o"),
            "ia-4": AgentConfig(name="DELTA", model="gpt-4o"),
        },
    )
    assert config.mode == "brainstorm"
    assert config.topic == "Comment améliorer l'éducation ?"
    assert len(config.players) == 4
    assert config.game_id.startswith("brainstorm_")


def test_brainstorm_rules_defaults():
    rules = BrainstormRulesConfig()
    assert rules.debate_round_seconds == 180
    assert rules.max_rounds == 5
    assert rules.consensus_threshold == 3
    assert rules.sub_rounds_per_debate == 3


def test_brainstorm_agent_creation():
    agent = BrainstormAgent(
        agent_id="ia-1",
        name="ALPHA",
        model="gpt-4o",
        personality="analytique",
    )
    assert agent.name == "ALPHA"
    assert agent.role == "brainstormer"
    assert agent.personality == "analytique"
    assert "brainstorming" in agent.system_prompt.lower()


def test_parse_brainstorm_vote_pour():
    raw = """[PENSÉE] Je pense que nous avons trouvé un bon consensus.
[VOTE] POUR — la réponse couvre tous les aspects importants
[REPONSE] L'éducation devrait intégrer plus de pratique et de projets concrets."""
    result = parse_response(raw)
    assert result["vote"] == "POUR"
    assert result["proposed_answer"] == "L'éducation devrait intégrer plus de pratique et de projets concrets."
    assert "aspects importants" in result["vote_justification"]


def test_parse_brainstorm_vote_contre():
    raw = """[PENSÉE] On n'a pas assez exploré le sujet.
[VOTE] CONTRE — il manque la dimension technologique"""
    result = parse_response(raw)
    assert result["vote"] == "CONTRE"
    assert result["proposed_answer"] is None
    assert "technologique" in result["vote_justification"]


def test_brainstorm_event_types_exist():
    assert EventType.BRAINSTORM_MESSAGE == "brainstorm.message"
    assert EventType.BRAINSTORM_VOTE == "brainstorm.vote"
    assert EventType.BRAINSTORM_CONSENSUS == "brainstorm.consensus"
    assert EventType.BRAINSTORM_NO_CONSENSUS == "brainstorm.no_consensus"


def test_brainstorm_phases_exist():
    assert Phase.BRAINSTORM_DEBATE == "brainstorm_debate"
    assert Phase.BRAINSTORM_VOTE == "brainstorm_vote"


def test_game_config_has_mode():
    from backend.config.game_config import GameConfig
    config = GameConfig(
        players={"ia-1": AgentConfig(name="V", model="gpt-4o")},
        scientist=AgentConfig(name="S", model="gpt-4o"),
        jury={"j-1": AgentConfig(name="J", model="gpt-4o")},
    )
    assert config.mode == "tribunal"
