import { motion, AnimatePresence } from "framer-motion";

interface ThoughtBubbleProps {
  thought: string | null | undefined;
  agentName?: string;
}

export default function ThoughtBubble({ thought, agentName }: ThoughtBubbleProps) {
  return (
    <AnimatePresence mode="wait">
      {thought && (
        <motion.div
          key={thought}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="mt-2 rounded-lg bg-white/5 px-3 py-2 text-sm italic text-gray-400 backdrop-blur-sm"
        >
          <span className="mr-1 text-gray-500">
            {agentName ? `${agentName} ` : ""}
          </span>
          <span>{thought}</span>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
