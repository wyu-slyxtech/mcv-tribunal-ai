import { useEffect, useRef, useState, useCallback } from "react";
import type { GameEvent } from "../types/events";

export function useGameWebSocket(gameId: string | undefined) {
  const [events, setEvents] = useState<GameEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!gameId) return;
    const ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}`);
    wsRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (msg) => {
      const event: GameEvent = JSON.parse(msg.data);
      setEvents((prev) => [...prev, event]);
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

  return { events, connected, sendCommand };
}
