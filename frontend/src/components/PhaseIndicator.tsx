import { motion } from "framer-motion";

interface TimerData {
  elapsed: number;
  remaining: number;
}

interface PhaseIndicatorProps {
  phase: string | null | undefined;
  timerData?: TimerData | null;
}

const PHASE_LABELS: Record<string, string> = {
  strategy: "Strategy",
  interrogation: "Interrogatoire",
  defense: "Defense",
  arena: "Arene",
};

const PHASE_ICONS: Record<string, string> = {
  strategy: "\uD83E\uDD2B",
  interrogation: "\uD83D\uDD0D",
  defense: "\uD83D\uDEE1\uFE0F",
  arena: "\u2694\uFE0F",
};

export default function PhaseIndicator({ phase, timerData }: PhaseIndicatorProps) {
  const label = phase ? PHASE_LABELS[phase] ?? phase : "En attente...";
  const icon = phase ? PHASE_ICONS[phase] ?? "\u2699\uFE0F" : "\u23F3";

  const progress =
    timerData && timerData.remaining + timerData.elapsed > 0
      ? timerData.elapsed / (timerData.elapsed + timerData.remaining)
      : 0;

  return (
    <div className="flex items-center gap-4 rounded-xl border border-gray-800 bg-gray-900/80 px-6 py-3 backdrop-blur">
      <span className="text-2xl">{icon}</span>
      <div className="flex-1">
        <div className="text-lg font-semibold tracking-wide text-gray-100">
          {label}
        </div>
        {timerData && phase === "strategy" && (
          <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-gray-800">
            <motion.div
              className="h-full rounded-full bg-gradient-to-r from-cyan-500 to-teal-400"
              initial={{ width: 0 }}
              animate={{ width: `${progress * 100}%` }}
              transition={{ duration: 0.5 }}
            />
          </div>
        )}
      </div>
      {timerData && timerData.remaining > 0 && (
        <span className="font-mono text-sm text-gray-400">
          {Math.ceil(timerData.remaining)}s
        </span>
      )}
    </div>
  );
}
