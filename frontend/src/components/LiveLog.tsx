import { useEffect, useRef } from "react";
import type { GameEvent } from "../types/events";

interface LiveLogProps {
  events: GameEvent[];
}

function roleIcon(role: string | null): string {
  switch (role) {
    case "player":
      return "\uD83E\uDD16";
    case "scientist":
      return "\uD83E\uDDD1\u200D\uD83D\uDD2C";
    case "jury":
      return "\uD83D\uDC68\u200D\u2696\uFE0F";
    case "brainstormer":
      return "\uD83E\uDDE0";
    default:
      return "\u2699\uFE0F";
  }
}

function formatTimestamp(ts: string): string {
  try {
    const d = new Date(ts);
    return d.toLocaleTimeString("fr-FR", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  } catch {
    return ts;
  }
}

function eventContent(event: GameEvent): string {
  if (event.data?.content) return String(event.data.content);
  if (event.data?.message) return String(event.data.message);
  if (event.data?.phase) return `Phase: ${event.data.phase}`;
  return event.type;
}

export default function LiveLog({ events }: LiveLogProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [events.length]);

  const filtered = events.filter((e) => e.type !== "agent.typing");

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-950/80 backdrop-blur">
      <div className="border-b border-gray-800 px-4 py-2 text-xs font-semibold uppercase tracking-widest text-gray-500">
        Journal en direct
      </div>
      <div
        ref={containerRef}
        className="max-h-56 overflow-y-auto p-3 font-mono text-xs leading-relaxed text-gray-400"
      >
        {filtered.length === 0 && (
          <div className="text-gray-600">En attente des evenements...</div>
        )}
        {filtered.map((event, i) => (
          <div key={event.id ?? i} className="flex gap-2 py-0.5">
            <span className="shrink-0 text-gray-600">
              [{formatTimestamp(event.timestamp)}]
            </span>
            <span className="shrink-0">{roleIcon(event.agent_role)}</span>
            {event.agent_name && (
              <span className="shrink-0 font-semibold text-gray-300">
                {event.agent_name}:
              </span>
            )}
            <span className="break-words">{eventContent(event)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
