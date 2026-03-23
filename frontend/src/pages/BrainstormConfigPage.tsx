import { useState, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";

interface ProviderInfo {
  models: string[];
  env_key: string;
}

interface PlayerForm {
  name: string;
  model: string;
  personality: string;
  customPersonality: string;
}

const ALL_NAMES = ["ALPHA", "BETA", "GAMMA", "DELTA", "EPSILON", "ZETA", "ETA", "THETA"];
const BRAINSTORM_PERSONALITIES = [
  "analytique",
  "créatif",
  "pragmatique",
  "provocateur",
  "synthétiseur",
  "devil's advocate",
  "optimiste",
  "critique",
];

export default function BrainstormConfigPage() {
  const navigate = useNavigate();
  const [allModels, setAllModels] = useState<string[]>([]);
  const [topic, setTopic] = useState("");
  const [launching, setLaunching] = useState(false);

  const [numPlayers, setNumPlayers] = useState(4);

  const makePlayer = (name: string): PlayerForm => ({
    name,
    model: "",
    personality: "random",
    customPersonality: "",
  });

  const [players, setPlayers] = useState<PlayerForm[]>(
    ALL_NAMES.slice(0, 4).map(makePlayer)
  );

  const [rules, setRules] = useState({
    debate_round_seconds: 180,
    max_rounds: 5,
    consensus_threshold: 3,
    sub_rounds_per_debate: 3,
  });

  useEffect(() => {
    fetch("/api/providers")
      .then((r) => r.json())
      .then((data: { providers: Record<string, ProviderInfo> }) => {
        const models: string[] = [];
        for (const info of Object.values(data.providers)) {
          models.push(...info.models);
        }
        setAllModels(models);
        if (models.length > 0) {
          setPlayers((prev) =>
            prev.map((p) => ({ ...p, model: p.model || models[0] }))
          );
        }
      })
      .catch(console.error);
  }, []);

  const handleNumPlayersChange = useCallback(
    (n: number) => {
      setNumPlayers(n);
      setPlayers((prev) => {
        if (n > prev.length) {
          const extra = ALL_NAMES.slice(prev.length, n).map(makePlayer);
          const withModels = extra.map((p) => ({
            ...p,
            model: allModels[0] || "",
          }));
          return [...prev, ...withModels];
        }
        return prev.slice(0, n);
      });
      // Ajuster le seuil de consensus si nécessaire
      setRules((r) => ({
        ...r,
        consensus_threshold: Math.min(r.consensus_threshold, n),
      }));
    },
    [allModels]
  );

  const updatePlayer = useCallback(
    (index: number, field: keyof PlayerForm, value: string) => {
      setPlayers((prev) => {
        const next = [...prev];
        next[index] = { ...next[index], [field]: value };
        return next;
      });
    },
    []
  );

  const handleLaunch = async () => {
    if (!topic.trim()) return;
    setLaunching(true);

    const playersConfig: Record<string, any> = {};
    players.forEach((p, i) => {
      const personality =
        p.personality === "custom"
          ? p.customPersonality
          : p.personality === "random"
          ? null
          : p.personality;
      playersConfig[`ia-${i + 1}`] = {
        name: p.name,
        model: p.model,
        personality,
      };
    });

    const config = {
      mode: "brainstorm",
      topic: topic.trim(),
      players: playersConfig,
      rules,
    };

    try {
      const res = await fetch("/api/game/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });
      const data = await res.json();
      const gameId = data.game_id;

      await fetch(`/api/game/${gameId}/start`, { method: "POST" });
      navigate(`/game/${gameId}`);
    } catch (err) {
      console.error(err);
      setLaunching(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-4 mb-8">
          <button
            onClick={() => navigate("/")}
            className="text-gray-500 hover:text-gray-300 transition-colors"
          >
            {"← Retour"}
          </button>
          <h1 className="text-3xl font-bold text-purple-400">
            {"🧠"} Brainstorming IA
          </h1>
        </div>

        {/* Topic */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-3 text-gray-300">
            Sujet / Question
          </h2>
          <textarea
            value={topic}
            onChange={(e) => setTopic(e.target.value)}
            placeholder="Posez votre question ou décrivez le sujet à explorer..."
            className="w-full h-32 px-4 py-3 rounded-xl bg-gray-900 border border-gray-700 text-gray-100 placeholder-gray-600 focus:border-purple-500 focus:outline-none resize-none"
          />
        </section>

        {/* Players */}
        <section className="mb-8">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-lg font-semibold text-gray-300">
              Les {numPlayers} IA Débattrices
            </h2>
            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-400">Nombre :</label>
              <div className="flex gap-1">
                {[2, 3, 4, 5, 6, 7, 8].map((n) => (
                  <button
                    key={n}
                    onClick={() => handleNumPlayersChange(n)}
                    className={`w-8 h-8 rounded-lg text-sm font-bold transition-colors ${
                      numPlayers === n
                        ? "bg-purple-600 text-white"
                        : "bg-gray-800 text-gray-400 hover:bg-gray-700"
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {players.map((player, i) => (
              <div
                key={i}
                className="p-4 rounded-xl bg-gray-900 border border-gray-800"
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-purple-400 font-bold">
                    {"🤖"} IA-{i + 1}
                  </span>
                </div>

                <label className="block text-xs text-gray-500 mb-1">Nom</label>
                <input
                  type="text"
                  value={player.name}
                  onChange={(e) => updatePlayer(i, "name", e.target.value)}
                  className="w-full mb-3 px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-sm text-gray-200 focus:border-purple-500 focus:outline-none"
                />

                <label className="block text-xs text-gray-500 mb-1">
                  Modèle
                </label>
                <select
                  value={player.model}
                  onChange={(e) => updatePlayer(i, "model", e.target.value)}
                  className="w-full mb-3 px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-sm text-gray-200 focus:border-purple-500 focus:outline-none"
                >
                  {allModels.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>

                <label className="block text-xs text-gray-500 mb-1">
                  Personnalité
                </label>
                <select
                  value={player.personality}
                  onChange={(e) =>
                    updatePlayer(i, "personality", e.target.value)
                  }
                  className="w-full mb-1 px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-sm text-gray-200 focus:border-purple-500 focus:outline-none"
                >
                  <option value="random">Aléatoire</option>
                  {BRAINSTORM_PERSONALITIES.map((p) => (
                    <option key={p} value={p}>
                      {p}
                    </option>
                  ))}
                  <option value="custom">Personnalisée...</option>
                </select>
                {player.personality === "custom" && (
                  <input
                    type="text"
                    value={player.customPersonality}
                    onChange={(e) =>
                      updatePlayer(i, "customPersonality", e.target.value)
                    }
                    placeholder="Décrivez la personnalité..."
                    className="w-full mt-2 px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-sm text-gray-200 focus:border-purple-500 focus:outline-none"
                  />
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Rules */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold mb-3 text-gray-300">Règles</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="p-4 rounded-xl bg-gray-900 border border-gray-800">
              <label className="block text-xs text-gray-500 mb-1">
                Durée par round de débat (secondes)
              </label>
              <input
                type="number"
                min={30}
                max={600}
                value={rules.debate_round_seconds}
                onChange={(e) =>
                  setRules((r) => ({
                    ...r,
                    debate_round_seconds: parseInt(e.target.value) || 180,
                  }))
                }
                className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-sm text-gray-200 focus:border-purple-500 focus:outline-none"
              />
            </div>

            <div className="p-4 rounded-xl bg-gray-900 border border-gray-800">
              <label className="block text-xs text-gray-500 mb-1">
                Nombre max de rounds
              </label>
              <input
                type="number"
                min={1}
                max={20}
                value={rules.max_rounds}
                onChange={(e) =>
                  setRules((r) => ({
                    ...r,
                    max_rounds: parseInt(e.target.value) || 5,
                  }))
                }
                className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-sm text-gray-200 focus:border-purple-500 focus:outline-none"
              />
            </div>

            <div className="p-4 rounded-xl bg-gray-900 border border-gray-800">
              <label className="block text-xs text-gray-500 mb-1">
                Seuil de consensus (sur {numPlayers})
              </label>
              <input
                type="number"
                min={2}
                max={numPlayers}
                value={rules.consensus_threshold}
                onChange={(e) =>
                  setRules((r) => ({
                    ...r,
                    consensus_threshold: parseInt(e.target.value) || 3,
                  }))
                }
                className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-sm text-gray-200 focus:border-purple-500 focus:outline-none"
              />
            </div>

            <div className="p-4 rounded-xl bg-gray-900 border border-gray-800">
              <label className="block text-xs text-gray-500 mb-1">
                Échanges par round de débat
              </label>
              <input
                type="number"
                min={1}
                max={10}
                value={rules.sub_rounds_per_debate}
                onChange={(e) =>
                  setRules((r) => ({
                    ...r,
                    sub_rounds_per_debate: parseInt(e.target.value) || 3,
                  }))
                }
                className="w-full px-3 py-2 rounded-lg bg-gray-800 border border-gray-700 text-sm text-gray-200 focus:border-purple-500 focus:outline-none"
              />
            </div>
          </div>
        </section>

        {/* Launch */}
        <button
          onClick={handleLaunch}
          disabled={launching || !topic.trim()}
          className="w-full py-4 rounded-xl font-bold text-lg bg-purple-600 hover:bg-purple-500 disabled:bg-gray-700 disabled:text-gray-500 transition-colors"
        >
          {launching ? "Lancement..." : "Lancer le Brainstorming"}
        </button>
      </div>
    </div>
  );
}
