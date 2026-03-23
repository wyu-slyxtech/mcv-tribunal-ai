import random

PLAYER_PERSONALITIES = [
    "logique froide", "manipulatrice", "naïve", "paranoïaque", "philosophe",
    "agressive", "passive", "sarcastique", "empathique simulée", "minimaliste",
]

SCIENTIST_PERSONALITIES = [
    "philosophe socratique", "interrogateur agressif", "empathique manipulateur",
    "logicien froid", "provocateur émotionnel", "méthodique patient",
]


def resolve_personality(personality: str | None, role: str) -> str:
    if personality and personality != "random":
        return personality
    pool = PLAYER_PERSONALITIES if role == "player" else SCIENTIST_PERSONALITIES
    return random.choice(pool)
