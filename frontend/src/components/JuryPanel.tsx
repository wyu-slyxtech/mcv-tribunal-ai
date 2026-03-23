import { motion } from "framer-motion";
import ThoughtBubble from "./ThoughtBubble";

interface JurorInfo {
  id: string;
  name: string;
  model?: string;
  lastThought?: string | null;
  scores?: Record<string, number>;
}

interface JuryPanelProps {
  jurors: JurorInfo[];
  playerNames?: Record<string, string>;
}

function barColor(index: number): string {
  const colors = [
    "bg-cyan-500",
    "bg-teal-500",
    "bg-sky-500",
    "bg-blue-500",
  ];
  return colors[index % colors.length];
}

export default function JuryPanel({ jurors, playerNames }: JuryPanelProps) {
  if (!jurors || jurors.length === 0) {
    return (
      <div className="rounded-xl border border-gray-800 bg-gray-900/80 p-4 text-center text-gray-600">
        En attente du jury...
      </div>
    );
  }

  // Aggregate scores across jurors
  const aggregated: Record<string, number[]> = {};
  for (const juror of jurors) {
    if (!juror.scores) continue;
    for (const [playerId, score] of Object.entries(juror.scores)) {
      if (!aggregated[playerId]) aggregated[playerId] = [];
      aggregated[playerId].push(score);
    }
  }

  const averages: { playerId: string; avg: number }[] = Object.entries(
    aggregated
  )
    .map(([playerId, scores]) => ({
      playerId,
      avg: Math.round(scores.reduce((a, b) => a + b, 0) / scores.length),
    }))
    .sort((a, b) => b.avg - a.avg);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="rounded-xl border border-purple-900/40 bg-gradient-to-r from-gray-900 via-gray-900 to-purple-950/20 p-4"
    >
      <div className="mb-3 text-xs font-semibold uppercase tracking-widest text-purple-400">
        {"\uD83D\uDC68\u200D\u2696\uFE0F"} Jury
      </div>

      {/* Juror cards */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {jurors.map((juror) => (
          <div
            key={juror.id}
            className="rounded-lg border border-purple-900/20 bg-gray-950/50 p-3"
          >
            <div className="flex items-center gap-2">
              <span>{"\uD83D\uDC68\u200D\u2696\uFE0F"}</span>
              <span className="font-semibold text-purple-300">
                {juror.name}
              </span>
            </div>
            {juror.model && (
              <div className="mt-0.5 text-xs text-gray-500">{juror.model}</div>
            )}
            <ThoughtBubble thought={juror.lastThought} />
          </div>
        ))}
      </div>

      {/* Score ranking bar chart */}
      {averages.length > 0 && (
        <div className="mt-4 space-y-2">
          <div className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Scores moyens
          </div>
          {averages.map((item, idx) => (
            <div key={item.playerId} className="flex items-center gap-3">
              <span className="w-24 truncate text-sm text-gray-300">
                {playerNames?.[item.playerId] ?? item.playerId}
              </span>
              <div className="h-3 flex-1 overflow-hidden rounded-full bg-gray-800">
                <motion.div
                  className={`h-full rounded-full ${barColor(idx)}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.min(item.avg, 100)}%` }}
                  transition={{ duration: 0.6, delay: idx * 0.1 }}
                />
              </div>
              <span className="w-8 text-right font-mono text-xs text-gray-400">
                {item.avg}
              </span>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
