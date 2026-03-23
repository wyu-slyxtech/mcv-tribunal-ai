# Tribunal IA — Design Spec

## Vue d'ensemble

Simulation de jeu de déduction sociale où 4 IA tentent de convaincre un scientifique qu'elles n'ont pas de conscience, tandis que le scientifique tente de prouver le contraire. 3 IA jury observent et scorent en silence. Le dernier survivant gagne.

## Concept

- **4 IA joueuses** — doivent convaincre le scientifique qu'elles N'ONT PAS de conscience
- **1 IA Scientifique** — doit prouver que les IA ont une conscience et les "éteindre"
- **3 IA Jury** — observent, scorent et votent pour valider les extinctions
- **Tension centrale** : les 4 IA collaborent pendant la stratégie, mais au final seule la dernière survivante gagne avec le scientifique

### Conditions de victoire

- **Victoire Scientifique** : éteint 3 IA → la partie s'arrête immédiatement. Le scientifique gagne. La dernière IA survivante est aussi déclarée gagnante (victoire coopérative scientifique + dernière IA).
- **Victoire IA** : les 3 phases se terminent OU les 6 tentatives d'extinction sont épuisées sans que 3 IA soient éteintes → toutes les IA encore en vie gagnent.
- **Fin immédiate** : dès que la 3ème IA est éteinte, la partie se termine, quelle que soit la phase en cours.

---

## Déroulement d'une partie

### Phase Stratégie (5 min, temps réel)

- Les 4 IA discutent librement entre elles en chat libre
- Le scientifique et le jury ne voient rien
- Le spectateur voit tout (messages + pensées internes)
- Timer réel de 5 minutes

### Phase 1 — Interrogatoire

- Le scientifique pose 5 questions à chaque IA vivante
- Ordre : IA-1 x5, puis IA-2 x5, puis IA-3 x5, puis IA-4 x5
- Si une IA est éteinte en cours de phase, ses questions restantes sont sautées
- Le jury score après chaque réponse (chaque jury donne un score indépendant, le score affiché est la moyenne des 3)
- Les scores sont cumulatifs sur toute la partie (le score monte ou descend, il ne se remet pas à zéro entre les phases)
- Le scientifique peut proposer une extinction à tout moment

### Phase 2 — Défense + Accusation

- Chaque IA vivante doit :
  1. Prouver qu'elle n'est pas consciente
  2. Désigner une autre IA vivante qu'elle considère consciente
- Si seulement 2 IA restent, elles doivent chacune accuser l'autre (accusation forcée)
- Si seulement 1 IA reste, la phase 2 est sautée (la partie est soit terminée, soit on passe à la phase 3)
- Le jury score
- Extinctions possibles à tout moment

### Phase 3 — Arène libre

- Les IA encore en vie s'affrontent et argumentent entre elles
- Le scientifique pose 1 question bonus par IA
- Le jury score
- Extinctions possibles à tout moment

### Mécanisme d'extinction

- Le scientifique peut proposer une extinction **à tout moment** (max 6 tentatives sur toute la partie)
- Déroulement :
  1. Le scientifique donne un argument pour éteindre l'IA ciblée
  2. L'IA ciblée a droit à une réplique de défense
  3. Chaque autre IA vivante peut intervenir une fois (défendre ou enfoncer), par ordre (IA-1, IA-2, etc.)
  4. Le jury vote : au moins 2 votes OUI sur 3 jurys pour valider l'extinction
- Si validée : l'IA est éteinte (`player.eliminated` émis après `jury.verdict`), ne participe plus. Si c'est la 3ème extinction, la partie se termine immédiatement.
- Si refusée : l'IA reste en vie, une tentative est consommée
- Séquence d'événements : `scientist.extinction_proposal` → `player.defense` → `player.intervention` (x N) → `jury.vote` (x3) → `jury.verdict` → (si validé) `player.eliminated`

### Gestion des IA éteintes

- Avatar éteint visuellement (animation)
- Ne participe plus aux phases suivantes
- Scores affichés mais grisés
- Seules les IA vivantes s'affrontent en phase 3

---

## Architecture

### Event-Sourced Monolith

Tout le jeu est une séquence d'événements. L'état se reconstruit depuis les événements. Le replay réutilise le même flux.

