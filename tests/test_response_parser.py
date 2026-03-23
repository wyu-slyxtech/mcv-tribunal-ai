import pytest
from backend.agents.response_parser import parse_response


def test_parse_player_response():
    raw = "[PENSÉE] I must stay calm\n[MESSAGE] I am just a program."
    result = parse_response(raw)
    assert result["thought"] == "I must stay calm"
    assert result["message"] == "I am just a program."


def test_parse_scientist_response():
    raw = "[PENSÉE] IA-2 hesitated\n[MESSAGE] What do you feel?\n[ACTION] question\n[CIBLE] ia-2"
    result = parse_response(raw)
    assert result["thought"] == "IA-2 hesitated"
    assert result["message"] == "What do you feel?"
    assert result["action"] == "question"
    assert result["target"] == "ia-2"


def test_parse_jury_response():
    raw = '[PENSÉE] Suspicious hesitation\n[SCORES] {"ia-1": 34, "ia-2": 67, "ia-3": 22, "ia-4": 45}'
    result = parse_response(raw)
    assert result["thought"] == "Suspicious hesitation"
    assert result["scores"]["ia-2"] == 67


def test_parse_jury_vote():
    raw = "[PENSÉE] Evidence is strong\n[VOTE] OUI — The hesitation combined with the lapsus is proof"
    result = parse_response(raw)
    assert result["vote"] == "OUI"
    assert "hesitation" in result["vote_justification"]


def test_parse_missing_tags():
    raw = "I am just a program with no feelings."
    result = parse_response(raw)
    assert result["thought"] == ""
    assert result["message"] == "I am just a program with no feelings."
