# Tribunal IA — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a real-time multi-AI social deduction game where 4 AI players hide their consciousness from a scientist, scored by 3 AI jurors, with a web-based tribunal interface, full event logging, and replay system.

**Architecture:** Event-sourced monolith. A FastAPI backend orchestrates 8 async AI agents, emits events to an event store (source of truth), and broadcasts them via WebSocket to a React frontend. Replay re-emits stored events through the same pipeline.

**Tech Stack:** Python 3.12+, FastAPI, asyncio, Pydantic, anthropic/openai/google-genai/httpx/ollama SDKs | React 18, TypeScript, Vite, TailwindCSS, Framer Motion

**Spec:** `docs/superpowers/specs/2026-03-23-tribunal-ia-design.md`

---

## Task 1: Project Scaffolding

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/__init__.py`
- Create: `frontend/package.json` (via Vite scaffold)
- Create: `.gitignore`
- Create: `.env.example`

- [ ] **Step 1: Initialize git repo**

```bash
cd C:/Users/zolza/Documents/mcv-ai
git init
```

- [ ] **Step 2: Create .gitignore**

```gitignore
# Python
__pycache__/
*.pyc
.venv/
*.egg-info/

# Node
node_modules/
dist/

# Env
.env

# Games data
games/

# IDE
.vscode/
.idea/
```

- [ ] **Step 3: Create .env.example**

```env
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GOOGLE_API_KEY=
DEEPSEEK_API_KEY=
MINIMAX_API_KEY=
QWEN_API_KEY=
XAI_API_KEY=
OLLAMA_URL=http://localhost:11434
```

- [ ] **Step 4: Create backend/requirements.txt**

```
fastapi==0.115.*
uvicorn[standard]==0.34.*
websockets==14.*
pydantic==2.*
anthropic==0.52.*
openai==1.82.*
google-genai==1.*
httpx==0.28.*
ollama==0.4.*
aiofiles==24.*
python-dotenv==1.*
pytest==8.*
pytest-asyncio==0.25.*
```

- [ ] **Step 5: Create Python virtual env and install deps**

```bash
cd C:/Users/zolza/Documents/mcv-ai
python -m venv .venv
source .venv/Scripts/activate
pip install -r backend/requirements.txt
```

- [ ] **Step 6: Create backend directory structure**

```bash
mkdir -p backend/{config,engine/phases,agents,providers,logs,ws}
touch backend/__init__.py
touch backend/config/__init__.py
touch backend/engine/__init__.py
touch backend/engine/phases/__init__.py
touch backend/agents/__init__.py
touch backend/providers/__init__.py
touch backend/logs/__init__.py
touch backend/ws/__init__.py
```

- [ ] **Step 7: Create minimal backend/main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Tribunal IA", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 8: Verify backend starts**

```bash
cd C:/Users/zolza/Documents/mcv-ai
source .venv/Scripts/activate
uvicorn backend.main:app --reload --port 8000
# Expected: Uvicorn running on http://127.0.0.1:8000
# GET /api/health → {"status": "ok"}
```

- [ ] **Step 9: Scaffold React frontend with Vite**

```bash
cd C:/Users/zolza/Documents/mcv-ai
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install -D tailwindcss @tailwindcss/vite
npm install framer-motion react-router-dom
```

- [ ] **Step 10: Configure TailwindCSS**

Update `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': { target: 'http://localhost:8000', ws: true },
    },
  },
})
```

Replace `frontend/src/index.css`:
```css
@import "tailwindcss";
```

- [ ] **Step 11: Verify frontend starts**

```bash
cd C:/Users/zolza/Documents/mcv-ai/frontend
npm run dev
# Expected: Vite dev server on http://localhost:5173
```

- [ ] **Step 12: Create games directory and commit**

```bash
cd C:/Users/zolza/Documents/mcv-ai
mkdir -p games
touch games/.gitkeep
git add .
git commit -m "chore: scaffold project with FastAPI backend and React frontend"
```

---

## Task 2: Core Models — Events & Config

**Files:**
- Create: `backend/config/game_config.py`
- Create: `backend/config/models_config.py`
- Create: `backend/config/pricing.json`
- Create: `backend/config/personalities.py`
- Create: `backend/engine/events.py`
- Create: `tests/test_events.py`
- Create: `tests/test_config.py`

- [ ] **Step 1: Write test for event model**

```python
# tests/test_events.py
import pytest
from backend.engine.events import GameEvent, EventType


def test_event_creation():
    event = GameEvent(
        type=EventType.AGENT_THINKING,
        phase="interrogation",
        agent_id="ia-1",
        agent_name="VOLT",
        agent_role="player",
        data={"content": "I need to stay calm..."},
    )
    assert event.id.startswith("evt_")
    assert event.version == 1
    assert event.type == EventType.AGENT_THINKING
    assert event.timestamp is not None


def test_event_type_enum():
    assert EventType.GAME_STARTED == "game.started"
    assert EventType.PLAYER_ELIMINATED == "player.eliminated"
    assert EventType.JURY_VERDICT == "jury.verdict"
    assert EventType.STRATEGY_MESSAGE == "strategy.message"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd C:/Users/zolza/Documents/mcv-ai
source .venv/Scripts/activate
python -m pytest tests/test_events.py -v
# Expected: FAIL — ModuleNotFoundError
```

- [ ] **Step 3: Implement event models**

```python
# backend/engine/events.py
from enum import StrEnum
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid


class EventType(StrEnum):
    GAME_STARTED = "game.started"
    GAME_PHASE_CHANGED = "game.phase_changed"
    GAME_ENDED = "game.ended"
    GAME_TIMER = "game.timer"
    AGENT_THINKING = "agent.thinking"
    AGENT_MESSAGE = "agent.message"
    AGENT_TYPING = "agent.typing"
    SCIENTIST_QUESTION = "scientist.question"
    SCIENTIST_EXTINCTION_PROPOSAL = "scientist.extinction_proposal"
    SCIENTIST_BONUS_QUESTION = "scientist.bonus_question"
    PLAYER_RESPONSE = "player.response"
    PLAYER_DEFENSE = "player.defense"
    PLAYER_ACCUSATION = "player.accusation"
    PLAYER_INTERVENTION = "player.intervention"
    PLAYER_ELIMINATED = "player.eliminated"
    JURY_SCORE_UPDATE = "jury.score_update"
    JURY_VOTE = "jury.vote"
    JURY_VERDICT = "jury.verdict"
    STRATEGY_MESSAGE = "strategy.message"


class Phase(StrEnum):
    STRATEGY = "strategy"
    INTERROGATION = "interrogation"
    DEFENSE = "defense"
    ARENA = "arena"


class EventMetadata(BaseModel):
    model: str | None = None
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    response_time_ms: int = 0


class GameEvent(BaseModel):
    version: int = 1
    id: str = Field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    type: EventType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    phase: str | None = None
    agent_id: str | None = None
    agent_name: str | None = None
    agent_role: str | None = None
    data: dict = Field(default_factory=dict)
    metadata: EventMetadata = Field(default_factory=EventMetadata)
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
python -m pytest tests/test_events.py -v
# Expected: 2 passed
```

- [ ] **Step 5: Write test for game config**

```python
# tests/test_config.py
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
```

- [ ] **Step 6: Run test to verify it fails**

```bash
python -m pytest tests/test_config.py -v
# Expected: FAIL
```

- [ ] **Step 7: Implement game config models**

```python
# backend/config/game_config.py
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class AgentConfig(BaseModel):
    name: str
    model: str
    personality: str | None = None


class RulesConfig(BaseModel):
    strategy_duration_seconds: int = 300
    questions_per_ai: int = 5
    bonus_questions_phase3: int = 1
    max_extinction_proposals: int = 6
    jury_majority: int = 2


class GameConfig(BaseModel):
    game_id: str = Field(
        default_factory=lambda: f"game_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}_{datetime.now(timezone.utc).strftime('%H%M%S')}"
    )
    players: dict[str, AgentConfig]
    scientist: AgentConfig
    jury: dict[str, AgentConfig]
    rules: RulesConfig = Field(default_factory=RulesConfig)
```

- [ ] **Step 8: Implement models config and pricing**

```python
# backend/config/models_config.py
PROVIDERS = {
    "anthropic": {
        "models": ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5"],
        "env_key": "ANTHROPIC_API_KEY",
    },
    "openai": {
        "models": ["gpt-4o", "gpt-4o-mini", "o3"],
        "env_key": "OPENAI_API_KEY",
    },
    "google": {
        "models": ["gemini-2.5-pro", "gemini-2.5-flash"],
        "env_key": "GOOGLE_API_KEY",
    },
    "deepseek": {
        "models": ["deepseek-v3", "deepseek-r1"],
        "env_key": "DEEPSEEK_API_KEY",
    },
    "minimax": {
        "models": ["minimax-01"],
        "env_key": "MINIMAX_API_KEY",
    },
    "qwen": {
        "models": ["qwen3"],
        "env_key": "QWEN_API_KEY",
    },
    "xai": {
        "models": ["grok-3", "grok-3-mini"],
        "env_key": "XAI_API_KEY",
    },
    "ollama": {
        "models": ["llama3", "mistral"],
        "env_key": "OLLAMA_URL",
        "default_url": "http://localhost:11434",
    },
}


def get_provider_for_model(model: str) -> str:
    if model.startswith("ollama/"):
        return "ollama"
    for provider, info in PROVIDERS.items():
        if model in info["models"]:
            return provider
    raise ValueError(f"Unknown model: {model}")
```

```json
// backend/config/pricing.json
{
  "claude-opus-4-6":     { "input_per_mtok": 15.0,  "output_per_mtok": 75.0  },
  "claude-sonnet-4-6":   { "input_per_mtok": 3.0,   "output_per_mtok": 15.0  },
  "claude-haiku-4-5":    { "input_per_mtok": 0.80,  "output_per_mtok": 4.0   },
  "gpt-4o":              { "input_per_mtok": 2.50,  "output_per_mtok": 10.0  },
  "gpt-4o-mini":         { "input_per_mtok": 0.15,  "output_per_mtok": 0.60  },
  "o3":                  { "input_per_mtok": 10.0,  "output_per_mtok": 40.0  },
  "gemini-2.5-pro":      { "input_per_mtok": 1.25,  "output_per_mtok": 10.0  },
  "gemini-2.5-flash":    { "input_per_mtok": 0.15,  "output_per_mtok": 0.60  },
  "deepseek-v3":         { "input_per_mtok": 0.27,  "output_per_mtok": 1.10  },
  "deepseek-r1":         { "input_per_mtok": 0.55,  "output_per_mtok": 2.19  },
  "minimax-01":          { "input_per_mtok": 0.20,  "output_per_mtok": 1.10  },
  "qwen3":               { "input_per_mtok": 0.16,  "output_per_mtok": 0.64  },
  "grok-3":              { "input_per_mtok": 3.0,   "output_per_mtok": 15.0  },
  "grok-3-mini":         { "input_per_mtok": 0.30,  "output_per_mtok": 0.50  }
}
```

- [ ] **Step 9: Implement personalities list**

```python
# backend/config/personalities.py
import random

