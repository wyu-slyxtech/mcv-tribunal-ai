import { useMemo, useState, useCallback } from "react";
import { useParams } from "react-router-dom";
import { useGameWebSocket } from "../hooks/useWebSocket";
import type { GameConfig } from "../types/events";
import Tribunal from "../components/Tribunal";

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

export default function GamePage() {
  const { id } = useParams();
  const { events, connected } = useGameWebSocket(id);
  const [extinctionDismissed, setExtinctionDismissed] = useState(0);

  const derived = useMemo(() => {
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

    // Track extinction state
    const extinctions: ExtinctionData[] = [];
    let currentExtinction: ExtinctionData | null = null;

    for (const event of events) {
      const { type, agent_id, data } = event;

      switch (type) {
        case "game.started":
          gameConfig = data?.config as GameConfig ?? null;
          if (gameConfig?.players && !aliveInit) {
            aliveInit = true;
            alivePlayers.length = 0;
            for (const pid of Object.keys(gameConfig.players)) {
              alivePlayers.push(pid);
            }
          }
          break;

        case "game.phase_changed":
          currentPhase = data?.phase as string ?? null;
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
          // Message-type events: update lastMessage
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

    // Build juror info from config + state
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

    // Current extinction in progress (the latest one not yet finalized, or the last completed if any)
    const latestExtinction =
      currentExtinction ??
      (extinctions.length > 0
        ? extinctions[extinctions.length - 1]
        : null);

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
  }, [events]);

  // Only show extinction modal if it hasn't been dismissed
  const showExtinction =
    derived.extinctionInProgress &&
    derived.extinctionAttempts > extinctionDismissed
      ? derived.extinctionInProgress
      : null;

  const handleExtinctionClose = useCallback(() => {
    setExtinctionDismissed(derived.extinctionAttempts);
  }, [derived.extinctionAttempts]);

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Connection status bar */}
      <div
        className={`flex items-center justify-between px-6 py-2 text-xs ${
          connected
            ? "bg-green-950/40 text-green-400"
            : "bg-red-950/40 text-red-400"
        }`}
      >
        <span>
          {connected ? "Connecte" : "Deconnecte"} &mdash; Partie {id}
        </span>
        <span className="font-mono">
          {events.length} evenements
        </span>
      </div>

      {/* Main content */}
      {!derived.gameConfig && events.length === 0 ? (
        <div className="flex min-h-[60vh] items-center justify-center">
          <div className="text-center text-gray-500">
            <div className="mb-2 text-4xl">{"\u23F3"}</div>
            <div className="text-lg">En attente du debut de la partie...</div>
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
        />
      )}
    </div>
  );
}
