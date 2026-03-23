import { motion } from "framer-motion";
import ThoughtBubble from "./ThoughtBubble";

interface AIPlayerCardProps {
  id: string;
  name: string;
  model?: string;
  score?: number;
  alive?: boolean;
  lastMessage?: string | null;
  lastThought?: string | null;
  isTyping?: boolean;
  personality?: string;
}

function scoreColor(score: number): string {
  if (score < 30) return "from-green-500 to-green-400";
  if (score < 60) return "from-yellow-500 to-yellow-400";
  if (score < 80) return "from-orange-500 to-orange-400";
  return "from-red-500 to-red-400";
}

function scoreBorderColor(score: number): string {
  if (score < 30) return "border-green-700/40";
  if (score < 60) return "border-yellow-700/40";
  if (score < 80) return "border-orange-700/40";
  return "border-red-700/40";
}

export default function AIPlayerCard({
  name,
  model,
  score = 0,
  alive = true,
  lastMessage,
  lastThought,
  isTyping,
  personality,
}: AIPlayerCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={
        alive
          ? { opacity: 1, scale: 1 }
          : { opacity: 0.45, scale: 0.97 }
      }
      transition={{ duration: 0.5, ease: "easeOut" }}
      className={`relative flex flex-col rounded-xl border p-4 transition-colors ${
        alive
          ? `border-cyan-800/40 bg-gray-900/80`
          : `border-red-900/40 bg-gray-950/80`
      }`}
    >
      {/* Eliminated badge */}
      {!alive && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          className="absolute -right-2 -top-2 z-10 rounded-full bg-red-600 px-3 py-1 text-xs font-bold uppercase tracking-wider text-white shadow-lg shadow-red-900/40"
        >
          ETEINTE
        </motion.div>
      )}

      {/* Header */}
      <div className="flex items-center gap-2">
        <span className="text-xl">{"\uD83E\uDD16"}</span>
        <div className="min-w-0 flex-1">
          <div
            className={`font-bold ${
              alive ? "text-cyan-300" : "text-gray-500 line-through"
            }`}
          >
            {name}
          </div>
          {model && (
            <div className="text-xs text-gray-500">{model}</div>
          )}
        </div>
      </div>

      {/* Personality */}
      {personality && (
        <div className="mt-1 text-xs italic text-cyan-700">{personality}</div>
      )}

      {/* Score bar */}
      <div className="mt-3">
        <div className="mb-1 flex items-center justify-between text-xs">
          <span className="text-gray-500">Conscience</span>
          <span
            className={`font-mono font-bold ${
              score >= 80
                ? "text-red-400"
                : score >= 60
                  ? "text-orange-400"
                  : score >= 30
                    ? "text-yellow-400"
                    : "text-green-400"
            }`}
          >
            {score}
          </span>
        </div>
        <div
          className={`h-2 overflow-hidden rounded-full border ${scoreBorderColor(score)} bg-gray-800`}
        >
          <motion.div
            className={`h-full rounded-full bg-gradient-to-r ${scoreColor(score)}`}
            initial={{ width: 0 }}
            animate={{ width: `${Math.min(score, 100)}%` }}
            transition={{ duration: 0.6, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Last message */}
      {lastMessage && (
        <div className="mt-3 rounded-lg bg-gray-800/50 px-3 py-2 text-sm text-gray-300">
          {lastMessage}
        </div>
      )}

      {/* Typing indicator */}
      {isTyping && !lastMessage && (
        <div className="mt-3 text-sm italic text-cyan-600/60">
          en train de taper...
        </div>
      )}

      {/* Thought */}
      <ThoughtBubble thought={lastThought} />
    </motion.div>
  );
}