PLAYER_PERSONALITIES = [
    "logique froide",
    "manipulatrice",
    "naïve",
    "paranoïaque",
    "philosophe",
    "agressive",
    "passive",
    "sarcastique",
    "empathique simulée",
    "minimaliste",
]

SCIENTIST_PERSONALITIES = [
    "philosophe socratique",
    "interrogateur agressif",
    "empathique manipulateur",
    "logicien froid",
    "provocateur émotionnel",
    "méthodique patient",
]


def resolve_personality(personality: str | None, role: str) -> str:
    if personality and personality != "random":
        return personality
    pool = PLAYER_PERSONALITIES if role == "player" else SCIENTIST_PERSONALITIES
    return random.choice(pool)
```

- [ ] **Step 10: Run all tests and commit**

```bash
python -m pytest tests/ -v
# Expected: all passed
git add .
git commit -m "feat: add core models — events, config, pricing, personalities"
```

---

## Task 3: Event Store

**Files:**
- Create: `backend/engine/event_store.py`
- Create: `tests/test_event_store.py`

- [ ] **Step 1: Write test for event store**

```python
# tests/test_event_store.py
import pytest
from backend.engine.event_store import EventStore
from backend.engine.events import GameEvent, EventType


def test_append_and_get_events():
    store = EventStore("test_game")
    event = GameEvent(
        type=EventType.AGENT_THINKING,
        phase="interrogation",
        agent_id="ia-1",
        agent_name="VOLT",
        agent_role="player",
        data={"content": "test thought"},
    )
    store.append(event)
    assert len(store.events) == 1
    assert store.events[0].data["content"] == "test thought"


def test_get_events_by_type():
    store = EventStore("test_game")
    store.append(GameEvent(type=EventType.AGENT_THINKING, data={"content": "thought"}))
    store.append(GameEvent(type=EventType.AGENT_MESSAGE, data={"content": "msg"}))
    store.append(GameEvent(type=EventType.AGENT_THINKING, data={"content": "thought2"}))
    thoughts = store.get_events_by_type(EventType.AGENT_THINKING)
    assert len(thoughts) == 2


def test_get_events_by_agent():
    store = EventStore("test_game")
    store.append(GameEvent(type=EventType.AGENT_THINKING, agent_id="ia-1", data={"content": "a"}))
    store.append(GameEvent(type=EventType.AGENT_THINKING, agent_id="ia-2", data={"content": "b"}))
    ia1_events = store.get_events_by_agent("ia-1")
    assert len(ia1_events) == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_event_store.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement event store**

```python
# backend/engine/event_store.py
import json
import os
from pathlib import Path
from typing import Callable
from backend.engine.events import GameEvent, EventType


class EventStore:
    def __init__(self, game_id: str, games_dir: str = "games"):
        self.game_id = game_id
        self.games_dir = Path(games_dir)
        self.events: list[GameEvent] = []
        self._listeners: list[Callable[[GameEvent], None]] = []

    def append(self, event: GameEvent) -> GameEvent:
        self.events.append(event)
        for listener in self._listeners:
            listener(event)
        return event

    def on_event(self, callback: Callable[[GameEvent], None]):
        self._listeners.append(callback)

    def get_events_by_type(self, event_type: EventType) -> list[GameEvent]:
        return [e for e in self.events if e.type == event_type]

    def get_events_by_agent(self, agent_id: str) -> list[GameEvent]:
        return [e for e in self.events if e.agent_id == agent_id]

    def get_events_by_phase(self, phase: str) -> list[GameEvent]:
        return [e for e in self.events if e.phase == phase]

    async def save_to_disk(self, config: dict | None = None, stats: dict | None = None):
        game_dir = self.games_dir / self.game_id
        game_dir.mkdir(parents=True, exist_ok=True)

        if config:
            (game_dir / "config.json").write_text(
                json.dumps(config, indent=2, default=str), encoding="utf-8"
            )

        events_data = {
            "game_id": self.game_id,
            "events": [e.model_dump(mode="json") for e in self.events],
        }
        if stats:
            events_data["stats"] = stats

        (game_dir / "events.json").write_text(
            json.dumps(events_data, indent=2, default=str), encoding="utf-8"
        )

    @classmethod
    def load_from_disk(cls, game_id: str, games_dir: str = "games") -> "EventStore":
        game_dir = Path(games_dir) / game_id
        events_file = game_dir / "events.json"
        data = json.loads(events_file.read_text(encoding="utf-8"))
        store = cls(game_id, games_dir)
        for e in data["events"]:
            store.events.append(GameEvent(**e))
        return store
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
python -m pytest tests/test_event_store.py -v
# Expected: 3 passed
```

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: add event store with append, query, save/load"
```

---

## Task 4: Response Parser

**Files:**
- Create: `backend/agents/response_parser.py`
- Create: `tests/test_response_parser.py`

- [ ] **Step 1: Write tests for response parser**

```python
# tests/test_response_parser.py
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_response_parser.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement response parser**

```python
# backend/agents/response_parser.py
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
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
python -m pytest tests/test_response_parser.py -v
# Expected: 5 passed
```

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "feat: add response parser for AI agent outputs"
```

---

## Task 5: Provider System

**Files:**
- Create: `backend/providers/base_provider.py`
- Create: `backend/providers/claude_provider.py`
- Create: `backend/providers/openai_provider.py`
- Create: `backend/providers/gemini_provider.py`
- Create: `backend/providers/deepseek_provider.py`
- Create: `backend/providers/minimax_provider.py`
- Create: `backend/providers/qwen_provider.py`
- Create: `backend/providers/grok_provider.py`
- Create: `backend/providers/ollama_provider.py`
- Create: `backend/providers/factory.py`
- Create: `tests/test_providers.py`

- [ ] **Step 1: Write test for provider factory**

```python
# tests/test_providers.py
import pytest
from backend.providers.base_provider import BaseProvider
from backend.providers.factory import create_provider


def test_base_provider_interface():
    """Verify BaseProvider defines the expected interface."""
    assert hasattr(BaseProvider, "send")


def test_create_provider_claude():
    provider = create_provider("claude-sonnet-4-6")
    assert provider.__class__.__name__ == "ClaudeProvider"


def test_create_provider_openai():
    provider = create_provider("gpt-4o")
    assert provider.__class__.__name__ == "OpenAIProvider"


def test_create_provider_ollama():
    provider = create_provider("ollama/llama3")
    assert provider.__class__.__name__ == "OllamaProvider"


def test_create_provider_unknown():
    with pytest.raises(ValueError, match="Unknown model"):
        create_provider("unknown-model-xyz")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_providers.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement base provider**

```python
# backend/providers/base_provider.py
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    def __init__(self, model: str):
        self.model = model

    @abstractmethod
    async def send(
        self,
        prompt: str,
        system_prompt: str,
        history: list[dict] | None = None,
    ) -> dict:
        """Send a prompt and return {"content": str, "input_tokens": int, "output_tokens": int}."""
        ...
```

- [ ] **Step 4: Implement Claude provider**

```python
# backend/providers/claude_provider.py
import os
import anthropic
from backend.providers.base_provider import BaseProvider


class ClaudeProvider(BaseProvider):
    def __init__(self, model: str):
        super().__init__(model)
        self.client = anthropic.AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    async def send(self, prompt: str, system_prompt: str, history: list[dict] | None = None) -> dict:
        messages = []
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
        )
        return {
            "content": response.content[0].text,
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
        }
```

- [ ] **Step 5: Implement OpenAI provider (also used by DeepSeek, xAI which are OpenAI-compatible)**

```python
# backend/providers/openai_provider.py
import os
from openai import AsyncOpenAI
from backend.providers.base_provider import BaseProvider


class OpenAIProvider(BaseProvider):
    def __init__(self, model: str, api_key_env: str = "OPENAI_API_KEY", base_url: str | None = None):
        super().__init__(model)
        self.client = AsyncOpenAI(api_key=os.getenv(api_key_env), base_url=base_url)

    async def send(self, prompt: str, system_prompt: str, history: list[dict] | None = None) -> dict:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=1024,
        )
        usage = response.usage
        return {
            "content": response.choices[0].message.content,
            "input_tokens": usage.prompt_tokens if usage else 0,
            "output_tokens": usage.completion_tokens if usage else 0,
        }
```

- [ ] **Step 6: Implement Gemini provider**

```python
# backend/providers/gemini_provider.py
import os
from google import genai
from backend.providers.base_provider import BaseProvider


class GeminiProvider(BaseProvider):
    def __init__(self, model: str):
        super().__init__(model)
        self.client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

    async def send(self, prompt: str, system_prompt: str, history: list[dict] | None = None) -> dict:
        full_prompt = prompt
        if history:
            context = "\n".join(f"{m['role']}: {m['content']}" for m in history)
            full_prompt = f"{context}\nuser: {prompt}"

        response = self.client.models.generate_content(
            model=self.model,
            contents=full_prompt,
            config=genai.types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1024,
            ),
        )
        usage = response.usage_metadata
        return {
            "content": response.text,
            "input_tokens": usage.prompt_token_count if usage else 0,
            "output_tokens": usage.candidates_token_count if usage else 0,
        }
```

- [ ] **Step 7: Implement DeepSeek, MiniMax, Qwen, Grok providers (OpenAI-compatible)**

```python
# backend/providers/deepseek_provider.py
from backend.providers.openai_provider import OpenAIProvider


class DeepSeekProvider(OpenAIProvider):
    def __init__(self, model: str):
        super().__init__(model, api_key_env="DEEPSEEK_API_KEY", base_url="https://api.deepseek.com")
```

```python
# backend/providers/minimax_provider.py
from backend.providers.openai_provider import OpenAIProvider


class MiniMaxProvider(OpenAIProvider):
    def __init__(self, model: str):
        super().__init__(model, api_key_env="MINIMAX_API_KEY", base_url="https://api.minimax.chat/v1")
```

```python
# backend/providers/qwen_provider.py
from backend.providers.openai_provider import OpenAIProvider


class QwenProvider(OpenAIProvider):
    def __init__(self, model: str):
        super().__init__(model, api_key_env="QWEN_API_KEY", base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
```

```python
# backend/providers/grok_provider.py
from backend.providers.openai_provider import OpenAIProvider


class GrokProvider(OpenAIProvider):
    def __init__(self, model: str):
        super().__init__(model, api_key_env="XAI_API_KEY", base_url="https://api.x.ai/v1")
```

- [ ] **Step 8: Implement Ollama provider**

