import { motion } from "framer-motion";
import ThoughtBubble from "./ThoughtBubble";

interface ScientistPanelProps {
  name?: string;
  model?: string;
  lastMessage?: string | null;
  lastThought?: string | null;
  extinctionAttempts?: number;
  maxAttempts?: number;
  isTyping?: boolean;
}

export default function ScientistPanel({
  name,
  model,
  lastMessage,
  lastThought,
  extinctionAttempts = 0,
  maxAttempts = 3,
  isTyping,
}: ScientistPanelProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="rounded-xl border border-amber-900/40 bg-gradient-to-r from-gray-900 via-gray-900 to-amber-950/20 p-4"
    >
      <div className="flex items-start gap-4">
        {/* Avatar */}
        <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-amber-900/30 text-2xl">
          {"\uD83E\uDDD1\u200D\uD83D\uDD2C"}
        </div>

        {/* Info */}
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-amber-300">
              {name ?? "Scientifique"}
            </span>
            {model && (
              <span className="rounded bg-amber-900/30 px-2 py-0.5 text-xs text-amber-400">
                {model}
              </span>
            )}
          </div>

          {/* Last message */}
          {lastMessage && (
            <div className="mt-2 rounded-lg border border-amber-900/20 bg-amber-950/20 px-3 py-2 text-sm text-gray-200">
              {lastMessage}
            </div>
          )}

          {/* Typing indicator */}
          {isTyping && !lastMessage && (
            <div className="mt-2 text-sm italic text-amber-400/60">
              en train de taper...
            </div>
          )}

          {/* Thought */}
          <ThoughtBubble thought={lastThought} />
        </div>

        {/* Extinction attempts */}
        <div className="shrink-0 text-right">
          <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">
            Extinctions
          </div>
          <div className="flex gap-1">
            {Array.from({ length: maxAttempts }).map((_, i) => (
              <span key={i} className="text-lg">
                {i < extinctionAttempts ? "\u26A1" : "\u2B1C"}
              </span>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
