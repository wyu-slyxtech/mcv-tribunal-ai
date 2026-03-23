import { useEffect, useRef, useState, useCallback } from "react";
import type { GameEvent } from "../types/events";

export function useGameWebSocket(gameId: string | undefined) {
  const [events, setEvents] = useState<GameEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!gameId) return;

    // Load past events from REST API first (in case we connected mid-game)
    fetch(`/api/game/${gameId}/status`)
      .then((r) => r.json())
      .then((status) => {
        if (status.running || status.status === "completed") {
          // Try to load existing events from the engine's event store
          fetch(`/api/game/${gameId}/events`)
            .then((r) => {
              if (r.ok) return r.json();
              return null;
            })
            .then((data) => {
              if (data?.events && Array.isArray(data.events)) {
                setEvents(data.events as GameEvent[]);
              }
            })
            .catch(() => {});
        }
      })
      .catch(() => {});

    const ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}`);
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (msg) => {
      const event: GameEvent = JSON.parse(msg.data);
      setEvents((prev) => {
        // Deduplicate by event id
        if (event.id && prev.some((e) => e.id === event.id)) return prev;
        return [...prev, event];
      });
    };
    return () => ws.close();
  }, [gameId]);

  return { events, connected };
}

export function useReplayWebSocket(gameId: string | undefined) {
  const [events, setEvents] = useState<GameEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!gameId) return;
    const ws = new WebSocket(`ws://localhost:8000/ws/replay/${gameId}`);
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (msg) => {
      const event: GameEvent = JSON.parse(msg.data);
      setEvents((prev) => [...prev, event]);
    };
    return () => ws.close();
  }, [gameId]);

  const sendCommand = useCallback((command: string, params?: Record<string, any>) => {
    wsRef.current?.send(JSON.stringify({ command, ...params }));
  }, []);

  const clearEvents = useCallback(() => setEvents([]), []);

  return { events, connected, sendCommand, clearEvents };
}