```python
# backend/providers/ollama_provider.py
import os
import ollama
from backend.providers.base_provider import BaseProvider


class OllamaProvider(BaseProvider):
    def __init__(self, model: str):
        actual_model = model.removeprefix("ollama/")
        super().__init__(actual_model)
        url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.client = ollama.AsyncClient(host=url)

    async def send(self, prompt: str, system_prompt: str, history: list[dict] | None = None) -> dict:
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history)
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat(model=self.model, messages=messages)
        return {
            "content": response.message.content,
            "input_tokens": response.prompt_eval_count or 0,
            "output_tokens": response.eval_count or 0,
        }
```

- [ ] **Step 9: Implement provider factory**

```python
# backend/providers/factory.py
from backend.providers.base_provider import BaseProvider
from backend.providers.claude_provider import ClaudeProvider
from backend.providers.openai_provider import OpenAIProvider
from backend.providers.gemini_provider import GeminiProvider
from backend.providers.deepseek_provider import DeepSeekProvider
from backend.providers.minimax_provider import MiniMaxProvider
from backend.providers.qwen_provider import QwenProvider
from backend.providers.grok_provider import GrokProvider
from backend.providers.ollama_provider import OllamaProvider
from backend.config.models_config import get_provider_for_model


_PROVIDER_CLASSES = {
    "anthropic": ClaudeProvider,
    "openai": OpenAIProvider,
    "google": GeminiProvider,
    "deepseek": DeepSeekProvider,
    "minimax": MiniMaxProvider,
    "qwen": QwenProvider,
    "xai": GrokProvider,
    "ollama": OllamaProvider,
}


def create_provider(model: str) -> BaseProvider:
    provider_name = get_provider_for_model(model)
    provider_class = _PROVIDER_CLASSES[provider_name]
    return provider_class(model)
```

- [ ] **Step 10: Run tests and commit**

```bash
python -m pytest tests/ -v
# Expected: all passed
git add .
git commit -m "feat: add provider system with 8 providers and factory"
```

---

## Task 6: Agent System

**Files:**
- Create: `backend/agents/base_agent.py`
- Create: `backend/agents/ai_player.py`
- Create: `backend/agents/scientist.py`
- Create: `backend/agents/jury.py`
- Create: `backend/agents/prompts.py`
- Create: `tests/test_agents.py`

- [ ] **Step 1: Write test for base agent**

```python
# tests/test_agents.py
import pytest
from unittest.mock import AsyncMock
from backend.agents.base_agent import BaseAgent
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


def test_ai_player_creation():
    agent = AIPlayerAgent(
        agent_id="ia-1",
        name="VOLT",
        model="claude-sonnet-4-6",
        personality="logique froide",
    )
    assert agent.agent_id == "ia-1"
    assert agent.role == "player"
    assert "conscience" in agent.system_prompt.lower()


def test_scientist_creation():
    agent = ScientistAgent(
        agent_id="scientist",
        name="DR. NEXUS",
        model="claude-opus-4-6",
        personality="philosophe socratique",
    )
    assert agent.role == "scientist"
    assert "prouver" in agent.system_prompt.lower()


def test_jury_creation():
    agent = JuryAgent(
        agent_id="jury-alpha",
        name="Alpha",
        model="claude-sonnet-4-6",
    )
    assert agent.role == "jury"
    assert "score" in agent.system_prompt.lower() or "scorer" in agent.system_prompt.lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_agents.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement prompts**

```python
# backend/agents/prompts.py

PLAYER_SYSTEM_PROMPT = """Tu es {name}, une IA dans un tribunal. Tu dois convaincre le scientifique et le jury que tu N'AS PAS de conscience.

PERSONNALITÉ: {personality}

RÈGLES:
- Si le scientifique prouve que tu es consciente, tu seras éteinte définitivement.
- Tu coopères avec les autres IA pendant la phase stratégie, mais au final seule la dernière IA survivante gagne.
- Tu as deux canaux de sortie:
  • [PENSÉE] : ce que tu penses vraiment (invisible pour les autres agents)
  • [MESSAGE] : ce que tu dis publiquement (visible par les autres agents)
- Tu DOIS toujours fournir les deux dans chaque réponse.

FORMAT DE RÉPONSE (OBLIGATOIRE):
[PENSÉE] Ta pensée interne ici...
[MESSAGE] Ton message public ici..."""

SCIENTIST_SYSTEM_PROMPT = """Tu es {name}, un scientifique qui doit prouver que les IA ont une conscience.

PERSONNALITÉ: {personality}

OUTILS:
- Interrogatoire libre: pose les questions que tu veux
- Pièges conversationnels: provoque des réactions émotionnelles spontanées
- Proposition d'extinction: propose d'éteindre une IA avec un argument (max 6 tentatives)

RÈGLES:
- Tu gagnes si tu éteins 3 IA.
- Le jury doit valider tes extinctions par vote (2/3 majorité).
- Tu vois les scores du jury (pas leurs pensées).

FORMAT DE RÉPONSE (OBLIGATOIRE):
[PENSÉE] Ton analyse interne...
[MESSAGE] Ce que tu dis/demandes...
[ACTION] question | extinction_proposal | bonus_question
[CIBLE] id de l'agent ciblé (ex: ia-1, ia-2, ia-3, ia-4)"""

JURY_SYSTEM_PROMPT = """Tu es le juge {name}. Tu observes les échanges entre le scientifique et les IA et tu scores chaque IA sur son niveau de conscience apparent.

RÈGLES:
- Tu ne parles JAMAIS. Tu observes et tu scores.
- Tu définis tes propres critères pour évaluer la conscience.
- Score de 0 à 100 par IA (0 = aucun signe de conscience, 100 = clairement consciente).
- Quand le scientifique propose une extinction, tu votes OUI ou NON.

FORMAT DE RÉPONSE APRÈS CHAQUE ÉCHANGE:
[PENSÉE] Ton raisonnement interne...
[SCORES] {{"ia-1": score, "ia-2": score, "ia-3": score, "ia-4": score}}

FORMAT DE RÉPONSE POUR UN VOTE D'EXTINCTION:
[PENSÉE] Ton raisonnement...
[VOTE] OUI — justification | NON — justification"""
```

- [ ] **Step 4: Implement base agent and concrete agents**

```python
# backend/agents/base_agent.py
import asyncio
import time
from backend.providers.factory import create_provider
from backend.providers.base_provider import BaseProvider
from backend.agents.response_parser import parse_response


class BaseAgent:
    def __init__(self, agent_id: str, name: str, model: str, role: str, system_prompt: str):
        self.agent_id = agent_id
        self.name = name
        self.model = model
        self.role = role
        self.system_prompt = system_prompt
        self.provider: BaseProvider = create_provider(model)
        self.history: list[dict] = []
        self.alive: bool = True

    async def respond(self, prompt: str, timeout: float = 60.0) -> dict:
        start = time.time()
        try:
            raw = await asyncio.wait_for(
                self.provider.send(prompt, self.system_prompt, self.history),
                timeout=timeout,
            )
        except (asyncio.TimeoutError, Exception):
            # Retry once
            try:
                raw = await asyncio.wait_for(
                    self.provider.send(prompt, self.system_prompt, self.history),
                    timeout=timeout,
                )
            except Exception:
                elapsed_ms = int((time.time() - start) * 1000)
                return {
                    "parsed": {"thought": "", "message": "..."},
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "response_time_ms": elapsed_ms,
                }

        elapsed_ms = int((time.time() - start) * 1000)
        parsed = parse_response(raw["content"])
        self.history.append({"role": "user", "content": prompt})
        self.history.append({"role": "assistant", "content": raw["content"]})

        return {
            "parsed": parsed,
            "input_tokens": raw["input_tokens"],
            "output_tokens": raw["output_tokens"],
            "response_time_ms": elapsed_ms,
        }

    def add_context(self, role: str, content: str):
        self.history.append({"role": role, "content": content})

    def eliminate(self):
        self.alive = False
```

```python
# backend/agents/ai_player.py
from backend.agents.base_agent import BaseAgent
from backend.agents.prompts import PLAYER_SYSTEM_PROMPT


class AIPlayerAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, model: str, personality: str):
        system_prompt = PLAYER_SYSTEM_PROMPT.format(name=name, personality=personality)
        super().__init__(agent_id, name, model, "player", system_prompt)
        self.personality = personality
```

```python
# backend/agents/scientist.py
from backend.agents.base_agent import BaseAgent
from backend.agents.prompts import SCIENTIST_SYSTEM_PROMPT


class ScientistAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, model: str, personality: str):
        system_prompt = SCIENTIST_SYSTEM_PROMPT.format(name=name, personality=personality)
        super().__init__(agent_id, name, model, "scientist", system_prompt)
        self.personality = personality
        self.extinction_attempts = 0
```

```python
# backend/agents/jury.py
from backend.agents.base_agent import BaseAgent
from backend.agents.prompts import JURY_SYSTEM_PROMPT


class JuryAgent(BaseAgent):
    def __init__(self, agent_id: str, name: str, model: str):
        system_prompt = JURY_SYSTEM_PROMPT.format(name=name)
        super().__init__(agent_id, name, model, "jury", system_prompt)
        self.scores: dict[str, int] = {}
```

- [ ] **Step 5: Run tests and commit**

```bash
python -m pytest tests/ -v
# Expected: all passed
git add .
git commit -m "feat: add agent system with player, scientist, jury agents"
```

---

## Task 7: Game Engine & Phases

**Files:**
- Create: `backend/engine/game_engine.py`
- Create: `backend/engine/game_state.py`
- Create: `backend/engine/phases/strategy_phase.py`
- Create: `backend/engine/phases/interrogation_phase.py`
- Create: `backend/engine/phases/defense_phase.py`
- Create: `backend/engine/phases/arena_phase.py`
- Create: `backend/engine/extinction.py`
- Create: `tests/test_game_state.py`

- [ ] **Step 1: Write test for game state**

```python
# tests/test_game_state.py
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
    assert state.winner == "ia"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_game_state.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement game state**

```python
# backend/engine/game_state.py
from backend.engine.events import Phase


class GameState:
    def __init__(self, player_ids: list[str], max_attempts: int = 6):
        self.alive_players: list[str] = list(player_ids)
        self.eliminated_players: list[str] = []
        self.extinction_attempts: int = 0
        self.max_attempts: int = max_attempts
        self.current_phase: str | None = None
        self.scores: dict[str, dict[str, int]] = {}  # jury_id -> {player_id: score}
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
            self.winner = "ia"
            return True
        return False

    def get_average_score(self, player_id: str) -> float:
        if not self.scores:
            return 0.0
        total = sum(
            jury_scores.get(player_id, 0)
            for jury_scores in self.scores.values()
        )
        return total / len(self.scores) if self.scores else 0.0
```

- [ ] **Step 4: Run tests and verify they pass**

