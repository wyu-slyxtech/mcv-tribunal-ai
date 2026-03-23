import type { GameEvent, BrainstormConfig } from "../types/events";
import LiveLog from "./LiveLog";
import ThoughtBubble from "./ThoughtBubble";

interface BrainstormProps {
  config: BrainstormConfig | null;
  currentPhase: string | null;
  currentRound: number;
  maxRounds: number;
  timerData: { elapsed: number; remaining: number } | null;
  lastThought: Record<string, string>;
  lastMessage: Record<string, string>;
  isTyping: Record<string, boolean>;
  votes: Record<string, { vote: string; justification: string; proposed_answer?: string }>;
  gameEnded: boolean;
  endResult: string | null;
  finalAnswer: string | null;
  logs: GameEvent[];
}

export default function Brainstorm({
  config,
  currentPhase,
  currentRound,
  maxRounds,
  timerData,
  lastThought,
  lastMessage,
  isTyping,
  votes,
  gameEnded,
  endResult,
  finalAnswer,
  logs,
}: BrainstormProps) {
  const players = config?.players ?? {};
  const playerIds = Object.keys(players);

  return (
    <div className="mx-auto max-w-6xl px-4 py-6 space-y-6">
      {/* Header: Topic */}
      <div className="rounded-xl border border-purple-800/50 bg-purple-950/20 p-6">
        <div className="text-xs font-semibold uppercase tracking-widest text-purple-400 mb-2">
          Sujet du Brainstorming
        </div>
        <div className="text-lg text-gray-100 leading-relaxed">
          {config?.topic ?? "..."}
        </div>
      </div>

      {/* Phase & Round indicator */}
      <div className="flex items-center justify-between rounded-xl border border-gray-800 bg-gray-900/60 px-6 py-3">
        <div className="flex items-center gap-4">
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
              currentPhase === "brainstorm_debate"
                ? "bg-purple-600/30 text-purple-300"
                : currentPhase === "brainstorm_vote"
                ? "bg-amber-600/30 text-amber-300"
                : gameEnded
                ? "bg-gray-700/30 text-gray-400"
                : "bg-gray-700/30 text-gray-500"
            }`}
          >
            {currentPhase === "brainstorm_debate"
              ? "Debat"
              : currentPhase === "brainstorm_vote"
              ? "Vote"
              : gameEnded
              ? "Termine"
              : "En attente"}
          </span>
          <span className="text-sm text-gray-400">
            Round {currentRound} / {maxRounds}
          </span>
        </div>
        {timerData && currentPhase === "brainstorm_debate" && (
          <span className="font-mono text-sm text-gray-400">
            {Math.floor(timerData.remaining / 60)}:
            {String(timerData.remaining % 60).padStart(2, "0")}
          </span>
        )}
      </div>

      {/* Consensus result banner */}
      {gameEnded && (
        <div
          className={`rounded-xl border p-6 text-center ${
            endResult === "consensus"
              ? "border-green-700/50 bg-green-950/30"
              : "border-orange-700/50 bg-orange-950/30"
          }`}
        >
          <div className="text-2xl font-bold mb-2">
            {endResult === "consensus" ? (
              <span className="text-green-400">Consensus atteint !</span>
            ) : (
              <span className="text-orange-400">
                Pas de consensus (limite atteinte)
              </span>
            )}
          </div>
          {finalAnswer && (
            <div className="mt-4 p-4 rounded-lg bg-gray-900 border border-gray-700 text-left">
              <div className="text-xs font-semibold uppercase text-gray-500 mb-2">
                Reponse finale
              </div>
              <div className="text-gray-200 leading-relaxed whitespace-pre-wrap">
                {finalAnswer}
              </div>
            </div>
          )}
        </div>
      )}

      {/* AI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {playerIds.map((pid) => {
          const player = players[pid];
          const typing = isTyping[pid];
          const message = lastMessage[pid];
          const thought = lastThought[pid];
          const vote = votes[pid];

          return (
            <div
              key={pid}
              className="rounded-xl border border-gray-800 bg-gray-900/60 p-4 flex flex-col"
            >
              {/* Player header */}
              <div className="flex items-center justify-between mb-3">
                <div>
                  <div className="font-bold text-gray-100">{player.name}</div>
                  <div className="text-xs text-gray-500">{player.model}</div>
                </div>
                {vote && (
                  <span
                    className={`px-2 py-1 rounded text-xs font-bold ${
                      vote.vote === "POUR"
                        ? "bg-green-900/50 text-green-400"
                        : "bg-red-900/50 text-red-400"
                    }`}
                  >
                    {vote.vote}
                  </span>
                )}
              </div>

              {player.personality && (
                <div className="text-xs italic text-purple-400/70 mb-2">
                  {player.personality}
                </div>
              )}

              {/* Message */}
              <div className="flex-1">
                {typing && (
                  <div className="text-xs text-purple-400 animate-pulse mb-1">
                    en train de taper...
                  </div>
                )}
                {message && (
                  <div className="rounded-lg bg-gray-800/50 p-3 text-sm text-gray-300 leading-relaxed">
                    {message}
                  </div>
                )}
              </div>

              {/* Thought bubble */}
              <ThoughtBubble thought={thought ?? null} />

              {/* Vote details */}
              {vote?.proposed_answer && (
                <div className="mt-2 rounded-lg bg-green-950/20 border border-green-800/30 p-2 text-xs text-green-300">
                  <span className="font-semibold">Reponse proposee : </span>
                  {vote.proposed_answer}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Live log */}
      <LiveLog events={logs} />
    </div>
  );
}
