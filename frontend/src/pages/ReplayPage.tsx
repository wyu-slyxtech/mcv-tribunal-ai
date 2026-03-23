import { useMemo, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useReplayWebSocket } from "../hooks/useWebSocket";
import type { GameConfig, GameEvent } from "../types/events";
import Tribunal from "../components/Tribunal";

// ---------- Shared types (same as GamePage) ----------

interface ExtinctionData {
  target?: string;
  targetScore?: number;
  argument?: string;
  defense?: string;
  interventions?: Array<{ name: string; content: string }>;
  votes?: Array<{ juror_name: string; vote: boolean; justification?: string }>;
  verdict?: boolean | null;
}

interface JurorInfo {
  id: string;
  name: string;
  model?: string;
  lastThought?: string | null;
  scores?: Record<string, number>;
}

// ---------- State derivation (same logic as GamePage) ----------

function deriveGameState(events: GameEvent[]) {
  let currentPhase: string | null = null;
  let gameConfig: GameConfig | null = null;
  const alivePlayers: string[] = [];
  let aliveInit = false;
  const scores: Record<string, Record<string, number>> = {};
  const lastThought: Record<string, string> = {};
  const lastMessage: Record<string, string> = {};
  const isTyping: Record<string, boolean> = {};
  let extinctionAttempts = 0;
  let timerData: { elapsed: number; remaining: number } | null = null;

  const extinctions: ExtinctionData[] = [];
  let currentExtinction: ExtinctionData | null = null;

  for (const event of events) {
    const { type, agent_id, data } = event;

    switch (type) {
      case "game.started":
        gameConfig = (data?.config as GameConfig) ?? null;
        if (gameConfig?.players && !aliveInit) {
          aliveInit = true;
          alivePlayers.length = 0;
          for (const pid of Object.keys(gameConfig.players)) {
            alivePlayers.push(pid);
          }
        }
        break;

      case "game.phase_changed":
        currentPhase = (data?.phase as string) ?? null;
        break;

      case "game.timer":
        timerData = {
          elapsed: (data?.elapsed as number) ?? 0,
          remaining: (data?.remaining as number) ?? 0,
        };
        break;

      case "jury.score_update":
        if (agent_id && data?.scores) {
          scores[agent_id] = {
            ...(scores[agent_id] ?? {}),
            ...(data.scores as Record<string, number>),
          };
        }
        break;

      case "agent.thinking":
        if (agent_id) {
          lastThought[agent_id] = String(data?.content ?? "");
          isTyping[agent_id] = false;
        }
        break;

      case "agent.typing":
        if (agent_id) {
          isTyping[agent_id] = true;
        }
        break;

      case "player.eliminated":
        if (data?.player_id) {
          const idx = alivePlayers.indexOf(data.player_id as string);
          if (idx !== -1) alivePlayers.splice(idx, 1);
        }
        break;

      case "scientist.extinction_proposal":
        extinctionAttempts++;
        currentExtinction = {
          target: data?.target_name as string | undefined,
          targetScore: data?.target_score as number | undefined,
          argument: data?.argument as string | undefined,
        };
        break;

      case "player.defense":
        if (currentExtinction) {
          currentExtinction.defense = data?.content as string | undefined;
        }
        break;

      case "player.intervention":
        if (currentExtinction) {
          if (!currentExtinction.interventions) {
            currentExtinction.interventions = [];
          }
          currentExtinction.interventions.push({
            name: (event.agent_name ?? "IA") as string,
            content: String(data?.content ?? ""),
          });
        }
        break;

      case "jury.vote":
        if (currentExtinction) {
          if (!currentExtinction.votes) {
            currentExtinction.votes = [];
          }
          currentExtinction.votes.push({
            juror_name: (event.agent_name ?? "Jure") as string,
            vote: Boolean(data?.vote),
            justification: data?.justification as string | undefined,
          });
        }
        break;

      case "jury.verdict":
        if (currentExtinction) {
          currentExtinction.verdict = Boolean(data?.approved);
          extinctions.push(currentExtinction);
          currentExtinction = null;
        }
        break;

      default:
        if (
          agent_id &&
          (type.includes("message") ||
            type.includes("question") ||
            type.includes("answer") ||
            type.includes("response") ||
            type.includes("statement") ||
            type === "scientist.question" ||
            type === "player.answer" ||
            type === "player.statement" ||
            type === "scientist.statement")
        ) {
          lastMessage[agent_id] = String(data?.content ?? "");
          isTyping[agent_id] = false;
        }
        break;
    }
  }

  // Compute average scores per player
  const averageScores: Record<string, number> = {};
  const playerScoreAcc: Record<string, number[]> = {};
  for (const jurorScores of Object.values(scores)) {
    for (const [playerId, score] of Object.entries(jurorScores)) {
      if (!playerScoreAcc[playerId]) playerScoreAcc[playerId] = [];
      playerScoreAcc[playerId].push(score);
    }
  }
  for (const [pid, arr] of Object.entries(playerScoreAcc)) {
    averageScores[pid] = Math.round(
      arr.reduce((a, b) => a + b, 0) / arr.length
    );
  }

  // Build juror info
  const jurors: JurorInfo[] = [];
  if (gameConfig?.jury) {
    for (const [jid, jcfg] of Object.entries(gameConfig.jury)) {
      jurors.push({
        id: jid,
        name: jcfg.name,
        model: jcfg.model,
        lastThought: lastThought[jid] ?? null,
        scores: scores[jid] ?? undefined,
      });
    }
  }

  const latestExtinction =
    currentExtinction ??
    (extinctions.length > 0 ? extinctions[extinctions.length - 1] : null);

  return {
    currentPhase,
    gameConfig,
    alivePlayers: [...alivePlayers],
    averageScores,
    lastThought,
    lastMessage,
    isTyping,
    extinctionAttempts,
    timerData,
    jurors,
    extinctionInProgress: latestExtinction,
  };
}