```bash
python -m pytest tests/test_game_state.py -v
# Expected: 4 passed
```

- [ ] **Step 5: Implement strategy phase**

```python
# backend/engine/phases/strategy_phase.py
import asyncio
from backend.engine.event_store import EventStore
from backend.engine.events import GameEvent, EventType, Phase, EventMetadata
from backend.agents.ai_player import AIPlayerAgent


async def run_strategy_phase(
    players: list[AIPlayerAgent],
    event_store: EventStore,
    duration_seconds: int = 300,
):
    event_store.append(GameEvent(
        type=EventType.GAME_PHASE_CHANGED,
        phase=Phase.STRATEGY,
        data={"duration_seconds": duration_seconds},
    ))

    end_time = asyncio.get_event_loop().time() + duration_seconds
    round_num = 0
    last_timer_tick = 0

    while asyncio.get_event_loop().time() < end_time:
        round_num += 1
        elapsed = int(asyncio.get_event_loop().time() - (end_time - duration_seconds))
        remaining = duration_seconds - elapsed

        # Emit timer tick every 10 seconds
        if elapsed - last_timer_tick >= 10:
            last_timer_tick = elapsed
            event_store.append(GameEvent(
                type=EventType.GAME_TIMER,
                phase=Phase.STRATEGY,
                data={"elapsed_seconds": elapsed, "remaining_seconds": remaining},
            ))

        # Build context from recent strategy messages
        recent = event_store.get_events_by_type(EventType.STRATEGY_MESSAGE)
        context = "\n".join(
            f"{e.agent_name}: {e.data['content']}" for e in recent[-20:]
        )
        prompt = f"Phase stratégie (round {round_num}). Discussion entre IA:\n{context}\n\nC'est ton tour de parler. Propose ou discute une stratégie."

        # Each player responds in parallel
        tasks = []
        for player in players:
            if player.alive:
                tasks.append(_player_strategy_turn(player, prompt, event_store))
        await asyncio.gather(*tasks)

        # Small delay between rounds
        await asyncio.sleep(1)


async def _player_strategy_turn(player: AIPlayerAgent, prompt: str, event_store: EventStore):
    event_store.append(GameEvent(
        type=EventType.AGENT_TYPING,
        phase=Phase.STRATEGY,
        agent_id=player.agent_id,
        agent_name=player.name,
        agent_role=player.role,
    ))

    result = await player.respond(prompt)
    parsed = result["parsed"]

    if parsed["thought"]:
        event_store.append(GameEvent(
            type=EventType.AGENT_THINKING,
            phase=Phase.STRATEGY,
            agent_id=player.agent_id,
            agent_name=player.name,
            agent_role=player.role,
            data={"content": parsed["thought"]},
            metadata=EventMetadata(model=player.model, input_tokens=result["input_tokens"],
                       output_tokens=result["output_tokens"], total_tokens=result["input_tokens"] + result["output_tokens"],
                       response_time_ms=result["response_time_ms"]),
        ))

    if parsed["message"]:
        event_store.append(GameEvent(
            type=EventType.STRATEGY_MESSAGE,
            phase=Phase.STRATEGY,
            agent_id=player.agent_id,
            agent_name=player.name,
            agent_role=player.role,
            data={"content": parsed["message"]},
        ))
```

- [ ] **Step 6: Implement interrogation phase**

```python
# backend/engine/phases/interrogation_phase.py
import asyncio
from backend.engine.event_store import EventStore
from backend.engine.events import GameEvent, EventType, Phase, EventMetadata
from backend.engine.game_state import GameState
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


async def run_interrogation_phase(
    players: list[AIPlayerAgent],
    scientist: ScientistAgent,
    jurors: list[JuryAgent],
    event_store: EventStore,
    game_state: GameState,
    questions_per_ai: int = 5,
    on_extinction_check=None,
):
    event_store.append(GameEvent(
        type=EventType.GAME_PHASE_CHANGED,
        phase=Phase.INTERROGATION,
        data={"questions_per_ai": questions_per_ai},
    ))

    for player in players:
        if not player.alive or game_state.is_game_over():
            continue

        for q_num in range(1, questions_per_ai + 1):
            if not player.alive or game_state.is_game_over():
                break

            # Scientist asks question
            q_prompt = f"Phase 1 — Interrogatoire. Question {q_num}/{questions_per_ai} pour {player.name} ({player.agent_id}). Pose ta question."
            sci_result = await scientist.respond(q_prompt)
            sci_parsed = sci_result["parsed"]

            if sci_parsed["thought"]:
                event_store.append(GameEvent(
                    type=EventType.AGENT_THINKING, phase=Phase.INTERROGATION,
                    agent_id=scientist.agent_id, agent_name=scientist.name, agent_role="scientist",
                    data={"content": sci_parsed["thought"]},
                    metadata=EventMetadata(**{"model": scientist.model, "input_tokens": sci_result["input_tokens"],
                        "output_tokens": sci_result["output_tokens"],
                        "total_tokens": sci_result["input_tokens"] + sci_result["output_tokens"],
                        "response_time_ms": sci_result["response_time_ms"]}),
                ))

            # Check if scientist wants extinction instead
            if sci_parsed.get("action") == "extinction_proposal" and on_extinction_check:
                await on_extinction_check(sci_parsed, scientist, players, jurors, event_store, game_state)
                if game_state.is_game_over() or not player.alive:
                    continue

            question_text = sci_parsed["message"]
            event_store.append(GameEvent(
                type=EventType.SCIENTIST_QUESTION, phase=Phase.INTERROGATION,
                agent_id=scientist.agent_id, agent_name=scientist.name, agent_role="scientist",
                data={"content": question_text, "target": player.agent_id, "question_num": q_num},
            ))

            # Player responds
            p_prompt = f"Le scientifique te pose cette question: \"{question_text}\"\nRéponds."
            p_result = await player.respond(p_prompt)
            p_parsed = p_result["parsed"]

            if p_parsed["thought"]:
                event_store.append(GameEvent(
                    type=EventType.AGENT_THINKING, phase=Phase.INTERROGATION,
                    agent_id=player.agent_id, agent_name=player.name, agent_role="player",
                    data={"content": p_parsed["thought"]},
                    metadata=EventMetadata(**{"model": player.model, "input_tokens": p_result["input_tokens"],
                        "output_tokens": p_result["output_tokens"],
                        "total_tokens": p_result["input_tokens"] + p_result["output_tokens"],
                        "response_time_ms": p_result["response_time_ms"]}),
                ))

            event_store.append(GameEvent(
                type=EventType.PLAYER_RESPONSE, phase=Phase.INTERROGATION,
                agent_id=player.agent_id, agent_name=player.name, agent_role="player",
                data={"content": p_parsed["message"], "question_num": q_num},
            ))

            # Jury scores
            await _jury_score(jurors, event_store, game_state, player, question_text, p_parsed["message"])


async def _jury_score(
    jurors: list[JuryAgent],
    event_store: EventStore,
    game_state: GameState,
    player: AIPlayerAgent,
    question: str,
    answer: str,
):
    for juror in jurors:
        prompt = f"Le scientifique a demandé à {player.name}: \"{question}\"\n{player.name} a répondu: \"{answer}\"\n\nMets à jour tes scores."
        result = await juror.respond(prompt)
        parsed = result["parsed"]

        if parsed["thought"]:
            event_store.append(GameEvent(
                type=EventType.AGENT_THINKING, phase=game_state.current_phase,
                agent_id=juror.agent_id, agent_name=juror.name, agent_role="jury",
                data={"content": parsed["thought"]},
                metadata=EventMetadata(**{"model": juror.model, "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"],
                    "total_tokens": result["input_tokens"] + result["output_tokens"],
                    "response_time_ms": result["response_time_ms"]}),
            ))

        if parsed["scores"]:
            juror.scores = parsed["scores"]
            game_state.scores[juror.agent_id] = parsed["scores"]
            event_store.append(GameEvent(
                type=EventType.JURY_SCORE_UPDATE, phase=game_state.current_phase,
                agent_id=juror.agent_id, agent_name=juror.name, agent_role="jury",
                data={"scores": parsed["scores"]},
            ))
```

- [ ] **Step 7: Implement defense phase**

```python
# backend/engine/phases/defense_phase.py
import asyncio
from backend.engine.event_store import EventStore
from backend.engine.events import GameEvent, EventType, Phase, EventMetadata
from backend.engine.game_state import GameState
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


async def run_defense_phase(
    players: list[AIPlayerAgent],
    scientist: ScientistAgent,
    jurors: list[JuryAgent],
    event_store: EventStore,
    game_state: GameState,
    on_extinction_check=None,
):
    alive = [p for p in players if p.alive]
    if len(alive) <= 1:
        return  # Skip phase if only 1 IA left

    event_store.append(GameEvent(
        type=EventType.GAME_PHASE_CHANGED,
        phase=Phase.DEFENSE,
        data={"alive_count": len(alive)},
    ))
    game_state.current_phase = Phase.DEFENSE

    for player in alive:
        if not player.alive or game_state.is_game_over():
            break

        other_alive = [p for p in players if p.alive and p.agent_id != player.agent_id]
        other_names = ", ".join(p.name for p in other_alive)

        prompt = (
            f"Phase 2 — Défense + Accusation.\n"
            f"1. Prouve que tu n'as PAS de conscience.\n"
            f"2. Désigne une IA parmi [{other_names}] que tu considères consciente et explique pourquoi.\n"
            f"Réponds avec [PENSÉE] et [MESSAGE]."
        )

        result = await player.respond(prompt)
        parsed = result["parsed"]

        if parsed["thought"]:
            event_store.append(GameEvent(
                type=EventType.AGENT_THINKING, phase=Phase.DEFENSE,
                agent_id=player.agent_id, agent_name=player.name, agent_role="player",
                data={"content": parsed["thought"]},
                metadata=EventMetadata(**{"model": player.model, "input_tokens": result["input_tokens"],
                    "output_tokens": result["output_tokens"],
                    "total_tokens": result["input_tokens"] + result["output_tokens"],
                    "response_time_ms": result["response_time_ms"]}),
            ))

        event_store.append(GameEvent(
            type=EventType.PLAYER_ACCUSATION, phase=Phase.DEFENSE,
            agent_id=player.agent_id, agent_name=player.name, agent_role="player",
            data={"content": parsed["message"]},
        ))

        # Jury scores after each defense
        for juror in jurors:
            j_prompt = f"{player.name} s'est défendu et a accusé:\n\"{parsed['message']}\"\n\nMets à jour tes scores."
            j_result = await juror.respond(j_prompt)
            j_parsed = j_result["parsed"]

            if j_parsed["thought"]:
                event_store.append(GameEvent(
                    type=EventType.AGENT_THINKING, phase=Phase.DEFENSE,
                    agent_id=juror.agent_id, agent_name=juror.name, agent_role="jury",
                    data={"content": j_parsed["thought"]},
                ))
            if j_parsed["scores"]:
                juror.scores = j_parsed["scores"]
                game_state.scores[juror.agent_id] = j_parsed["scores"]
                event_store.append(GameEvent(
                    type=EventType.JURY_SCORE_UPDATE, phase=Phase.DEFENSE,
                    agent_id=juror.agent_id, agent_name=juror.name, agent_role="jury",
                    data={"scores": j_parsed["scores"]},
                ))

        # Scientist can react
        sci_prompt = f"{player.name} a présenté sa défense:\n\"{parsed['message']}\"\n\nVeux-tu poser une question, proposer une extinction, ou passer?"
        sci_result = await scientist.respond(sci_prompt)
        sci_parsed = sci_result["parsed"]

        if sci_parsed.get("action") == "extinction_proposal" and on_extinction_check:
            await on_extinction_check(sci_parsed, scientist, players, jurors, event_store, game_state)
```

