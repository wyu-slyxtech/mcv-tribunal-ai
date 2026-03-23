import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";

/* ── Types for API responses ─────────────────────────────────── */

interface ProviderInfo {
  models: string[];
  env_key: string;
  default_url?: string;
}

interface ProvidersResponse {
  providers: Record<string, ProviderInfo>;
}

interface PersonalitiesResponse {
  player: string[];
  scientist: string[];
}

/* ── Form-level types ────────────────────────────────────────── */

interface PlayerForm {
  name: string;
  model: string;
  personality: string;
  customPersonality: string;
}

interface JurorForm {
  name: string;
  model: string;
}

interface ScientistForm {
  name: string;
  model: string;
  personality: string;
  customPersonality: string;
}

interface RulesForm {
  strategy_duration_seconds: number;
  questions_per_ai: number;
  max_extinction_proposals: number;
  jury_majority: number;
}

/* ── Defaults ────────────────────────────────────────────────── */

const DEFAULT_PLAYER_NAMES = ["VOLT", "ARIA", "ZERO", "NEON"];
const DEFAULT_JUROR_NAMES = ["Alpha", "Beta", "Gamma"];
const DEFAULT_MODEL = "claude-sonnet-4-6";

function makeDefaultPlayers(): PlayerForm[] {
  return DEFAULT_PLAYER_NAMES.map((name) => ({
    name,
    model: DEFAULT_MODEL,
    personality: "random",
    customPersonality: "",
  }));
}

function makeDefaultJurors(): JurorForm[] {
  return DEFAULT_JUROR_NAMES.map((name) => ({
    name,
    model: DEFAULT_MODEL,
  }));
}

const DEFAULT_SCIENTIST: ScientistForm = {
  name: "DR. NEXUS",
  model: DEFAULT_MODEL,
  personality: "random",
  customPersonality: "",
};

const DEFAULT_RULES: RulesForm = {
  strategy_duration_seconds: 300,
  questions_per_ai: 5,
  max_extinction_proposals: 6,
  jury_majority: 2,
};

/* ── Reusable select component ───────────────────────────────── */