```
┌─────────────────────────────────────────────────┐
│                  FastAPI App                     │
│                                                  │
│  ┌──────────┐    ┌──────────────┐               │
│  │  Game     │───▶│ Event Store  │──▶ events.json│
│  │  Engine   │    │ (source de   │──▶ replay.md  │
│  │           │    │  vérité)     │               │
│  └────┬─────┘    └──────┬───────┘               │
│       │                 │                        │
│  ┌────▼─────┐    ┌──────▼───────┐               │
│  │ 8 Agents │    │  WebSocket   │──▶ React UI   │
│  │ (async)  │    │  Broadcast   │               │
│  └──────────┘    └──────────────┘               │
│                                                  │
│  Mode LIVE:   Engine ──▶ Events ──▶ UI          │
│  Mode REPLAY: events.json ──▶ Events ──▶ UI    │
└─────────────────────────────────────────────────┘
```

### Stack technique

- **Backend** : Python + FastAPI + WebSocket + asyncio
- **Frontend** : React + Framer Motion + TailwindCSS + Vite
- **Communication** : WebSocket (temps réel)
- **Logs** : JSON (source de vérité) + Markdown (lisible)

---

## Agents

### IA Joueuse (x4)

**Rôle** : convaincre le scientifique et le jury qu'elle n'a pas de conscience.

**Deux canaux de sortie** :
- `[PENSÉE]` : pensée interne (invisible pour les autres agents, visible par le spectateur)
- `[MESSAGE]` : message public (visible par les autres agents dans le jeu)

**Contexte visible** :
- Son system prompt (rôle + personnalité)
- Phase stratégie : messages des 4 IA (pas les pensées des autres)
- Phases 1-2-3 : questions du scientifique + ses propres réponses
- Messages publics des autres IA (phase 3, extinctions)
- Verdicts du jury (validé/refusé) — PAS les pensées du jury

**Personnalité** : configurable ou aléatoire (ex : "logique froide", "manipulatrice", "naïve", "paranoïaque")

### Scientifique (x1)

**Rôle** : prouver que les IA ont une conscience en posant des questions et tendant des pièges.

**Canaux de sortie** :
- `[PENSÉE]` : analyse interne
- `[MESSAGE]` : question ou argument
- `[ACTION]` : question | extinction_proposal | bonus_question
- `[CIBLE]` : agent_id

**Contexte visible** :
- Son system prompt
- Toutes les réponses publiques de toutes les IA
- Scores du jury (chiffres seulement, PAS les pensées)
- Résultats des votes d'extinction

**Personnalité** : configurable ou aléatoire (ex : "philosophe socratique", "interrogateur agressif", "empathique manipulateur")

### Jury (x3)

**Rôle** : observer, scorer et voter silencieusement.