// ---------- Replay speed options ----------

const SPEED_OPTIONS = [1, 2, 5, 10] as const;

// ---------- Phase list for jump dropdown ----------

const PHASE_LIST = [
  { value: "strategy", label: "Strategy" },
  { value: "interrogation", label: "Interrogatoire" },
  { value: "defense", label: "Defense" },
  { value: "arena", label: "Arene" },
];

// ---------- ReplayControls component ----------

interface ReplayControlsProps {
  eventCount: number;
  totalEvents: number | null;
  playing: boolean;
  speed: number;
  onPlay: () => void;
  onPause: () => void;
  onSpeedChange: (s: number) => void;
  onSkipToStart: () => void;
  onSkipToEnd: () => void;
  onStepBack: () => void;
  onStepForward: () => void;
  onSkipToPhase: (phase: string) => void;
  onSkipToExtinction: (n: number) => void;
  extinctionCount: number;
}

function ReplayControls({
  eventCount,
  totalEvents,
  playing,
  speed,
  onPlay,
  onPause,
  onSpeedChange,
  onSkipToStart,
  onSkipToEnd,
  onStepBack,
  onStepForward,
  onSkipToPhase,
  onSkipToExtinction,
  extinctionCount,
}: ReplayControlsProps) {
  const progressPercent =
    totalEvents && totalEvents > 0
      ? Math.min(100, (eventCount / totalEvents) * 100)
      : 0;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900/80 p-4 backdrop-blur">
      {/* Transport controls row */}
      <div className="flex flex-wrap items-center gap-3">
        {/* Playback buttons */}
        <div className="flex items-center gap-1">
          <button
            onClick={onSkipToStart}
            className="rounded p-2 text-gray-400 transition hover:bg-gray-800 hover:text-gray-200"
            title="Debut"
          >
            {"\u23EE"}
          </button>
          <button
            onClick={onStepBack}
            className="rounded p-2 text-gray-400 transition hover:bg-gray-800 hover:text-gray-200"
            title="Precedent"
          >
            {"\u23EA"}
          </button>
          <button
            onClick={playing ? onPause : onPlay}
            className="rounded-lg bg-cyan-600/20 px-3 py-2 text-lg text-cyan-400 transition hover:bg-cyan-600/30"
            title={playing ? "Pause" : "Lecture"}
          >
            {playing ? "\u23F8" : "\u25B6"}
          </button>
          <button
            onClick={onStepForward}
            className="rounded p-2 text-gray-400 transition hover:bg-gray-800 hover:text-gray-200"
            title="Suivant"
          >
            {"\u23E9"}
          </button>
          <button
            onClick={onSkipToEnd}
            className="rounded p-2 text-gray-400 transition hover:bg-gray-800 hover:text-gray-200"
            title="Fin"
          >
            {"\u23ED"}
          </button>
        </div>

        {/* Speed buttons */}
        <div className="flex items-center gap-1 border-l border-gray-800 pl-3">
          {SPEED_OPTIONS.map((s) => (
            <button
              key={s}
              onClick={() => onSpeedChange(s)}
              className={`rounded px-2 py-1 text-xs font-medium transition ${
                speed === s
                  ? "bg-cyan-600 text-white"
                  : "bg-gray-800 text-gray-400 hover:bg-gray-700 hover:text-gray-200"
              }`}
            >
              x{s}
            </button>
          ))}
        </div>

        {/* REPLAY badge */}
        <span className="ml-auto rounded bg-amber-600/20 px-2 py-1 text-xs font-bold tracking-wider text-amber-400">
          REPLAY
        </span>
      </div>

      {/* Progress bar */}
      <div className="mt-3">
        <div className="mb-1 flex items-center justify-between text-xs text-gray-500">
          <span>
            {eventCount}
            {totalEvents !== null ? ` / ${totalEvents}` : ""} evenements
          </span>
          <span>{Math.round(progressPercent)}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-gray-800">
          <div
            className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-teal-400 transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      </div>

      {/* Jump-to controls */}
      <div className="mt-3 flex flex-wrap items-center gap-3 text-sm">
        <label className="text-gray-500">Aller a:</label>
        <select
          onChange={(e) => {
            if (e.target.value) onSkipToPhase(e.target.value);
            e.target.value = "";
          }}
          defaultValue=""
          className="rounded bg-gray-800 px-2 py-1 text-sm text-gray-300 outline-none focus:ring-1 focus:ring-cyan-500"
        >
          <option value="" disabled>
            Phase...
          </option>
          {PHASE_LIST.map((p) => (
            <option key={p.value} value={p.value}>
              {p.label}
            </option>
          ))}
        </select>
        {extinctionCount > 0 && (
          <select
            onChange={(e) => {
              if (e.target.value) onSkipToExtinction(Number(e.target.value));
              e.target.value = "";
            }}
            defaultValue=""
            className="rounded bg-gray-800 px-2 py-1 text-sm text-gray-300 outline-none focus:ring-1 focus:ring-cyan-500"
          >
            <option value="" disabled>
              Extinction...
            </option>
            {Array.from({ length: extinctionCount }, (_, i) => (
              <option key={i + 1} value={i + 1}>
                Extinction #{i + 1}
              </option>
            ))}
          </select>
        )}
      </div>
    </div>
  );
}

