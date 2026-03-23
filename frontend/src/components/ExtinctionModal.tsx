import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

interface Vote {
  juror_name: string;
  vote: boolean;
  justification?: string;
}

interface ExtinctionData {
  target?: string;
  targetScore?: number;
  argument?: string;
  defense?: string;
  interventions?: Array<{ name: string; content: string }>;
  votes?: Vote[];
  verdict?: boolean | null;
}

interface ExtinctionModalProps {
  extinction: ExtinctionData | null;
  onClose?: () => void;
}

export default function ExtinctionModal({
  extinction,
  onClose,
}: ExtinctionModalProps) {
  const [autoDismiss, setAutoDismiss] = useState(false);

  useEffect(() => {
    if (extinction?.verdict != null) {
      const timer = setTimeout(() => {
        setAutoDismiss(true);
        onClose?.();
      }, 5000);
      return () => clearTimeout(timer);
    }
    setAutoDismiss(false);
  }, [extinction?.verdict, onClose]);

  const isOpen = extinction != null && !autoDismiss;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
          onClick={() => {
            if (extinction.verdict != null) onClose?.();
          }}
        >
          <motion.div
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.9, opacity: 0 }}
            transition={{ duration: 0.3 }}
            className="mx-4 max-h-[85vh] w-full max-w-2xl overflow-y-auto rounded-2xl border border-red-900/50 bg-gray-950 p-6 shadow-2xl shadow-red-900/20"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Title */}
            <div className="mb-4 text-center">
              <span className="text-3xl">{"\u26A1"}</span>
              <h2 className="mt-1 text-2xl font-bold tracking-wide text-red-400">
                TENTATIVE D&apos;EXTINCTION
              </h2>
            </div>

            {/* Target */}
            {extinction.target && (
              <div className="mb-4 rounded-lg border border-red-900/30 bg-red-950/20 p-3 text-center">
                <div className="text-sm text-gray-400">Cible</div>
                <div className="text-xl font-bold text-red-300">
                  {extinction.target}
                </div>
                {extinction.targetScore != null && (
                  <div className="mt-1 font-mono text-sm text-gray-400">
                    Score: {extinction.targetScore}/100
                  </div>
                )}
              </div>
            )}

            {/* Scientist argument */}
            {extinction.argument && (
              <div className="mb-3">
                <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-amber-500">
                  Argument du scientifique
                </div>
                <div className="rounded-lg bg-amber-950/20 p-3 text-sm text-gray-200">
                  {extinction.argument}
                </div>
              </div>
            )}

            {/* Defense */}
            {extinction.defense && (
              <div className="mb-3">
                <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-cyan-500">
                  Defense de la cible
                </div>
                <div className="rounded-lg bg-cyan-950/20 p-3 text-sm text-gray-200">
                  {extinction.defense}
                </div>
              </div>
            )}

            {/* Interventions */}
            {extinction.interventions && extinction.interventions.length > 0 && (
              <div className="mb-3">
                <div className="mb-1 text-xs font-semibold uppercase tracking-wider text-gray-500">
                  Interventions
                </div>
                <div className="space-y-2">
                  {extinction.interventions.map((item, i) => (
                    <div
                      key={i}
                      className="rounded-lg bg-gray-900/50 p-2 text-sm"
                    >
                      <span className="font-semibold text-cyan-400">
                        {item.name}:
                      </span>{" "}
                      <span className="text-gray-300">{item.content}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Votes */}
            {extinction.votes && extinction.votes.length > 0 && (
              <div className="mb-4">
                <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-purple-400">
                  Votes du jury
                </div>
                <div className="space-y-2">
                  {extinction.votes.map((v, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -20 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: i * 0.5 }}
                      className={`rounded-lg border p-3 ${
                        v.vote
                          ? "border-green-900/30 bg-green-950/20"
                          : "border-red-900/30 bg-red-950/20"
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-lg">
                          {v.vote ? "\u2705" : "\u274C"}
                        </span>
                        <span className="font-semibold text-gray-200">
                          {v.juror_name}
                        </span>
                        <span
                          className={`text-sm font-bold ${
                            v.vote ? "text-green-400" : "text-red-400"
                          }`}
                        >
                          {v.vote ? "OUI" : "NON"}
                        </span>
                      </div>
                      {v.justification && (
                        <div className="mt-1 text-sm italic text-gray-400">
                          {v.justification}
                        </div>
                      )}
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Verdict */}
            {extinction.verdict != null && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.5 }}
                className={`rounded-xl p-6 text-center ${
                  extinction.verdict
                    ? "bg-red-950/40 shadow-lg shadow-red-900/30"
                    : "bg-green-950/40 shadow-lg shadow-green-900/30"
                }`}
              >
                <div
                  className={`text-3xl font-black tracking-widest ${
                    extinction.verdict ? "text-red-400" : "text-green-400"
                  }`}
                >
                  {extinction.verdict
                    ? "EXTINCTION VALIDEE"
                    : "EXTINCTION REFUSEE"}
                </div>
              </motion.div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