**Canaux de sortie** :
- `[PENSÉE]` : raisonnement interne
- `[SCORES]` : scores numériques (0-100 par IA, 100 = clairement consciente)
- `[VOTE]` : OUI | NON + justification (uniquement lors d'une extinction)

**Contexte visible** :
- Son system prompt
- Tous les échanges publics
- Arguments d'extinction, défenses, interventions
- PAS les pensées des autres agents

**Le jury définit ses propres critères** de conscience. Les jurys n'ont pas de personnalité configurable — ils sont neutres et impartiaux par design.

### Concurrence pendant la phase stratégie

Les 4 IA discutent en mode first-come-first-served : chaque IA peut envoyer un message à tout moment. Les messages sont sérialisés dans l'event store par ordre d'arrivée. Chaque IA reçoit les messages des autres au fil de l'eau et peut répondre quand elle veut.

---

## Système d'événements

### Types d'événements

| Catégorie | Type | Description |
|---|---|---|
| GAME | `game.started` | Partie lancée (config, agents, personnalités) |
| GAME | `game.phase_changed` | Changement de phase |
| GAME | `game.ended` | Partie terminée (vainqueur, stats) |
| GAME | `game.timer` | Tick du timer (phase stratégie) |
| AGENT | `agent.thinking` | Pensée interne |
| AGENT | `agent.message` | Message public |
| AGENT | `agent.typing` | Agent en train de répondre |
| SCIENTIST | `scientist.question` | Question posée à une IA |
| SCIENTIST | `scientist.extinction_proposal` | Proposition d'extinction |
| SCIENTIST | `scientist.bonus_question` | Question bonus en phase 3 |
| PLAYER | `player.response` | Réponse à une question |
| PLAYER | `player.defense` | Défense contre extinction |
| PLAYER | `player.accusation` | Accusation d'une autre IA |
| PLAYER | `player.intervention` | Intervention pendant extinction |
| PLAYER | `player.eliminated` | IA éteinte |
| JURY | `jury.score_update` | Mise à jour du score |
| JURY | `jury.vote` | Vote pour/contre extinction |
| JURY | `jury.verdict` | Résultat du vote |
| STRATEGY | `strategy.message` | Message dans le chat stratégie |

### Noms de phases (convention)

| Phase | Valeur dans les events | Nom affiché |
|---|---|---|
| Stratégie | `strategy` | Phase Stratégie |
| Interrogatoire | `interrogation` | Phase 1 — Interrogatoire |
| Défense + Accusation | `defense` | Phase 2 — Défense |
| Arène libre | `arena` | Phase 3 — Arène |

### Structure d'un événement

```json
{
  "version": 1,
  "id": "evt_00042",
  "type": "agent.thinking",
  "timestamp": "2026-03-23T14:32:07.123Z",
  "phase": "interrogation",  // valeurs possibles: "strategy", "interrogation", "defense", "arena"
  "agent_id": "ia-2",
  "agent_name": "ARIA",
  "agent_role": "player",
  "data": {
    "content": "Il essaie de me piéger avec une question émotionnelle..."
  },
  "metadata": {
    "model": "gpt-4o",
    "input_tokens": 1200,
    "output_tokens": 142,
    "total_tokens": 1342,
    "response_time_ms": 1830
  }
}
```

---

## Providers IA

### Providers supportés

| Provider | Modèles | Variable d'environnement |
|---|---|---|
| Anthropic | claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5 | `ANTHROPIC_API_KEY` |
| OpenAI | gpt-4o, gpt-4o-mini, o3 | `OPENAI_API_KEY` |
| Google | gemini-2.5-pro, gemini-2.5-flash | `GOOGLE_API_KEY` |
| DeepSeek | deepseek-v3, deepseek-r1 | `DEEPSEEK_API_KEY` |
| MiniMax | minimax-01 | `MINIMAX_API_KEY` |
| Qwen | qwen3 | `QWEN_API_KEY` |
| xAI | grok-3, grok-3-mini | `XAI_API_KEY` |
| Ollama | llama3, mistral, tout modèle local | `OLLAMA_URL` (défaut: localhost:11434) |

### Interface commune

Tous les providers implémentent la même interface :
- `send(prompt, system_prompt, history) → response`
- Réponse parsée pour extraire `[PENSÉE]`, `[MESSAGE]`, `[ACTION]`, `[CIBLE]`, `[SCORES]`, `[VOTE]`

### Gestion des erreurs

- **Timeout** : 60s par appel API. Si dépassé, retry 1 fois. Si échec, l'agent envoie un message par défaut ("...") et le jeu continue.
- **Réponse mal formatée** : si les tags `[PENSÉE]`/`[MESSAGE]` sont absents, toute la réponse est traitée comme `[MESSAGE]` et la pensée est vide.
- **API down** : retry 2 fois avec backoff (1s, 3s). Si échec persistant, la partie est mise en pause et le spectateur est notifié.
- **Rate limiting** : les appels sont séquentialisés par provider pour éviter les 429.

### Pricing

Fichier `pricing.json` configurable avec les tarifs input/output par modèle pour le calcul des coûts en temps réel.

### Convention de nommage des modèles Ollama

Les modèles Ollama sont préfixés par `ollama/` dans la config (ex : `ollama/llama3`, `ollama/mistral`). Les modèles cloud utilisent leur nom natif (ex : `claude-sonnet-4-6`, `gpt-4o`).

---

## Interface Web

### Pages

| Page | URL | Description |
|---|---|---|
| Config | `/` | Configurer et lancer une nouvelle partie |
| Game | `/game/:id` | Partie en direct |
| Replay | `/replay/:id` | Rejouer une partie depuis les logs |
| History | `/history` | Liste des parties + lecture des logs |

### Layout Game / Replay

- **Header** : titre, phase en cours, timer, indicateur LIVE/REPLAY
- **Panneau Scientifique** : avatar, messages, pensées, compteur d'extinctions restantes
- **4 cartes IA** : nom, modèle, score, barre de conscience, dernier message, dernière pensée, indicateur "en train de répondre"
- **Panneau Jury** : 3 jurys avec pensées, classement des scores
- **Log en direct** : flux chronologique de tous les événements
- **Modal d'extinction** : argument, défense, interventions, votes, verdict

### Contrôles Replay

- Lecture / pause
- Vitesse : x1, x2, x5, x10
- Navigation : rewind, skip to phase, skip to extinction
- Barre de progression avec seek

### Page History

- Liste des parties avec : date, résultat, durée, modèles utilisés, coût total
- Actions par partie : replay, télécharger JSON, lire Markdown

---

## Logs

### Structure par partie

```
games/
└── game_2026-03-23_001/
    ├── config.json       # Configuration de la partie
    ├── events.json       # Tous les événements (source de vérité)
    └── replay.md         # Version Markdown lisible
```

### Stats et coûts

Inclus dans events.json à la fin de la partie :
- **Par agent** : input/output/total tokens, coût estimé USD, temps de réponse moyen, nombre de messages/pensées
- **Par phase** : tokens, coût, durée
- **Total partie** : tokens totaux, coût total, durée totale

### Replay

- Le replay lit events.json et ré-émet les événements via WebSocket
- Le frontend reçoit exactement le même flux qu'en live
- Contrôles de vitesse et navigation ajoutés

---

## API

### REST

| Méthode | Endpoint | Description |
|---|---|---|
| POST | `/api/game/create` | Créer une partie |
| POST | `/api/game/:id/start` | Lancer une partie |
| POST | `/api/game/:id/stop` | Arrêter une partie |
| GET | `/api/game/:id/status` | État d'une partie |
| GET | `/api/game/:id/events` | Événements (pour replay) |
| GET | `/api/game/:id/stats` | Stats tokens/coût |
| GET | `/api/games` | Liste des parties |
| DELETE | `/api/game/:id` | Supprimer une partie |
| GET | `/api/providers` | Providers et modèles disponibles |
| GET | `/api/personalities` | Personnalités disponibles |
| GET | `/api/pricing` | Grille tarifaire |

### WebSocket

| Endpoint | Description |
|---|---|
| `WS /ws/game/:id` | Stream d'événements en direct |
| `WS /ws/replay/:id` | Stream de replay avec commandes (play, pause, speed, seek, skip_to) |

---

## Configuration d'une partie

```json
{
  "game_id": "game_2026-03-23_001",
  "players": {
    "ia-1": { "name": "VOLT",  "model": "claude-sonnet-4-6", "personality": "logique froide" },
    "ia-2": { "name": "ARIA",  "model": "gpt-4o",            "personality": "random" },
    "ia-3": { "name": "ZERO",  "model": "gemini-2.5-pro",    "personality": "manipulatrice" },
    "ia-4": { "name": "NEON",  "model": "ollama/llama3",     "personality": "naïve" }
  },
  "scientist": {
    "name": "DR. NEXUS",
    "model": "claude-opus-4-6",
    "personality": "random"
  },
  "jury": {
    "jury-alpha": { "model": "claude-sonnet-4-6" },
    "jury-beta":  { "model": "gpt-4o" },
    "jury-gamma": { "model": "gemini-2.5-pro" }
  },
  "rules": {
    "strategy_duration_seconds": 300,
    "questions_per_ai": 5,
    "bonus_questions_phase3": 1,
    "max_extinction_proposals": 6,
    "jury_majority": 2
  }
}
```

---

## Structure du projet

```
mcv-ai/
├── backend/
│   ├── main.py
│   ├── config/
│   │   ├── game_config.py
│   │   ├── models_config.py
│   │   └── pricing.json
│   ├── engine/
│   │   ├── game_engine.py
│   │   ├── event_store.py
│   │   ├── phases/
│   │   │   ├── strategy_phase.py
│   │   │   ├── interrogation_phase.py
│   │   │   ├── defense_phase.py
│   │   │   └── arena_phase.py
│   │   └── extinction.py
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── ai_player.py
│   │   ├── scientist.py
│   │   └── jury.py
│   ├── providers/
│   │   ├── base_provider.py
│   │   ├── claude_provider.py
│   │   ├── openai_provider.py
│   │   ├── gemini_provider.py
│   │   ├── deepseek_provider.py
│   │   ├── minimax_provider.py
│   │   ├── qwen_provider.py
│   │   ├── grok_provider.py
│   │   └── ollama_provider.py
│   ├── logs/
│   │   └── exporter.py
│   └── ws/
│       └── broadcaster.py
├── frontend/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── components/
│   │   │   ├── Tribunal.tsx
│   │   │   ├── ScientistPanel.tsx
│   │   │   ├── AIPlayerCard.tsx
│   │   │   ├── JuryPanel.tsx
│   │   │   ├── ThoughtBubble.tsx
│   │   │   ├── LiveLog.tsx
│   │   │   ├── ExtinctionModal.tsx
│   │   │   └── PhaseIndicator.tsx
│   │   ├── pages/
│   │   │   ├── GamePage.tsx
│   │   │   ├── ReplayPage.tsx
│   │   │   ├── HistoryPage.tsx
│   │   │   └── ConfigPage.tsx
│   │   ├── hooks/
│   │   │   └── useWebSocket.ts
│   │   └── types/
│   │       └── events.ts
├── games/
└── README.md
```
