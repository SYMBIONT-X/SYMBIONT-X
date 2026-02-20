import { Routes, Route, Navigate } from 'react-router-dom';
import { Layout } from '@components/Layout/Layout';
import { DashboardPage } from '@pages/DashboardPage';
import { VulnerabilitiesPage } from '@pages/VulnerabilitiesPage';
import { AgentsPage } from '@pages/AgentsPage';
import { SettingsPage } from '@pages/SettingsPage';
import { MonitoringPage } from '@pages/MonitoringPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="vulnerabilities" element={<VulnerabilitiesPage />} />
        <Route path="agents" element={<AgentsPage />} />
        <Route path="monitoring" element={<MonitoringPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}

export default App;
