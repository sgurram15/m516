import { useEffect, useState } from "react";
import { getDashboard, reportPdfUrl } from "../api/client";
import type { ScanStatus, ScanSummaryOut } from "../api/types";
import { StatTile } from "../components/StatTile";
import { Waiting } from "../components/Waiting";

interface Props {
  scanId: string;
  status: ScanStatus;
}

// FR-5.2: summary KPIs from the scan, straight from ReportData (m516/report/template.py) — no
// re-aggregation on the frontend either.
export function Dashboard({ scanId, status }: Props) {
  const [summary, setSummary] = useState<ScanSummaryOut | null>(null);

  useEffect(() => {
    if (status !== "done") return;
    getDashboard(scanId).then(setSummary);
  }, [scanId, status]);

  if (status !== "done") return <Waiting status={status} />;
  if (!summary) return <p className="muted">Loading dashboard…</p>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>{summary.report_title}</h2>
          <p>
            {summary.domain}
            {summary.pack_display_name ? ` — ${summary.pack_display_name}` : ""}
          </p>
        </div>
        <a className="btn" href={reportPdfUrl(scanId)} target="_blank" rel="noreferrer">
          Export report (PDF)
        </a>
      </div>

      <div className="stat-grid">
        <StatTile label="Assets" value={summary.asset_count} />
        <StatTile label="Services" value={summary.service_count} />
        <StatTile label="Findings" value={summary.finding_count} />
        <StatTile label="Critical" value={summary.severity_counts.critical ?? 0} />
        <StatTile label="High" value={summary.severity_counts.high ?? 0} />
      </div>

      <div className="card">
        <h3 style={{ marginTop: 0 }}>Executive summary</h3>
        <p>{summary.executive_summary}</p>
      </div>

      <p className="disclaimer">
        Generated {new Date(summary.generated_at).toLocaleString()}. This is an automated, passive
        assessment — see the exported report for the full disclaimer and validation requirements.
      </p>
    </div>
  );
}
