import { BrowserRouter, Routes, Route } from "react-router-dom";
import GamePage from "./pages/GamePage";
import ReplayPage from "./pages/ReplayPage";
import HistoryPage from "./pages/HistoryPage";
import ConfigPage from "./pages/ConfigPage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ConfigPage />} />
        <Route path="/game/:id" element={<GamePage />} />
        <Route path="/replay/:id" element={<ReplayPage />} />
        <Route path="/history" element={<HistoryPage />} />
      </Routes>
    </BrowserRouter>
  );
}