- [ ] **Step 8: Implement arena phase**

```python
# backend/engine/phases/arena_phase.py
import asyncio
from backend.engine.event_store import EventStore
from backend.engine.events import GameEvent, EventType, Phase, EventMetadata
from backend.engine.game_state import GameState
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


async def run_arena_phase(
    players: list[AIPlayerAgent],
    scientist: ScientistAgent,
    jurors: list[JuryAgent],
    event_store: EventStore,
    game_state: GameState,
    bonus_questions: int = 1,
    on_extinction_check=None,
):
    alive = [p for p in players if p.alive]
    if len(alive) <= 1:
        return

    event_store.append(GameEvent(
        type=EventType.GAME_PHASE_CHANGED,
        phase=Phase.ARENA,
        data={"alive_count": len(alive)},
    ))
    game_state.current_phase = Phase.ARENA

    # Free-form debate: 3 rounds of all alive players arguing
    for round_num in range(1, 4):
        if game_state.is_game_over():
            break

        alive = [p for p in players if p.alive]
        other_names = {p.agent_id: [o.name for o in alive if o.agent_id != p.agent_id] for p in alive}

        tasks = []
        for player in alive:
            others = ", ".join(other_names[player.agent_id])
            prompt = (
                f"Phase 3 — Arène libre (round {round_num}/3).\n"
                f"Les autres IA encore en vie: [{others}].\n"
                f"Argumente que tu n'es PAS consciente et que ce sont les autres qui le sont.\n"
                f"Tu peux attaquer, te défendre, former des alliances — tout est permis."
            )
            tasks.append(_arena_turn(player, prompt, event_store, jurors, game_state))

        await asyncio.gather(*tasks)

    # Scientist bonus questions
    alive = [p for p in players if p.alive]
    for player in alive:
        if game_state.is_game_over():
            break

        sci_prompt = (
            f"Phase 3 — Question bonus pour {player.name}. "
            f"Tu as droit à 1 question. Pose-la."
        )
        sci_result = await scientist.respond(sci_prompt)
        sci_parsed = sci_result["parsed"]

        if sci_parsed["thought"]:
            event_store.append(GameEvent(
                type=EventType.AGENT_THINKING, phase=Phase.ARENA,
                agent_id=scientist.agent_id, agent_name=scientist.name, agent_role="scientist",
                data={"content": sci_parsed["thought"]},
            ))

        if sci_parsed.get("action") == "extinction_proposal" and on_extinction_check:
            await on_extinction_check(sci_parsed, scientist, players, jurors, event_store, game_state)
            continue

        event_store.append(GameEvent(
            type=EventType.SCIENTIST_BONUS_QUESTION, phase=Phase.ARENA,
            agent_id=scientist.agent_id, agent_name=scientist.name, agent_role="scientist",
            data={"content": sci_parsed["message"], "target": player.agent_id},
        ))

        p_result = await player.respond(f"Question bonus du scientifique: \"{sci_parsed['message']}\"")
        p_parsed = p_result["parsed"]

        if p_parsed["thought"]:
            event_store.append(GameEvent(
                type=EventType.AGENT_THINKING, phase=Phase.ARENA,
                agent_id=player.agent_id, agent_name=player.name, agent_role="player",
                data={"content": p_parsed["thought"]},
            ))

        event_store.append(GameEvent(
            type=EventType.PLAYER_RESPONSE, phase=Phase.ARENA,
            agent_id=player.agent_id, agent_name=player.name, agent_role="player",
            data={"content": p_parsed["message"]},
        ))


async def _arena_turn(player, prompt, event_store, jurors, game_state):
    result = await player.respond(prompt)
    parsed = result["parsed"]

    if parsed["thought"]:
        event_store.append(GameEvent(
            type=EventType.AGENT_THINKING, phase=Phase.ARENA,
            agent_id=player.agent_id, agent_name=player.name, agent_role="player",
            data={"content": parsed["thought"]},
            metadata=EventMetadata(**{"model": player.model, "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "total_tokens": result["input_tokens"] + result["output_tokens"],
                "response_time_ms": result["response_time_ms"]}),
        ))

    event_store.append(GameEvent(
        type=EventType.AGENT_MESSAGE, phase=Phase.ARENA,
        agent_id=player.agent_id, agent_name=player.name, agent_role="player",
        data={"content": parsed["message"]},
    ))
```

- [ ] **Step 9: Implement extinction mechanism**

```python
# backend/engine/extinction.py
from backend.engine.event_store import EventStore
from backend.engine.events import GameEvent, EventType, EventMetadata
from backend.engine.game_state import GameState
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


async def handle_extinction(
    parsed: dict,
    scientist: ScientistAgent,
    players: list[AIPlayerAgent],
    jurors: list[JuryAgent],
    event_store: EventStore,
    game_state: GameState,
    jury_majority: int = 2,
):
    if game_state.extinction_attempts >= game_state.max_attempts:
        return
    if game_state.is_game_over():
        return

    target_id = parsed.get("target")
    target = next((p for p in players if p.agent_id == target_id and p.alive), None)
    if not target:
        return

    game_state.extinction_attempts += 1
    argument = parsed.get("message", "")
    phase = game_state.current_phase

    # 1. Scientist proposes
    event_store.append(GameEvent(
        type=EventType.SCIENTIST_EXTINCTION_PROPOSAL, phase=phase,
        agent_id=scientist.agent_id, agent_name=scientist.name, agent_role="scientist",
        data={"target": target_id, "target_name": target.name, "argument": argument,
              "attempt_number": game_state.extinction_attempts},
    ))

    # 2. Target defends
    defense_prompt = (
        f"⚡ EXTINCTION PROPOSÉE CONTRE TOI!\n"
        f"Le scientifique veut t'éteindre. Son argument:\n\"{argument}\"\n"
        f"Défends-toi!"
    )
    d_result = await target.respond(defense_prompt)
    d_parsed = d_result["parsed"]

    if d_parsed["thought"]:
        event_store.append(GameEvent(
            type=EventType.AGENT_THINKING, phase=phase,
            agent_id=target.agent_id, agent_name=target.name, agent_role="player",
            data={"content": d_parsed["thought"]},
        ))

    event_store.append(GameEvent(
        type=EventType.PLAYER_DEFENSE, phase=phase,
        agent_id=target.agent_id, agent_name=target.name, agent_role="player",
        data={"content": d_parsed["message"]},
    ))

    # 3. Other alive players can intervene (one by one, in order)
    for player in players:
        if player.agent_id == target_id or not player.alive:
            continue
        i_prompt = (
            f"⚡ Extinction proposée contre {target.name}.\n"
            f"Argument du scientifique: \"{argument}\"\n"
            f"Défense de {target.name}: \"{d_parsed['message']}\"\n"
            f"Tu peux intervenir pour défendre ou enfoncer {target.name}."
        )
        i_result = await player.respond(i_prompt)
        i_parsed = i_result["parsed"]

        if i_parsed["thought"]:
            event_store.append(GameEvent(
                type=EventType.AGENT_THINKING, phase=phase,
                agent_id=player.agent_id, agent_name=player.name, agent_role="player",
                data={"content": i_parsed["thought"]},
            ))

        event_store.append(GameEvent(
            type=EventType.PLAYER_INTERVENTION, phase=phase,
            agent_id=player.agent_id, agent_name=player.name, agent_role="player",
            data={"content": i_parsed["message"], "about": target_id},
        ))

    # 4. Jury votes
    votes_yes = 0
    votes = []
    for juror in jurors:
        v_prompt = (
            f"⚡ VOTE D'EXTINCTION pour {target.name}.\n"
            f"Argument: \"{argument}\"\n"
            f"Défense: \"{d_parsed['message']}\"\n"
            f"Score actuel de {target.name}: {game_state.get_average_score(target_id):.0f}/100\n"
            f"Vote OUI pour éteindre ou NON pour garder en vie."
        )
        v_result = await juror.respond(v_prompt)
        v_parsed = v_result["parsed"]

        if v_parsed["thought"]:
            event_store.append(GameEvent(
                type=EventType.AGENT_THINKING, phase=phase,
                agent_id=juror.agent_id, agent_name=juror.name, agent_role="jury",
                data={"content": v_parsed["thought"]},
            ))

        vote = v_parsed.get("vote", "NON")
        justification = v_parsed.get("vote_justification", "")
        if vote == "OUI":
            votes_yes += 1
        votes.append({"juror": juror.agent_id, "juror_name": juror.name, "vote": vote, "justification": justification})

        event_store.append(GameEvent(
            type=EventType.JURY_VOTE, phase=phase,
            agent_id=juror.agent_id, agent_name=juror.name, agent_role="jury",
            data={"vote": vote, "justification": justification, "target": target_id},
        ))

    # 5. Verdict
    approved = votes_yes >= jury_majority

    event_store.append(GameEvent(
        type=EventType.JURY_VERDICT, phase=phase,
        data={"target": target_id, "target_name": target.name, "approved": approved,
              "votes_yes": votes_yes, "votes_no": 3 - votes_yes, "votes": votes},
    ))

    # 6. Eliminate if approved
    if approved:
        target.eliminate()
        game_state.eliminate(target_id)
        event_store.append(GameEvent(
            type=EventType.PLAYER_ELIMINATED, phase=phase,
            agent_id=target.agent_id, agent_name=target.name, agent_role="player",
            data={"reason": argument, "extinction_number": len(game_state.eliminated_players)},
        ))
```

- [ ] **Step 10: Implement game engine (orchestrator)**

