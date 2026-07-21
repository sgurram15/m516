import { useState } from "react";
import { ProgressBanner } from "./components/ProgressBanner";
import { Sidebar, TABS, type Tab } from "./components/Sidebar";
import { useScan } from "./hooks/useScan";
import { AssetDiscovery } from "./pages/AssetDiscovery";
import { Compliance } from "./pages/Compliance";
import { Dashboard } from "./pages/Dashboard";
import { RiskScoring } from "./pages/RiskScoring";
import { ScanInitiation } from "./pages/ScanInitiation";

export default function App() {
  const { scan, startError, start, reset } = useScan();
  const [activeTab, setActiveTab] = useState<Tab>(TABS[0]);

  if (!scan) {
    return <ScanInitiation onStart={start} startError={startError} />;
  }

  return (
    <div className="app-shell">
      <Sidebar active={activeTab} onSelect={setActiveTab} domain={scan.domain} onNewScan={reset} />
      <main className="main-content">
        <ProgressBanner status={scan.status} stage={scan.stage} />
        {scan.status === "error" && <div className="error-banner">Scan failed: {scan.error}</div>}

        {activeTab === "Dashboard" && <Dashboard scanId={scan.scan_id} status={scan.status} />}
        {activeTab === "Asset Discovery" && <AssetDiscovery scanId={scan.scan_id} status={scan.status} />}
        {activeTab === "Risk Scoring" && <RiskScoring scanId={scan.scan_id} status={scan.status} />}
        {activeTab === "Compliance" && <Compliance scanId={scan.scan_id} status={scan.status} />}
      </main>
    </div>
  );
}
