import pytest
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


def test_ai_player_creation():
    agent = AIPlayerAgent(
        agent_id="ia-1", name="VOLT", model="claude-sonnet-4-6", personality="logique froide",
    )
    assert agent.agent_id == "ia-1"
    assert agent.role == "player"
    assert "conscience" in agent.system_prompt.lower()


def test_scientist_creation():
    agent = ScientistAgent(
        agent_id="scientist", name="DR. NEXUS", model="claude-opus-4-6", personality="philosophe socratique",
    )
    assert agent.role == "scientist"
    assert "prouver" in agent.system_prompt.lower()


def test_jury_creation():
    agent = JuryAgent(agent_id="jury-alpha", name="Alpha", model="claude-sonnet-4-6")
    assert agent.role == "jury"
    assert "score" in agent.system_prompt.lower() or "scorer" in agent.system_prompt.lower()


def test_agent_eliminate():
    agent = AIPlayerAgent(agent_id="ia-1", name="VOLT", model="claude-sonnet-4-6", personality="logique froide")
    assert agent.alive is True
    agent.eliminate()
    assert agent.alive is False


def test_agent_add_context():
    agent = AIPlayerAgent(agent_id="ia-1", name="VOLT", model="claude-sonnet-4-6", personality="logique froide")
    agent.add_context("user", "test message")
    assert len(agent.history) == 1
    assert agent.history[0]["content"] == "test message"
