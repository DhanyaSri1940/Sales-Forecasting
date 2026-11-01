import { Navigate, Route, Routes } from "react-router-dom";
import Sidebar from "./components/Sidebar";
import Topbar from "./components/Topbar";
import Dashboard from "./pages/Dashboard";
import Forecast from "./pages/Forecast";
import Analytics from "./pages/Analytics";
import Inventory from "./pages/Inventory";
import ModelPerformance from "./pages/ModelPerformance";

export default function App() {
  return (
    <div className="app-shell">
      <Sidebar />
      <div className="workspace">
        <Topbar />
        <main className="main">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/forecast" element={<Forecast />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/inventory" element={<Inventory />} />
            <Route path="/model" element={<ModelPerformance />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}