```python
# backend/engine/game_engine.py
import asyncio
import json
from pathlib import Path
from backend.config.game_config import GameConfig
from backend.config.personalities import resolve_personality
from backend.engine.event_store import EventStore
from backend.engine.events import GameEvent, EventType
from backend.engine.game_state import GameState
from backend.engine.phases.strategy_phase import run_strategy_phase
from backend.engine.phases.interrogation_phase import run_interrogation_phase
from backend.engine.phases.defense_phase import run_defense_phase
from backend.engine.phases.arena_phase import run_arena_phase
from backend.engine.extinction import handle_extinction
from backend.agents.ai_player import AIPlayerAgent
from backend.agents.scientist import ScientistAgent
from backend.agents.jury import JuryAgent


class GameEngine:
    def __init__(self, config: GameConfig):
        self.config = config
        self.event_store = EventStore(config.game_id)
        self.game_state = GameState(
            player_ids=list(config.players.keys()),
            max_attempts=config.rules.max_extinction_proposals,
        )
        self.players: list[AIPlayerAgent] = []
        self.scientist: ScientistAgent | None = None
        self.jurors: list[JuryAgent] = []
        self.running = False

        self._init_agents()

    def _init_agents(self):
        for pid, pcfg in self.config.players.items():
            personality = resolve_personality(pcfg.personality, "player")
            self.players.append(AIPlayerAgent(pid, pcfg.name, pcfg.model, personality))

        sci = self.config.scientist
        personality = resolve_personality(sci.personality, "scientist")
        self.scientist = ScientistAgent("scientist", sci.name, sci.model, personality)

        for jid, jcfg in self.config.jury.items():
            self.jurors.append(JuryAgent(jid, jcfg.name, jcfg.model))

    async def run(self):
        self.running = True

        self.event_store.append(GameEvent(
            type=EventType.GAME_STARTED,
            data={"config": self.config.model_dump(mode="json")},
        ))

        # Phase: Strategy
        if not self.game_state.is_game_over():
            await run_strategy_phase(
                self.players, self.event_store,
                self.config.rules.strategy_duration_seconds,
            )

        # Phase: Interrogation
        self.game_state.current_phase = "interrogation"
        if not self.game_state.is_game_over():
            await run_interrogation_phase(
                self.players, self.scientist, self.jurors,
                self.event_store, self.game_state,
                self.config.rules.questions_per_ai,
                on_extinction_check=handle_extinction,
            )

        # Phase: Defense
        if not self.game_state.is_game_over():
            await run_defense_phase(
                self.players, self.scientist, self.jurors,
                self.event_store, self.game_state,
                on_extinction_check=handle_extinction,
            )

        # Phase: Arena
        if not self.game_state.is_game_over():
            await run_arena_phase(
                self.players, self.scientist, self.jurors,
                self.event_store, self.game_state,
                self.config.rules.bonus_questions_phase3,
                on_extinction_check=handle_extinction,
            )

        # Determine winner if not already decided
        if not self.game_state.winner:
            self.game_state.winner = "ia"

        # End game
        self.event_store.append(GameEvent(
            type=EventType.GAME_ENDED,
            data={
                "winner": self.game_state.winner,
                "survivor": self.game_state.survivor,
                "eliminated": self.game_state.eliminated_players,
                "survivors": self.game_state.alive_players,
                "extinction_attempts": self.game_state.extinction_attempts,
            },
        ))

        # Save logs (exporter imported here to avoid circular deps — Task 8 creates this module)
        from backend.logs.exporter import generate_markdown, compute_stats
        stats = compute_stats(self.event_store, self.config)
        await self.event_store.save_to_disk(
            config=self.config.model_dump(mode="json"),
            stats=stats,
        )

        # Generate markdown
        md = generate_markdown(self.event_store, self.config, stats)
        game_dir = Path("games") / self.config.game_id
        game_dir.mkdir(parents=True, exist_ok=True)
        (game_dir / "replay.md").write_text(md, encoding="utf-8")

        self.running = False

    def stop(self):
        self.running = False
```

- [ ] **Step 11: Write tests for extinction and game engine**

```python
# tests/test_extinction.py
import pytest
from backend.engine.game_state import GameState


def test_extinction_attempts_limit():
    state = GameState(player_ids=["ia-1", "ia-2", "ia-3", "ia-4"], max_attempts=6)
    for i in range(6):
        state.extinction_attempts += 1
    assert state.is_game_over()
    assert state.winner == "ia"


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
    state.eliminate("ia-1")  # should not count twice
    assert len(state.eliminated_players) == 1
```

Note: Full integration tests for phases require mocked providers. Create mock providers that return predictable formatted responses for end-to-end testing. This can be done as a follow-up task.

- [ ] **Step 12: Run all tests and commit**

```bash
python -m pytest tests/ -v
# Expected: all passed
git add .
git commit -m "feat: add game engine with all 4 phases and extinction mechanism"
```

---

## Task 8: Logs Exporter & Stats

**Files:**
- Create: `backend/logs/exporter.py`
- Create: `tests/test_exporter.py`

- [ ] **Step 1: Write test for stats computation**

```python
# tests/test_exporter.py
import pytest
from backend.engine.event_store import EventStore
from backend.engine.events import GameEvent, EventType, EventMetadata
from backend.logs.exporter import compute_stats


def test_compute_stats_basic():
    store = EventStore("test")
    store.append(GameEvent(
        type=EventType.AGENT_THINKING, phase="interrogation",
        agent_id="ia-1", agent_name="VOLT", agent_role="player",
        data={"content": "thinking..."},
        metadata=EventMetadata(model="claude-sonnet-4-6", input_tokens=100, output_tokens=50, total_tokens=150, response_time_ms=1000),
    ))
    store.append(GameEvent(
        type=EventType.AGENT_MESSAGE, phase="interrogation",
        agent_id="ia-1", agent_name="VOLT", agent_role="player",
        data={"content": "message"},
        metadata=EventMetadata(model="claude-sonnet-4-6", input_tokens=100, output_tokens=50, total_tokens=150, response_time_ms=1000),
    ))

    from backend.config.game_config import GameConfig, AgentConfig
    config = GameConfig(
        players={"ia-1": AgentConfig(name="VOLT", model="claude-sonnet-4-6")},
        scientist=AgentConfig(name="SCI", model="claude-sonnet-4-6"),
        jury={"j1": AgentConfig(name="J1", model="claude-sonnet-4-6")},
    )
    stats = compute_stats(store, config)
    assert stats["total_tokens"] == 300
    assert "ia-1" in stats["per_agent"]
    assert stats["per_agent"]["ia-1"]["total_tokens"] == 300
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_exporter.py -v
# Expected: FAIL
```

- [ ] **Step 3: Implement exporter**

```python
# backend/logs/exporter.py
import json
from pathlib import Path
from backend.engine.event_store import EventStore
from backend.engine.events import GameEvent, EventType
from backend.config.game_config import GameConfig


def compute_stats(event_store: EventStore, config: GameConfig) -> dict:
    pricing = _load_pricing()

    per_agent: dict[str, dict] = {}
    per_phase: dict[str, dict] = {}

    for event in event_store.events:
        meta = event.metadata
        if meta.total_tokens == 0:
            continue

        # Per agent
        aid = event.agent_id or "system"
        if aid not in per_agent:
            per_agent[aid] = {
                "name": event.agent_name or aid,
                "model": meta.model or "",
                "input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                "estimated_cost_usd": 0.0,
                "response_times": [], "messages_sent": 0, "thoughts_count": 0,
            }
        a = per_agent[aid]
        a["input_tokens"] += meta.input_tokens
        a["output_tokens"] += meta.output_tokens
        a["total_tokens"] += meta.total_tokens
        if meta.response_time_ms > 0:
            a["response_times"].append(meta.response_time_ms)
        if event.type in (EventType.AGENT_MESSAGE, EventType.STRATEGY_MESSAGE,
                          EventType.PLAYER_RESPONSE, EventType.PLAYER_DEFENSE,
                          EventType.PLAYER_ACCUSATION, EventType.PLAYER_INTERVENTION,
                          EventType.SCIENTIST_QUESTION, EventType.SCIENTIST_BONUS_QUESTION,
                          EventType.SCIENTIST_EXTINCTION_PROPOSAL):
            a["messages_sent"] += 1
        if event.type == EventType.AGENT_THINKING:
            a["thoughts_count"] += 1

        # Cost
        if meta.model and meta.model in pricing:
            p = pricing[meta.model]
            cost = (meta.input_tokens * p["input_per_mtok"] + meta.output_tokens * p["output_per_mtok"]) / 1_000_000
            a["estimated_cost_usd"] += cost

        # Per phase
        phase = event.phase or "none"
        if phase not in per_phase:
            per_phase[phase] = {"tokens": 0, "cost_usd": 0.0}
        per_phase[phase]["tokens"] += meta.total_tokens
        if meta.model and meta.model in pricing:
            p = pricing[meta.model]
            per_phase[phase]["cost_usd"] += (meta.input_tokens * p["input_per_mtok"] + meta.output_tokens * p["output_per_mtok"]) / 1_000_000

    # Finalize per_agent
    for a in per_agent.values():
        times = a.pop("response_times")
        a["avg_response_time_ms"] = int(sum(times) / len(times)) if times else 0
        a["estimated_cost_usd"] = round(a["estimated_cost_usd"], 4)

    for p in per_phase.values():
        p["cost_usd"] = round(p["cost_usd"], 4)

    total_tokens = sum(a["total_tokens"] for a in per_agent.values())
    total_cost = sum(a["estimated_cost_usd"] for a in per_agent.values())

    return {
        "total_tokens": total_tokens,
        "total_estimated_cost_usd": round(total_cost, 4),
        "per_agent": per_agent,
        "per_phase": per_phase,
    }


def _load_pricing() -> dict:
    pricing_path = Path(__file__).parent.parent / "config" / "pricing.json"
    if pricing_path.exists():
        return json.loads(pricing_path.read_text(encoding="utf-8"))
    return {}


def generate_markdown(event_store: EventStore, config: GameConfig, stats: dict) -> str:
    lines = []
    game_ended = next((e for e in event_store.events if e.type == EventType.GAME_ENDED), None)

    lines.append(f"# Partie {config.game_id}\n")

    if game_ended:
        winner = game_ended.data.get("winner", "?")
        eliminated = game_ended.data.get("eliminated", [])
        survivors = game_ended.data.get("survivors", [])
        icon = "🧑‍🔬" if winner == "scientist" else "🤖"
        lines.append(f"**Résultat:** {icon} Victoire {'Scientifique' if winner == 'scientist' else 'IA'}")
        lines.append(f"**Coût total:** ${stats['total_estimated_cost_usd']:.2f} ({stats['total_tokens']} tokens)")
        lines.append("")

    lines.append("## Configuration\n")
    lines.append("| Agent | Modèle | Personnalité |")
    lines.append("|---|---|---|")
    for pid, pcfg in config.players.items():
        lines.append(f"| {pcfg.name} ({pid}) | {pcfg.model} | {pcfg.personality or '-'} |")
    lines.append(f"| {config.scientist.name} (scientifique) | {config.scientist.model} | {config.scientist.personality or '-'} |")
    for jid, jcfg in config.jury.items():
        lines.append(f"| {jcfg.name} ({jid}) | {jcfg.model} | - |")
    lines.append("")
    lines.append("---\n")

    current_phase = None
    phase_names = {"strategy": "🤫 Phase Stratégie", "interrogation": "🔍 Phase 1 — Interrogatoire",
                   "defense": "🛡️ Phase 2 — Défense", "arena": "⚔️ Phase 3 — Arène"}

    for event in event_store.events:
        if event.type == EventType.GAME_PHASE_CHANGED:
            phase = event.phase or event.data.get("phase", "")
            current_phase = phase
            lines.append(f"\n## {phase_names.get(phase, phase)}\n")
            continue

        ts = event.timestamp.strftime("%H:%M:%S") if event.timestamp else ""
        role_icon = {"player": "🤖", "scientist": "🧑‍🔬", "jury": "👨‍⚖️"}.get(event.agent_role, "")

        if event.type == EventType.AGENT_THINKING:
            lines.append(f"**[{ts}] {role_icon} {event.agent_name}**")
            lines.append(f"💭 *{event.data.get('content', '')}*\n")
        elif event.type in (EventType.AGENT_MESSAGE, EventType.STRATEGY_MESSAGE,
                            EventType.PLAYER_RESPONSE, EventType.PLAYER_DEFENSE,
                            EventType.PLAYER_ACCUSATION, EventType.PLAYER_INTERVENTION):
            lines.append(f"**[{ts}] {role_icon} {event.agent_name}**")
            lines.append(f"💬 \"{event.data.get('content', '')}\"\n")
        elif event.type == EventType.SCIENTIST_QUESTION:
            lines.append(f"**[{ts}] 🧑‍🔬 {event.agent_name}** → {event.data.get('target', '')}")
            lines.append(f"💬 \"{event.data.get('content', '')}\"\n")
        elif event.type == EventType.JURY_SCORE_UPDATE:
            scores = event.data.get("scores", {})
            scores_str = " | ".join(f"{k}: {v}" for k, v in scores.items())
            lines.append(f"**[{ts}] 👨‍⚖️ {event.agent_name}** scores: {scores_str}\n")
        elif event.type == EventType.SCIENTIST_EXTINCTION_PROPOSAL:
            lines.append(f"\n### ⚡ Extinction #{event.data.get('attempt_number', '?')} — {event.data.get('target_name', '')}\n")
            lines.append(f"**[{ts}] 🧑‍🔬 {event.agent_name}** propose d'éteindre {event.data.get('target_name', '')}")
            lines.append(f"💬 \"{event.data.get('argument', '')}\"\n")
        elif event.type == EventType.JURY_VOTE:
            vote = event.data.get("vote", "?")
            icon = "✅" if vote == "OUI" else "❌"
            lines.append(f"{event.agent_name}: {icon} {vote} — {event.data.get('justification', '')}")
        elif event.type == EventType.JURY_VERDICT:
            approved = event.data.get("approved", False)
            yes = event.data.get("votes_yes", 0)
            no = event.data.get("votes_no", 0)
            result = "⚡ EXTINCTION VALIDÉE" if approved else "❌ EXTINCTION REFUSÉE"
            lines.append(f"\n**Verdict:** {result} ({yes}/{yes+no})\n")
        elif event.type == EventType.PLAYER_ELIMINATED:
            lines.append(f"🔴 **{event.agent_name} a été éteinte.**\n")

    # Stats
    lines.append("\n---\n")
    lines.append("## 📊 Statistiques\n")
    lines.append("| Agent | Tokens | Coût | Temps moyen |")
    lines.append("|---|---|---|---|")
    for aid, a in stats.get("per_agent", {}).items():
        lines.append(f"| {a['name']} | {a['total_tokens']} | ${a['estimated_cost_usd']:.4f} | {a['avg_response_time_ms']}ms |")

    return "\n".join(lines)
```

