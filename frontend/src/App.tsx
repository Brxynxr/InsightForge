import { Routes, Route } from "react-router-dom";
import Layout from "@/components/layout/Layout";
import DashboardPage from "@/components/pages/DashboardPage";
import UploadPage from "@/components/pages/UploadPage";
import HistoryPage from "@/components/pages/HistoryPage";
import SettingsPage from "@/components/pages/SettingsPage";
import BenchmarkPage from "@/components/pages/BenchmarkPage";

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<DashboardPage />} />
        <Route path="upload" element={<UploadPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="settings" element={<SettingsPage />} />
        <Route path="benchmark" element={<BenchmarkPage />} />
      </Route>
    </Routes>
  );
}

export default App;
