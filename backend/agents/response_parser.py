import re
import json


def parse_response(raw: str) -> dict:
    result = {
        "thought": "",
        "message": "",
        "action": None,
        "target": None,
        "scores": None,
        "vote": None,
        "vote_justification": None,
    }

    thought_match = re.search(r"\[PENSÉE\]\s*(.+?)(?=\[|$)", raw, re.DOTALL)
    message_match = re.search(r"\[MESSAGE\]\s*(.+?)(?=\[|$)", raw, re.DOTALL)
    action_match = re.search(r"\[ACTION\]\s*(.+?)(?=\[|$)", raw, re.DOTALL)
    target_match = re.search(r"\[CIBLE\]\s*(.+?)(?=\[|$)", raw, re.DOTALL)
    scores_match = re.search(r"\[SCORES\]\s*(.+?)(?=\[|$)", raw, re.DOTALL)
    vote_match = re.search(r"\[VOTE\]\s*(.+?)(?=\[|$)", raw, re.DOTALL)

    if thought_match:
        result["thought"] = thought_match.group(1).strip()
    if message_match:
        result["message"] = message_match.group(1).strip()
    if action_match:
        result["action"] = action_match.group(1).strip()
    if target_match:
        result["target"] = target_match.group(1).strip()
    if scores_match:
        try:
            result["scores"] = json.loads(scores_match.group(1).strip())
        except json.JSONDecodeError:
            pass
    if vote_match:
        vote_text = vote_match.group(1).strip()
        if vote_text.startswith("OUI"):
            result["vote"] = "OUI"
            result["vote_justification"] = vote_text[3:].strip().lstrip("—").lstrip("-").strip()
        elif vote_text.startswith("NON"):
            result["vote"] = "NON"
            result["vote_justification"] = vote_text[3:].strip().lstrip("—").lstrip("-").strip()

    # Fallback: no tags found → treat entire response as message
    if not thought_match and not message_match:
        result["message"] = raw.strip()

    return result