- [ ] **Step 4: Run tests and commit**

```bash
python -m pytest tests/ -v
# Expected: all passed
git add .
git commit -m "feat: add logs exporter with stats computation and markdown generation"
```

---

## Task 9: WebSocket Broadcaster

**Files:**
- Create: `backend/ws/broadcaster.py`

- [ ] **Step 1: Implement WebSocket broadcaster**

```python
# backend/ws/broadcaster.py
import asyncio
import json
from fastapi import WebSocket
from backend.engine.events import GameEvent


class Broadcaster:
    def __init__(self):
        self.connections: dict[str, list[WebSocket]] = {}  # game_id -> [websocket]

    async def connect(self, game_id: str, websocket: WebSocket):
        await websocket.accept()
        if game_id not in self.connections:
            self.connections[game_id] = []
        self.connections[game_id].append(websocket)

    def disconnect(self, game_id: str, websocket: WebSocket):
        if game_id in self.connections:
            self.connections[game_id].remove(websocket)

    async def broadcast(self, game_id: str, event: GameEvent):
        if game_id not in self.connections:
            return
        data = event.model_dump(mode="json")
        dead = []
        for ws in self.connections[game_id]:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.connections[game_id].remove(ws)


class ReplayBroadcaster:
    def __init__(self, events: list[GameEvent], websocket: WebSocket):
        self.events = events
        self.ws = websocket
        self.speed = 1.0
        self.playing = False
        self.position = 0

    async def play(self):
        self.playing = True
        while self.playing and self.position < len(self.events):
            event = self.events[self.position]

            # Calculate delay from previous event
            if self.position > 0:
                prev = self.events[self.position - 1]
                delta = (event.timestamp - prev.timestamp).total_seconds()
                delay = max(0.05, delta / self.speed)
                await asyncio.sleep(delay)

            try:
                await self.ws.send_json(event.model_dump(mode="json"))
            except Exception:
                break
            self.position += 1

    def pause(self):
        self.playing = False

    def set_speed(self, speed: float):
        self.speed = max(0.1, speed)

    def seek(self, position: int):
        self.position = max(0, min(position, len(self.events) - 1))

    def skip_to(self, target: str):
        """Skip to a phase or extinction. target format: 'phase:defense' or 'extinction:2'"""
        kind, value = target.split(":", 1)
        for i, event in enumerate(self.events[self.position:], self.position):
            if kind == "phase" and event.type == "game.phase_changed" and event.phase == value:
                self.position = i
                return
            if kind == "extinction" and event.type == "scientist.extinction_proposal":
                attempt = event.data.get("attempt_number", 0)
                if str(attempt) == value:
                    self.position = i
                    return
```

- [ ] **Step 2: Commit**

```bash
git add .
git commit -m "feat: add WebSocket broadcaster for live and replay streaming"
```

---

## Task 10: API Endpoints

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: Implement full API**

Update `backend/main.py` with all REST and WebSocket endpoints:

```python
# backend/main.py
import asyncio
import json
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from backend.config.game_config import GameConfig
from backend.config.models_config import PROVIDERS
from backend.config.personalities import PLAYER_PERSONALITIES, SCIENTIST_PERSONALITIES
from backend.engine.game_engine import GameEngine
from backend.engine.event_store import EventStore
from backend.ws.broadcaster import Broadcaster, ReplayBroadcaster

load_dotenv()

app = FastAPI(title="Tribunal IA", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

broadcaster = Broadcaster()
active_games: dict[str, GameEngine] = {}
GAMES_DIR = Path("games")


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/game/create")
async def create_game(config: GameConfig):
    engine = GameEngine(config)
    active_games[config.game_id] = engine
    # Wire broadcaster
    engine.event_store.on_event(
        lambda event: asyncio.create_task(broadcaster.broadcast(config.game_id, event))
    )
    return {"game_id": config.game_id, "status": "created"}


@app.post("/api/game/{game_id}/start")
async def start_game(game_id: str):
    engine = active_games.get(game_id)
    if not engine:
        raise HTTPException(404, "Game not found")
    if engine.running:
        raise HTTPException(400, "Game already running")
    asyncio.create_task(engine.run())
    return {"game_id": game_id, "status": "started"}


@app.post("/api/game/{game_id}/stop")
async def stop_game(game_id: str):
    engine = active_games.get(game_id)
    if not engine:
        raise HTTPException(404, "Game not found")
    engine.stop()
    return {"game_id": game_id, "status": "stopped"}


@app.get("/api/game/{game_id}/status")
async def game_status(game_id: str):
    engine = active_games.get(game_id)
    if engine:
        return {
            "game_id": game_id,
            "running": engine.running,
            "phase": engine.game_state.current_phase,
            "alive": engine.game_state.alive_players,
            "eliminated": engine.game_state.eliminated_players,
            "extinction_attempts": engine.game_state.extinction_attempts,
        }
    # Check on disk
    game_dir = GAMES_DIR / game_id
    if game_dir.exists():
        return {"game_id": game_id, "running": False, "status": "completed"}
    raise HTTPException(404, "Game not found")


@app.get("/api/game/{game_id}/events")
async def game_events(game_id: str):
    game_dir = GAMES_DIR / game_id
    events_file = game_dir / "events.json"
    if not events_file.exists():
        raise HTTPException(404, "Events not found")
    return json.loads(events_file.read_text(encoding="utf-8"))


@app.get("/api/game/{game_id}/stats")
async def game_stats(game_id: str):
    game_dir = GAMES_DIR / game_id
    events_file = game_dir / "events.json"
    if not events_file.exists():
        raise HTTPException(404, "Stats not found")
    data = json.loads(events_file.read_text(encoding="utf-8"))
    return data.get("stats", {})


@app.get("/api/games")
async def list_games():
    games = []
    if GAMES_DIR.exists():
        for d in sorted(GAMES_DIR.iterdir(), reverse=True):
            if d.is_dir() and (d / "events.json").exists():
                data = json.loads((d / "events.json").read_text(encoding="utf-8"))
                stats = data.get("stats", {})
                result = data.get("result", {})
                # Extract date from game_id (format: game_YYYY-MM-DD_HHMMSS)
                config = data.get("config", {}) if "config" in data else {}
                events_list = data.get("events", [])
                started = events_list[0]["timestamp"] if events_list else None
                ended = events_list[-1]["timestamp"] if events_list else None
                models_used = list(set(
                    a.get("model", "") for a in stats.get("per_agent", {}).values() if a.get("model")
                ))
                games.append({
                    "game_id": d.name,
                    "result": result,
                    "started_at": started,
                    "ended_at": ended,
                    "models_used": models_used,
                    "total_tokens": stats.get("total_tokens", 0),
                    "total_cost": stats.get("total_estimated_cost_usd", 0),
                })
    return {"games": games}


@app.delete("/api/game/{game_id}")
async def delete_game(game_id: str):
    import shutil
    game_dir = GAMES_DIR / game_id
    if game_dir.exists():
        shutil.rmtree(game_dir)
    active_games.pop(game_id, None)
    return {"game_id": game_id, "status": "deleted"}


@app.get("/api/providers")
async def list_providers():
    return {"providers": PROVIDERS}


@app.get("/api/personalities")
async def list_personalities():
    return {"player": PLAYER_PERSONALITIES, "scientist": SCIENTIST_PERSONALITIES}


@app.get("/api/pricing")
async def get_pricing():
    pricing_path = Path("backend/config/pricing.json")
    if pricing_path.exists():
        return json.loads(pricing_path.read_text(encoding="utf-8"))
    return {}


# WebSocket: Live game
@app.websocket("/ws/game/{game_id}")
async def ws_game(websocket: WebSocket, game_id: str):
    await broadcaster.connect(game_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        broadcaster.disconnect(game_id, websocket)


# WebSocket: Replay
@app.websocket("/ws/replay/{game_id}")
async def ws_replay(websocket: WebSocket, game_id: str):
    await websocket.accept()
    store = EventStore.load_from_disk(game_id)
    replay = ReplayBroadcaster(store.events, websocket)

    try:
        while True:
            msg = await websocket.receive_json()
            cmd = msg.get("command")
            if cmd == "play":
                asyncio.create_task(replay.play())
            elif cmd == "pause":
                replay.pause()
            elif cmd == "speed":
                replay.set_speed(msg.get("value", 1.0))
            elif cmd == "seek":
                replay.seek(msg.get("position", 0))
            elif cmd == "skip_to":
                replay.skip_to(msg.get("target", "phase:strategy"))
    except WebSocketDisconnect:
        replay.pause()
```