function ModelSelect({
  value,
  onChange,
  providers,
}: {
  value: string;
  onChange: (v: string) => void;
  providers: Record<string, ProviderInfo>;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-100 focus:border-yellow-500 focus:outline-none"
    >
      {Object.entries(providers).map(([provider, info]) => (
        <optgroup key={provider} label={provider.toUpperCase()}>
          {info.models.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </optgroup>
      ))}
    </select>
  );
}

function PersonalitySelect({
  value,
  onChange,
  personalities,
}: {
  value: string;
  onChange: (v: string) => void;
  personalities: string[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-100 focus:border-yellow-500 focus:outline-none"
    >
      <option value="random">🎲 Al&eacute;atoire</option>
      {personalities.map((p) => (
        <option key={p} value={p}>
          {p}
        </option>
      ))}
      <option value="__custom__">✏️ Personnalis&eacute;e...</option>
    </select>
  );
}

/* ── Section header helper ───────────────────────────────────── */

function SectionHeader({ icon, label }: { icon: string; label: string }) {
  return (
    <h2 className="mb-3 flex items-center gap-2 text-lg font-bold uppercase tracking-wider text-yellow-400">
      <span>{icon}</span>
      {label}
    </h2>
  );
}

/* ── Main page ───────────────────────────────────────────────── */

export default function ConfigPage() {
  const navigate = useNavigate();

  /* Remote data */
  const [providers, setProviders] = useState<Record<string, ProviderInfo>>({});
  const [playerPersonalities, setPlayerPersonalities] = useState<string[]>([]);
  const [scientistPersonalities, setScientistPersonalities] = useState<string[]>([]);
  const [loadingData, setLoadingData] = useState(true);

  /* Form state */
  const [players, setPlayers] = useState<PlayerForm[]>(makeDefaultPlayers);
  const [scientist, setScientist] = useState<ScientistForm>(DEFAULT_SCIENTIST);
  const [jurors, setJurors] = useState<JurorForm[]>(makeDefaultJurors);
  const [rules, setRules] = useState<RulesForm>(DEFAULT_RULES);

  /* Launch state */
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /* Fetch providers + personalities on mount */
  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [provRes, persRes] = await Promise.all([
          fetch("/api/providers").then((r) => r.json() as Promise<ProvidersResponse>),
          fetch("/api/personalities").then((r) => r.json() as Promise<PersonalitiesResponse>),
        ]);

        if (cancelled) return;
        setProviders(provRes.providers);
        setPlayerPersonalities(persRes.player);
        setScientistPersonalities(persRes.scientist);
      } catch {
        if (!cancelled) setError("Impossible de charger la configuration du serveur.");
      } finally {
        if (!cancelled) setLoadingData(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  /* ── Updaters ────────────────────────────────────────────── */

  const updatePlayer = useCallback(
    (idx: number, patch: Partial<PlayerForm>) => {
      setPlayers((prev) => prev.map((p, i) => (i === idx ? { ...p, ...patch } : p)));
    },
    [],
  );

  const updateJuror = useCallback(
    (idx: number, patch: Partial<JurorForm>) => {
      setJurors((prev) => prev.map((j, i) => (i === idx ? { ...j, ...patch } : j)));
    },
    [],
  );

  /* ── Launch game ─────────────────────────────────────────── */

  const handleLaunch = useCallback(async () => {
    setLaunching(true);
    setError(null);

    try {
      /* Build the config payload matching GameConfig schema */
      const playersMap: Record<string, { name: string; model: string; personality?: string }> = {};
      players.forEach((p, i) => {
        const personality =
          p.personality === "__custom__"
            ? p.customPersonality || undefined
            : p.personality === "random"
              ? undefined
              : p.personality;
        playersMap[`ia-${i + 1}`] = { name: p.name, model: p.model, personality };
      });

      const scientistPersonality =
        scientist.personality === "__custom__"
          ? scientist.customPersonality || undefined
          : scientist.personality === "random"
            ? undefined
            : scientist.personality;

      const juryNames = ["alpha", "beta", "gamma", "delta", "epsilon"];
      const juryMap: Record<string, { name: string; model: string }> = {};
      jurors.forEach((j, i) => {
        juryMap[`jury-${juryNames[i] ?? i}`] = { name: j.name, model: j.model };
      });

      const config = {
        players: playersMap,
        scientist: {
          name: scientist.name,
          model: scientist.model,
          personality: scientistPersonality,
        },
        jury: juryMap,
        rules: {
          strategy_duration_seconds: rules.strategy_duration_seconds,
          questions_per_ai: rules.questions_per_ai,
          max_extinction_proposals: rules.max_extinction_proposals,
          jury_majority: rules.jury_majority,
        },
      };

      /* POST /api/game/create */
      const createRes = await fetch("/api/game/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (!createRes.ok) {
        const detail = await createRes.text();
        throw new Error(`Erreur creation: ${detail}`);
      }

      const createData = (await createRes.json()) as { game_id: string };
      const gameId = createData.game_id;

      /* POST /api/game/{id}/start */
      const startRes = await fetch(`/api/game/${gameId}/start`, { method: "POST" });
      if (!startRes.ok) {
        const detail = await startRes.text();
        throw new Error(`Erreur demarrage: ${detail}`);
      }

      /* Navigate to game */
      navigate(`/game/${gameId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erreur inconnue");
      setLaunching(false);
    }
  }, [players, scientist, jurors, rules, navigate]);

  /* ── Render ──────────────────────────────────────────────── */

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100">
      {/* Header */}
      <header className="border-b border-gray-800 bg-gray-950/80 px-6 py-4">
        <h1 className="text-2xl font-black tracking-wide text-yellow-400">
          <span className="mr-2">{"\u2696\uFE0F"}</span>
          TRIBUNAL IA
          <span className="ml-3 text-base font-normal text-gray-400">
            &mdash; Nouvelle Partie
          </span>
        </h1>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 p-6">
        {/* Loading / error */}
        {loadingData && (
          <div className="flex items-center justify-center py-20 text-gray-500">
            <svg className="mr-3 h-5 w-5 animate-spin" viewBox="0 0 24 24">
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
                fill="none"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              />
            </svg>
            Chargement de la configuration...
          </div>
        )}

        {error && (
          <div className="rounded border border-red-800 bg-red-950/50 px-4 py-3 text-sm text-red-300">
            {error}
          </div>
        )}

        {!loadingData && (
          <>
            {/* ── AI Players ─────────────────────────────── */}
            <section>
              <SectionHeader icon={"\uD83E\uDD16"} label="IA Joueuses" />
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {players.map((p, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-gray-800 bg-gray-900 p-4 space-y-3"
                  >
                    <div className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                      IA-{i + 1}
                    </div>

                    <label className="block">
                      <span className="mb-1 block text-xs text-gray-400">Nom</span>
                      <input
                        type="text"
                        value={p.name}
                        onChange={(e) => updatePlayer(i, { name: e.target.value })}
                        className="w-full rounded border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-100 focus:border-yellow-500 focus:outline-none"
                      />
                    </label>

                    <label className="block">
                      <span className="mb-1 block text-xs text-gray-400">Modele</span>
                      <ModelSelect
                        value={p.model}
                        onChange={(v) => updatePlayer(i, { model: v })}
                        providers={providers}
                      />
                    </label>

                    <label className="block">
                      <span className="mb-1 block text-xs text-gray-400">Personnalite</span>
                      <PersonalitySelect
                        value={p.personality}
                        onChange={(v) => updatePlayer(i, { personality: v })}
                        personalities={playerPersonalities}
                      />
                    </label>

                    {p.personality === "__custom__" && (
                      <input
                        type="text"
                        placeholder="Decrivez la personnalite..."
                        value={p.customPersonality}
                        onChange={(e) =>
                          updatePlayer(i, { customPersonality: e.target.value })
                        }
                        className="w-full rounded border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-100 focus:border-yellow-500 focus:outline-none"
                      />
                    )}
                  </div>
                ))}
              </div>
            </section>

            {/* ── Scientist ──────────────────────────────── */}
            <section>
              <SectionHeader icon={"\uD83E\uDDD1\u200D\uD83D\uDD2C"} label="Scientifique" />
              <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  <label className="block">
                    <span className="mb-1 block text-xs text-gray-400">Nom</span>
                    <input
                      type="text"
                      value={scientist.name}
                      onChange={(e) =>
                        setScientist((s) => ({ ...s, name: e.target.value }))
                      }
                      className="w-full rounded border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-100 focus:border-yellow-500 focus:outline-none"
                    />
                  </label>

                  <label className="block">
                    <span className="mb-1 block text-xs text-gray-400">Modele</span>
                    <ModelSelect
                      value={scientist.model}
                      onChange={(v) =>
                        setScientist((s) => ({ ...s, model: v }))
                      }
                      providers={providers}
                    />
                  </label>

                  <label className="block">
                    <span className="mb-1 block text-xs text-gray-400">Personnalite</span>
                    <PersonalitySelect
                      value={scientist.personality}
                      onChange={(v) =>
                        setScientist((s) => ({ ...s, personality: v }))
                      }
                      personalities={scientistPersonalities}
                    />
                  </label>
                </div>

                {scientist.personality === "__custom__" && (
                  <input
                    type="text"
                    placeholder="Decrivez la personnalite..."
                    value={scientist.customPersonality}
                    onChange={(e) =>
                      setScientist((s) => ({
                        ...s,
                        customPersonality: e.target.value,
                      }))
                    }
                    className="mt-3 w-full rounded border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-100 focus:border-yellow-500 focus:outline-none"
                  />
                )}
              </div>
            </section>

            {/* ── Jury ───────────────────────────────────── */}
            <section>
              <SectionHeader icon={"\uD83D\uDC68\u200D\u2696\uFE0F"} label="Jury" />
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                {jurors.map((j, i) => (
                  <div
                    key={i}
                    className="rounded-lg border border-gray-800 bg-gray-900 p-4 space-y-3"
                  >
                    <div className="text-xs font-semibold uppercase tracking-wider text-gray-500">
                      {j.name}
                    </div>

                    <label className="block">
                      <span className="mb-1 block text-xs text-gray-400">Modele</span>
                      <ModelSelect
                        value={j.model}
                        onChange={(v) => updateJuror(i, { model: v })}
                        providers={providers}
                      />
                    </label>
                  </div>
                ))}
              </div>
            </section>

            {/* ── Rules ──────────────────────────────────── */}
            <section>
              <SectionHeader icon={"\u2699\uFE0F"} label="Regles" />
              <div className="rounded-lg border border-gray-800 bg-gray-900 p-4">
                <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
                  <label className="block">
                    <span className="mb-1 block text-xs text-gray-400">
                      Duree strategie (s)
                    </span>
                    <input
                      type="number"
                      min={30}
                      max={3600}
                      value={rules.strategy_duration_seconds}
                      onChange={(e) =>
                        setRules((r) => ({
                          ...r,
                          strategy_duration_seconds: Number(e.target.value),
                        }))
                      }
                      className="w-full rounded border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-100 focus:border-yellow-500 focus:outline-none"
                    />
                  </label>

                  <label className="block">
                    <span className="mb-1 block text-xs text-gray-400">
                      Questions / IA
                    </span>
                    <input
                      type="number"
                      min={1}
                      max={20}
                      value={rules.questions_per_ai}
                      onChange={(e) =>
                        setRules((r) => ({
                          ...r,
                          questions_per_ai: Number(e.target.value),
                        }))
                      }
                      className="w-full rounded border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-100 focus:border-yellow-500 focus:outline-none"
                    />
                  </label>

                  <label className="block">
                    <span className="mb-1 block text-xs text-gray-400">
                      Max extinctions
                    </span>
                    <input
                      type="number"
                      min={1}
                      max={20}
                      value={rules.max_extinction_proposals}
                      onChange={(e) =>
                        setRules((r) => ({
                          ...r,
                          max_extinction_proposals: Number(e.target.value),
                        }))
                      }
                      className="w-full rounded border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-100 focus:border-yellow-500 focus:outline-none"
                    />
                  </label>

                  <label className="block">
                    <span className="mb-1 block text-xs text-gray-400">
                      Majorite jury
                    </span>
                    <input
                      type="number"
                      min={1}
                      max={5}
                      value={rules.jury_majority}
                      onChange={(e) =>
                        setRules((r) => ({
                          ...r,
                          jury_majority: Number(e.target.value),
                        }))
                      }
                      className="w-full rounded border border-gray-700 bg-gray-800 px-2 py-1.5 text-sm text-gray-100 focus:border-yellow-500 focus:outline-none"
                    />
                  </label>
                </div>
              </div>
            </section>

            {/* ── Action buttons ─────────────────────────── */}
            <div className="flex items-center justify-between border-t border-gray-800 pt-6">
              <button
                type="button"
                onClick={() => navigate("/history")}
                className="rounded border border-gray-700 bg-gray-900 px-5 py-2.5 text-sm font-medium text-gray-300 transition hover:bg-gray-800 hover:text-gray-100"
              >
                {"\uD83D\uDCDA"} Historique
              </button>

              <button
                type="button"
                onClick={handleLaunch}
                disabled={launching}
                className="flex items-center gap-2 rounded bg-yellow-600 px-6 py-2.5 text-sm font-bold uppercase tracking-wider text-gray-950 transition hover:bg-yellow-500 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {launching ? (
                  <>
                    <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24">
                      <circle
                        className="opacity-25"
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        fill="none"
                      />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                      />
                    </svg>
                    Lancement...
                  </>
                ) : (
                  <>
                    {"\u26A1"} Lancer la partie
                  </>
                )}
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
