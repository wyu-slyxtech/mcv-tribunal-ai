import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import GamePage from "./pages/GamePage";
import ReplayPage from "./pages/ReplayPage";
import HistoryPage from "./pages/HistoryPage";
import ConfigPage from "./pages/ConfigPage";
import BrainstormConfigPage from "./pages/BrainstormConfigPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/config" element={<ConfigPage />} />
        <Route path="/brainstorm/config" element={<BrainstormConfigPage />} />
        <Route path="/game/:id" element={<GamePage />} />
        <Route path="/replay/:id" element={<ReplayPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </BrowserRouter>
  );
}