// ---------- ReplayPage ----------

export default function ReplayPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { events, connected, sendCommand } = useReplayWebSocket(id);

  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [extinctionDismissed, setExtinctionDismissed] = useState(0);

  // Try to get total event count from initial metadata if available
  const totalEvents = useMemo(() => {
    for (const ev of events) {
      if (ev.type === "replay.metadata" && ev.data?.total_events) {
        return ev.data.total_events as number;
      }
    }
    return null;
  }, [events]);

  const derived = useMemo(() => deriveGameState(events), [events]);

  const showExtinction =
    derived.extinctionInProgress &&
    derived.extinctionAttempts > extinctionDismissed
      ? derived.extinctionInProgress
      : null;

  const handleExtinctionClose = useCallback(() => {
    setExtinctionDismissed(derived.extinctionAttempts);
  }, [derived.extinctionAttempts]);

  const handlePlay = useCallback(() => {
    sendCommand("play");
    setPlaying(true);
  }, [sendCommand]);

  const handlePause = useCallback(() => {
    sendCommand("pause");
    setPlaying(false);
  }, [sendCommand]);

  const handleSpeedChange = useCallback(
    (s: number) => {
      sendCommand("speed", { value: s });
      setSpeed(s);
    },
    [sendCommand]
  );

  const handleSkipToStart = useCallback(() => {
    sendCommand("skip_to", { target: "start" });
  }, [sendCommand]);

  const handleSkipToEnd = useCallback(() => {
    sendCommand("skip_to", { target: "end" });
  }, [sendCommand]);

  const handleStepBack = useCallback(() => {
    sendCommand("step", { direction: "back" });
  }, [sendCommand]);

  const handleStepForward = useCallback(() => {
    sendCommand("step", { direction: "forward" });
  }, [sendCommand]);

  const handleSkipToPhase = useCallback(
    (phase: string) => {
      sendCommand("skip_to", { target: `phase:${phase}` });
    },
    [sendCommand]
  );

  const handleSkipToExtinction = useCallback(
    (n: number) => {
      sendCommand("skip_to", { target: `extinction:${n}` });
    },
    [sendCommand]
  );

  const replayControls = (
    <ReplayControls
      eventCount={events.length}
      totalEvents={totalEvents}
      playing={playing}
      speed={speed}
      onPlay={handlePlay}
      onPause={handlePause}
      onSpeedChange={handleSpeedChange}
      onSkipToStart={handleSkipToStart}
      onSkipToEnd={handleSkipToEnd}
      onStepBack={handleStepBack}
      onStepForward={handleStepForward}
      onSkipToPhase={handleSkipToPhase}
      onSkipToExtinction={handleSkipToExtinction}
      extinctionCount={derived.extinctionAttempts}
    />
  );

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Connection status bar */}
      <div
        className={`flex items-center justify-between px-6 py-2 text-xs ${
          connected
            ? "bg-amber-950/40 text-amber-400"
            : "bg-red-950/40 text-red-400"
        }`}
      >
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate("/history")}
            className="rounded bg-gray-800 px-2 py-1 text-xs text-gray-400 transition hover:bg-gray-700 hover:text-gray-200"
          >
            Historique
          </button>
          <span>
            {connected ? "REPLAY" : "Deconnecte"} &mdash; Partie {id}
          </span>
        </div>
        <span className="font-mono">{events.length} evenements</span>
      </div>

      {/* Main content */}
      {!derived.gameConfig && events.length === 0 ? (
        <div className="flex min-h-[60vh] items-center justify-center">
          <div className="text-center text-gray-500">
            <div className="mb-2 text-4xl">{"\u23F3"}</div>
            <div className="text-lg">Chargement du replay...</div>
            <div className="mt-1 text-sm text-gray-600">
              {connected
                ? "Connecte au serveur, en attente des evenements"
                : "Connexion au serveur..."}
            </div>
          </div>
        </div>
      ) : (
        <Tribunal
          currentPhase={derived.currentPhase}
          timerData={derived.timerData}
          gameConfig={derived.gameConfig}
          alivePlayers={derived.alivePlayers}
          averageScores={derived.averageScores}
          lastThought={derived.lastThought}
          lastMessage={derived.lastMessage}
          isTyping={derived.isTyping}
          extinctionAttempts={derived.extinctionAttempts}
          extinctionInProgress={showExtinction}
          jurors={derived.jurors}
          logs={events}
          onExtinctionClose={handleExtinctionClose}
          replayControls={replayControls}
        />
      )}
    </div>
  );
}
