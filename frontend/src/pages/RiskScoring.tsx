import { useEffect, useState } from "react";
import { getFindings, reportPdfUrl } from "../api/client";
import type { FindingOut, ScanStatus } from "../api/types";
import { SeverityBadge } from "../components/SeverityBadge";
import { Waiting } from "../components/Waiting";

interface Props {
  scanId: string;
  status: ScanStatus;
}

// FR-5.4: ranked findings. "Why it matters" (not the mockup's "Exploitation Scenario") is the
// deterministic explanation from m516/enrichment/scoring.py — never an LLM-generated narrative, since
// none is wired (same naming call demo/streamlit_app.py already made).
export function RiskScoring({ scanId, status }: Props) {
  const [findings, setFindings] = useState<FindingOut[] | null>(null);

  useEffect(() => {
    if (status !== "done") return;
    getFindings(scanId).then(setFindings);
  }, [scanId, status]);

  if (status !== "done") return <Waiting status={status} />;
  if (!findings) return <p className="muted">Loading findings…</p>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Risk Scoring</h2>
          <p>{findings.length} ranked finding(s), highest risk first</p>
        </div>
        <a className="btn" href={reportPdfUrl(scanId)} target="_blank" rel="noreferrer">
          Export report (PDF)
        </a>
      </div>

      {findings.length === 0 && <p className="muted">No CVE-eligible findings for this scan.</p>}

      {findings.map((finding, i) => (
        <div className="card" key={i}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
            <div>
              <strong>
                {finding.service.product ?? finding.service.name ?? "Unidentified service"} on port{" "}
                {finding.service.port}/{finding.service.protocol}
              </strong>
              <p className="muted" style={{ margin: "0.25rem 0" }}>
                {finding.asset.ip ?? finding.asset.hostname} · CVSS {finding.cvss} · contextual score{" "}
                {finding.contextual_score}
              </p>
            </div>
            <SeverityBadge severity={finding.severity} />
          </div>

          <p>
            <strong>Why it matters:</strong> {finding.explanation}
          </p>

          <p className="muted" style={{ fontSize: "0.85rem" }}>
            CVE(s): {finding.cve_ids.join(", ") || "—"} · match confidence: {finding.match_confidence}
            {finding.match_confidence === "broad" &&
              " (version not confirmed by passive lookup — verify before relying on this finding)"}
          </p>
        </div>
      ))}
    </div>
  );
}
