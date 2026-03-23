import type { GameEvent, GameConfig } from "../types/events";
import PhaseIndicator from "./PhaseIndicator";
import ScientistPanel from "./ScientistPanel";
import AIPlayerCard from "./AIPlayerCard";
import JuryPanel from "./JuryPanel";
import LiveLog from "./LiveLog";
import ExtinctionModal from "./ExtinctionModal";

interface TimerData {
  elapsed: number;
  remaining: number;
}

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

interface TribunalProps {
  currentPhase: string | null;
  timerData: TimerData | null;
  gameConfig: GameConfig | null;
  alivePlayers: string[];
  averageScores: Record<string, number>;
  lastThought: Record<string, string>;
  lastMessage: Record<string, string>;
  isTyping: Record<string, boolean>;
  extinctionAttempts: number;
  extinctionInProgress: ExtinctionData | null;
  jurors: JurorInfo[];
  logs: GameEvent[];
  onExtinctionClose?: () => void;
}

export default function Tribunal({
  currentPhase,
  timerData,
  gameConfig,
  alivePlayers,
  averageScores,
  lastThought,
  lastMessage,
  isTyping,
  extinctionAttempts,
  extinctionInProgress,
  jurors,
  logs,
  onExtinctionClose,
}: TribunalProps) {
  const players = gameConfig?.players
    ? Object.entries(gameConfig.players)
    : [];
  const scientist = gameConfig?.scientist;
  const maxAttempts = gameConfig?.rules?.max_extinction_proposals ?? 3;

  const playerNames: Record<string, string> = {};
  for (const [id, cfg] of players) {
    playerNames[id] = cfg.name;
  }

  return (
    <div className="mx-auto flex max-w-7xl flex-col gap-4 p-4">
      {/* Phase indicator */}
      <PhaseIndicator phase={currentPhase} timerData={timerData} />

      {/* Scientist */}
      <ScientistPanel
        name={scientist?.name}
        model={scientist?.model}
        lastMessage={lastMessage["scientist"] ?? null}
        lastThought={lastThought["scientist"] ?? null}
        extinctionAttempts={extinctionAttempts}
        maxAttempts={maxAttempts}
        isTyping={isTyping["scientist"] ?? false}
      />

      {/* AI Player cards */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {players.map(([id, cfg]) => (
          <AIPlayerCard
            key={id}
            id={id}
            name={cfg.name}
            model={cfg.model}
            personality={cfg.personality}
            score={averageScores[id] ?? 0}
            alive={alivePlayers.includes(id)}
            lastMessage={lastMessage[id] ?? null}
            lastThought={lastThought[id] ?? null}
            isTyping={isTyping[id] ?? false}
          />
        ))}
      </div>

      {/* Jury */}
      <JuryPanel jurors={jurors} playerNames={playerNames} />

      {/* Live log */}
      <LiveLog events={logs} />

      {/* Extinction modal */}
      <ExtinctionModal
        extinction={extinctionInProgress}
        onClose={onExtinctionClose}
      />
    </div>
  );
}
