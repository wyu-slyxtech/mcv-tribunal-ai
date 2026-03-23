import { useEffect, useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import type { GameSummary } from "../types/events";

export default function HistoryPage() {
  const navigate = useNavigate();
  const [games, setGames] = useState<GameSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);

  const fetchGames = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/games");
      if (!res.ok) throw new Error(`Erreur ${res.status}`);
      const data = await res.json();
      setGames(data.games ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur inconnue");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchGames();
  }, [fetchGames]);

  const handleDelete = async (gameId: string) => {
    setDeletingId(gameId);
    try {
      const res = await fetch(`/api/game/${gameId}`, { method: "DELETE" });
      if (!res.ok) throw new Error(`Erreur ${res.status}`);
      setConfirmDeleteId(null);
      await fetchGames();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur lors de la suppression");
    } finally {
      setDeletingId(null);
    }
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return "Date inconnue";
    try {
      return new Date(iso).toLocaleString("fr-FR", {
        day: "numeric",
        month: "long",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  const resultLabel = (result: GameSummary["result"]) => {
    if (!result || !result.winner) return { text: "Partie terminee", icon: "\u2753" };
    if (result.winner === "scientist") {
      return { text: "Victoire Scientifique", icon: "\uD83C\uDFC6" };
    }
    if (result.winner === "ia") {
      return { text: "Victoire des IA", icon: "\uD83E\uDD16" };
    }
    return { text: `Victoire: ${result.winner}`, icon: "\uD83C\uDFC6" };
  };

  const formatCost = (cost: number) => {
    if (cost === 0) return "$0.00";
    if (cost < 0.01) return `$${cost.toFixed(4)}`;
    return `$${cost.toFixed(2)}`;
  };

  const formatTokens = (tokens: number) => {
    if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(1)}M`;
    if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(0)}K`;
    return String(tokens);
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900/80 backdrop-blur">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <h1 className="text-2xl font-bold tracking-wide">
            Historique des Parties
          </h1>
          <button
            onClick={() => navigate("/")}
            className="rounded-lg bg-cyan-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-cyan-500"
          >
            Nouvelle Partie
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="mx-auto max-w-5xl px-6 py-8">
        {/* Error banner */}
        {error && (
          <div className="mb-6 rounded-lg border border-red-800 bg-red-950/40 px-4 py-3 text-sm text-red-400">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-4 underline hover:text-red-300"
            >
              Fermer
            </button>
          </div>
        )}

        {/* Loading */}
        {loading && (
          <div className="flex min-h-[40vh] items-center justify-center">
            <div className="text-center text-gray-500">
              <div className="mb-2 text-4xl">{"\u23F3"}</div>
              <div className="text-lg">Chargement...</div>
            </div>
          </div>
        )}

        {/* Empty state */}
        {!loading && games.length === 0 && !error && (
          <div className="flex min-h-[40vh] items-center justify-center">
            <div className="text-center text-gray-500">
              <div className="mb-3 text-5xl">{"\uD83C\uDFAE"}</div>
              <div className="text-lg font-medium">Aucune partie jouee</div>
              <div className="mt-2 text-sm text-gray-600">
                Lancez une nouvelle partie pour commencer
              </div>
              <button
                onClick={() => navigate("/")}
                className="mt-6 rounded-lg bg-cyan-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-cyan-500"
              >
                Nouvelle Partie
              </button>
            </div>
          </div>
        )}

        {/* Game list */}
        {!loading && games.length > 0 && (
          <div className="flex flex-col gap-4">
            {games.map((game) => {
              const { text: resultText, icon: resultIcon } = resultLabel(game.result);
              const isDeleting = deletingId === game.game_id;
              const isConfirming = confirmDeleteId === game.game_id;

              return (
                <div
                  key={game.game_id}
                  className="rounded-xl border border-gray-800 bg-gray-900/70 p-5 transition hover:border-gray-700"
                >
                  {/* Title row */}
                  <div className="mb-3 flex items-start justify-between gap-4">
                    <h2 className="font-mono text-sm text-gray-400">
                      {game.game_id}
                    </h2>
                    {/* Delete button */}
                    <div className="flex items-center gap-2">
                      {isConfirming ? (
                        <>
                          <span className="text-xs text-red-400">Supprimer ?</span>
                          <button
                            onClick={() => void handleDelete(game.game_id)}
                            disabled={isDeleting}
                            className="rounded bg-red-600 px-2 py-1 text-xs font-medium text-white transition hover:bg-red-500 disabled:opacity-50"
                          >
                            {isDeleting ? "..." : "Oui"}
                          </button>
                          <button
                            onClick={() => setConfirmDeleteId(null)}
                            className="rounded bg-gray-700 px-2 py-1 text-xs font-medium text-gray-300 transition hover:bg-gray-600"
                          >
                            Non
                          </button>
                        </>
                      ) : (
                        <button
                          onClick={() => setConfirmDeleteId(game.game_id)}
                          className="rounded p-1 text-gray-600 transition hover:bg-gray-800 hover:text-red-400"
                          title="Supprimer"
                        >
                          <svg
                            className="h-4 w-4"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                            />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Info row */}
                  <div className="mb-4 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm">
                    <span>
                      {resultIcon} {resultText}
                    </span>
                    <span className="text-gray-400">
                      {formatDate(game.started_at)}
                    </span>
                  </div>

                  {/* Models */}
                  {game.models_used.length > 0 && (
                    <div className="mb-3 text-sm text-gray-400">
                      Modeles: {game.models_used.join(", ")}
                    </div>
                  )}

                  {/* Stats */}
                  <div className="mb-4 flex flex-wrap gap-x-6 gap-y-1 text-sm text-gray-500">
                    <span>
                      Cout: {formatCost(game.total_cost)}
                    </span>
                    <span>
                      {formatTokens(game.total_tokens)} tokens
                    </span>
                    {game.result?.eliminated && game.result.eliminated.length > 0 && (
                      <span>
                        {game.result.eliminated.length} elimine(s)
                      </span>
                    )}
                    {game.result?.survivors && game.result.survivors.length > 0 && (
                      <span>
                        {game.result.survivors.length} survivant(s)
                      </span>
                    )}
                  </div>

                  {/* Action buttons */}
                  <div className="flex flex-wrap gap-3">
                    <button
                      onClick={() => navigate(`/replay/${game.game_id}`)}
                      className="rounded-lg bg-cyan-600/20 px-4 py-2 text-sm font-medium text-cyan-400 transition hover:bg-cyan-600/30"
                    >
                      Replay
                    </button>
                    <a
                      href={`/api/game/${game.game_id}/events`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="rounded-lg bg-gray-800 px-4 py-2 text-sm font-medium text-gray-300 transition hover:bg-gray-700"
                    >
                      JSON
                    </a>
                    <button
                      onClick={() =>
                        window.open(
                          `/api/game/${game.game_id}/stats`,
                          "_blank"
                        )
                      }
                      className="rounded-lg bg-gray-800 px-4 py-2 text-sm font-medium text-gray-300 transition hover:bg-gray-700"
                    >
                      Stats
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
