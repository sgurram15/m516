export const TABS = ["Dashboard", "Asset Discovery", "Risk Scoring", "Compliance"] as const;
export type Tab = (typeof TABS)[number];

interface Props {
  active: Tab;
  onSelect: (tab: Tab) => void;
  domain: string;
  onNewScan: () => void;
}

// Deliberately just these 4 tabs + the pre-scan "Scan Initiation" screen (App.tsx) = FR-5's five
// screens. The mockups' "Breach Monitor"/"Users & Roles" are out of scope (ADR-010, confirmed with the
// client — see docs/15_PROGRESS.md); "Port Scanner" isn't a separate FR-5 screen, so port/service
// detail lives inside Asset Discovery instead of a 6th tab.
export function Sidebar({ active, onSelect, domain, onNewScan }: Props) {
  return (
    <aside className="sidebar">
      <h1>M516</h1>
      <p>External Attack Surface &amp; Compliance</p>
      <p className="muted" style={{ marginTop: "-1rem" }}>
        {domain}
      </p>
      <nav>
        {TABS.map((tab) => (
          <button
            key={tab}
            className={`nav-item${tab === active ? " active" : ""}`}
            onClick={() => onSelect(tab)}
          >
            {tab}
          </button>
        ))}
      </nav>
      <button className="btn btn-secondary" style={{ marginTop: "1.5rem", width: "100%" }} onClick={onNewScan}>
        New scan
      </button>
    </aside>
  );
}