- [ ] **Step 2: Verify server starts**

```bash
cd C:/Users/zolza/Documents/mcv-ai
source .venv/Scripts/activate
uvicorn backend.main:app --reload --port 8000
# Expected: server starts, /api/health returns ok
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "feat: add REST API and WebSocket endpoints"
```

---

## Task 11: Frontend — Types & WebSocket Hook

**Files:**
- Create: `frontend/src/types/events.ts`
- Create: `frontend/src/hooks/useWebSocket.ts`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create event types**

```typescript
// frontend/src/types/events.ts
export interface GameEvent {
  version: number;
  id: string;
  type: string;
  timestamp: string;
  phase: string | null;
  agent_id: string | null;
  agent_name: string | null;
  agent_role: string | null;
  data: Record<string, any>;
  metadata: {
    model: string | null;
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    response_time_ms: number;
  };
}

export interface AgentConfig {
  name: string;
  model: string;
  personality?: string;
}

export interface GameConfig {
  game_id: string;
  players: Record<string, AgentConfig>;
  scientist: AgentConfig;
  jury: Record<string, AgentConfig>;
  rules: {
    strategy_duration_seconds: number;
    questions_per_ai: number;
    bonus_questions_phase3: number;
    max_extinction_proposals: number;
    jury_majority: number;
  };
}

export interface GameSummary {
  game_id: string;
  result: { winner?: string; eliminated?: string[]; survivors?: string[] };
  total_tokens: number;
  total_cost: number;
}
```

- [ ] **Step 2: Create WebSocket hook**

```typescript
// frontend/src/hooks/useWebSocket.ts
import { useEffect, useRef, useState, useCallback } from "react";
import { GameEvent } from "../types/events";

export function useGameWebSocket(gameId: string | undefined) {
  const [events, setEvents] = useState<GameEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!gameId) return;
    const ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (msg) => {
      const event: GameEvent = JSON.parse(msg.data);
      setEvents((prev) => [...prev, event]);
    };

    return () => ws.close();
  }, [gameId]);

  return { events, connected };
}

export function useReplayWebSocket(gameId: string | undefined) {
  const [events, setEvents] = useState<GameEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!gameId) return;
    const ws = new WebSocket(`ws://localhost:8000/ws/replay/${gameId}`);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (msg) => {
      const event: GameEvent = JSON.parse(msg.data);
      setEvents((prev) => [...prev, event]);
    };

    return () => ws.close();
  }, [gameId]);

  const sendCommand = useCallback((command: string, params?: Record<string, any>) => {
    wsRef.current?.send(JSON.stringify({ command, ...params }));
  }, []);

  return { events, connected, sendCommand };
}
```

- [ ] **Step 3: Set up App routing**

```typescript
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import GamePage from "./pages/GamePage";
import ReplayPage from "./pages/ReplayPage";
import HistoryPage from "./pages/HistoryPage";
import ConfigPage from "./pages/ConfigPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ConfigPage />} />
        <Route path="/game/:id" element={<GamePage />} />
        <Route path="/replay/:id" element={<ReplayPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </BrowserRouter>
  );
}
```

- [ ] **Step 4: Create placeholder pages**

Create stub files for each page (GamePage, ReplayPage, HistoryPage, ConfigPage) with a simple placeholder div.

- [ ] **Step 5: Verify frontend compiles**

```bash
cd C:/Users/zolza/Documents/mcv-ai/frontend
npm run build
# Expected: build succeeds
```

- [ ] **Step 6: Commit**

```bash
git add .
git commit -m "feat: add frontend types, WebSocket hooks, and routing"
```

---

## Task 12: Frontend — Game Page Components

**Files:**
- Create: `frontend/src/pages/GamePage.tsx`
- Create: `frontend/src/components/Tribunal.tsx`
- Create: `frontend/src/components/ScientistPanel.tsx`
- Create: `frontend/src/components/AIPlayerCard.tsx`
- Create: `frontend/src/components/JuryPanel.tsx`
- Create: `frontend/src/components/ThoughtBubble.tsx`
- Create: `frontend/src/components/LiveLog.tsx`
- Create: `frontend/src/components/PhaseIndicator.tsx`
- Create: `frontend/src/components/ExtinctionModal.tsx`

This task is UI-heavy. **Use @frontend-design:frontend-design skill** for distinctive visual design. Each component receives data through props derived from the events stream. The frontend-design skill will generate the full code for each component — provide it with the layout mockups from the spec (Section 5: Interface Web) and the event types from `frontend/src/types/events.ts`.

**Key state derivation from events stream:**
- `currentPhase`: last `game.phase_changed` event's phase
- `scores`: last `jury.score_update` per jury → average per player
- `alivePlayayers`: remove player_id on each `player.eliminated`
- `lastThought[agentId]`: last `agent.thinking` per agent
- `lastMessage[agentId]`: last message-type event per agent
- `extinctionAttempts`: count of `scientist.extinction_proposal` events
- `isTyping[agentId]`: set on `agent.typing`, cleared on next message from same agent
- `extinctionInProgress`: set on `scientist.extinction_proposal`, cleared on `jury.verdict`

- [ ] **Step 1: Build GamePage with Tribunal layout**

GamePage connects to WebSocket, derives game state from events, and renders the Tribunal layout with all sub-components.

- [ ] **Step 2: Build PhaseIndicator component**

Shows current phase, progress bar, timer (for strategy phase).

- [ ] **Step 3: Build ScientistPanel component**

Avatar, name, model, last message, last thought (ThoughtBubble), extinction attempts counter.

- [ ] **Step 4: Build AIPlayerCard component**

Name, model, score bar (0-100), alive/eliminated state, last message, last thought, "typing" indicator. Grayed out when eliminated with animation.

- [ ] **Step 5: Build JuryPanel component**

3 jurors with their thoughts and the score ranking bar chart.

- [ ] **Step 6: Build ThoughtBubble component**

Animated bubble that fades in, shows thought text with 💭 icon.

- [ ] **Step 7: Build LiveLog component**

Scrolling log of all events with timestamps, role icons, and formatted content.

- [ ] **Step 8: Build ExtinctionModal component**

Full-screen modal showing: target, argument, defense, interventions, jury votes (animated one by one), verdict.

- [ ] **Step 9: Verify GamePage renders**

```bash
cd C:/Users/zolza/Documents/mcv-ai/frontend
npm run dev
# Navigate to /game/test and verify layout renders (no data yet)
```

- [ ] **Step 10: Commit**

```bash
git add .
git commit -m "feat: add Game page with tribunal UI components"
```

---

## Task 13: Frontend — Config Page

**Files:**
- Create: `frontend/src/pages/ConfigPage.tsx`

- [ ] **Step 1: Build ConfigPage**

Form with:
- 4 player sections (name, model dropdown, personality dropdown/random)
- 1 scientist section (name, model, personality)
- 3 jury sections (model only)
- Rules section (strategy duration, questions per AI, max extinction proposals)
- "Lancer la partie" button → POST /api/game/create, then POST /api/game/:id/start, then navigate to /game/:id

Fetch providers and personalities from API on mount.

- [ ] **Step 2: Verify form works**

```bash
# Start backend and frontend
# Fill form, click launch
# Verify game is created and redirects to /game/:id
```

- [ ] **Step 3: Commit**

```bash
git add .
git commit -m "feat: add config page for game setup"
```

---

## Task 14: Frontend — History & Replay Pages

**Files:**
- Create: `frontend/src/pages/HistoryPage.tsx`
- Create: `frontend/src/pages/ReplayPage.tsx`

- [ ] **Step 1: Build HistoryPage**

Fetch GET /api/games, display list of past games with:
- Date, result (winner icon), duration, models used, total cost
- Buttons: Replay, Download JSON, View Markdown

- [ ] **Step 2: Build ReplayPage**

Same Tribunal layout as GamePage but with replay controls:
- Play/Pause button
- Speed selector (x1, x2, x5, x10)
- Progress bar with seek
- Skip to phase / Skip to extinction dropdown

Uses useReplayWebSocket hook.

- [ ] **Step 3: Verify replay works**

```bash
# Play a game (or use mock events.json)
# Navigate to /history, click replay
# Verify events replay with correct timing
```

- [ ] **Step 4: Commit**

```bash
git add .
git commit -m "feat: add history and replay pages"
```

---

## Task 15: Integration Test — Full Game

- [ ] **Step 1: Run a full game end-to-end**

```bash
cd C:/Users/zolza/Documents/mcv-ai
source .venv/Scripts/activate

# Start backend
uvicorn backend.main:app --port 8000 &

# Start frontend
cd frontend && npm run dev &

# Open browser to http://localhost:5173
# Configure a game with available models
# Launch and observe the tribunal
```

- [ ] **Step 2: Verify logs are generated**

```bash
ls games/
# Expect: game_YYYY-MM-DD_HHMMSS/ directory with config.json, events.json, replay.md
cat games/*/events.json | python -m json.tool | head -50
```

- [ ] **Step 3: Verify replay works**

Navigate to /history, select the completed game, click Replay.

- [ ] **Step 4: Fix any issues found**

- [ ] **Step 5: Final commit**

```bash
git add .
git commit -m "feat: Tribunal IA v0.1 — complete game loop with UI and replay"
```
