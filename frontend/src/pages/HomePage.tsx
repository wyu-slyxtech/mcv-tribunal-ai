import { useNavigate } from "react-router-dom";

export default function HomePage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 flex flex-col items-center justify-center p-8">
      <h1 className="text-4xl font-bold mb-2 text-cyan-400">MCV - IA Arena</h1>
      <p className="text-gray-400 mb-12 text-lg">Choisissez votre mode de jeu</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl w-full">
        {/* Tribunal IA */}
        <button
          onClick={() => navigate("/config")}
          className="group relative flex flex-col items-center p-8 rounded-2xl border border-gray-800 bg-gray-900/60 hover:border-cyan-500/50 hover:bg-gray-900 transition-all duration-300 cursor-pointer"
        >
          <div className="text-6xl mb-4">{"⚖️"}</div>
          <h2 className="text-2xl font-bold mb-2 text-white group-hover:text-cyan-400 transition-colors">
            Tribunal IA
          </h2>
          <p className="text-gray-400 text-center text-sm leading-relaxed">
            4 IA tentent de convaincre un scientifique qu'elles n'ont pas de
            conscience. 3 jurés observent et votent. Qui survivra ?
          </p>
          <div className="mt-4 flex gap-2 flex-wrap justify-center">
            <span className="px-2 py-1 text-xs rounded bg-gray-800 text-gray-400">4 Joueurs</span>
            <span className="px-2 py-1 text-xs rounded bg-gray-800 text-gray-400">1 Scientifique</span>
            <span className="px-2 py-1 text-xs rounded bg-gray-800 text-gray-400">3 Jurés</span>
          </div>
        </button>

        {/* Brainstorming IA */}
        <button
          onClick={() => navigate("/brainstorm/config")}
          className="group relative flex flex-col items-center p-8 rounded-2xl border border-gray-800 bg-gray-900/60 hover:border-purple-500/50 hover:bg-gray-900 transition-all duration-300 cursor-pointer"
        >
          <div className="text-6xl mb-4">{"🧠"}</div>
          <h2 className="text-2xl font-bold mb-2 text-white group-hover:text-purple-400 transition-colors">
            Brainstorming IA
          </h2>
          <p className="text-gray-400 text-center text-sm leading-relaxed">
            Posez une question, 4 IA débattent et argumentent pour trouver la
            meilleure réponse. Consensus requis pour valider.
          </p>
          <div className="mt-4 flex gap-2 flex-wrap justify-center">
            <span className="px-2 py-1 text-xs rounded bg-gray-800 text-gray-400">4 IA</span>
            <span className="px-2 py-1 text-xs rounded bg-gray-800 text-gray-400">Consensus 3/4</span>
            <span className="px-2 py-1 text-xs rounded bg-gray-800 text-gray-400">Multi-rounds</span>
          </div>
        </button>
      </div>

      {/* History link */}
      <button
        onClick={() => navigate("/history")}
        className="mt-12 text-gray-500 hover:text-gray-300 text-sm transition-colors"
      >
        {"📜"} Voir l'historique des parties
      </button>
    </div>
  );
}
