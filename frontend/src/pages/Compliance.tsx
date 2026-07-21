import { useEffect, useState } from "react";
import { getCompliance, reportPdfUrl } from "../api/client";
import type { ComplianceGapOut, ScanStatus } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";
import { Waiting } from "../components/Waiting";
import { UNMAPPED } from "../api/types";

interface Props {
  scanId: string;
  status: ScanStatus;
}

// FR-5.5: framework/clause matrix + PDF export. Per docs/05_API_DESIGN.md, every gap will read
// "unmapped" until an LLM is wired into m516/compliance/mapper.py (WP3, still gated) — StatusBadge
// renders that honestly as "Not yet classified", never as a false "compliant" (BR-5).
export function Compliance({ scanId, status }: Props) {
  const [gaps, setGaps] = useState<ComplianceGapOut[] | null>(null);

  useEffect(() => {
    if (status !== "done") return;
    getCompliance(scanId).then(setGaps);
  }, [scanId, status]);

  if (status !== "done") return <Waiting status={status} />;
  if (!gaps) return <p className="muted">Loading compliance mapping…</p>;

  const anyClassified = gaps.some((g) => g.status !== UNMAPPED);

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Compliance</h2>
          <p>{gaps.length} candidate clause(s) retrieved against this scan's findings</p>
        </div>
        <a className="btn" href={reportPdfUrl(scanId)} target="_blank" rel="noreferrer">
          Export report (PDF)
        </a>
      </div>

      {!anyClassified && (
        <div className="card" style={{ borderColor: "var(--color-medium)" }}>
          No LLM classifier is configured yet, so nothing below has a real compliant/non-compliant
          verdict — these are candidate clauses for analyst review, not a determination.
        </div>
      )}

      <div className="card" style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>Framework</th>
              <th>Clause</th>
              <th>Status</th>
              <th>Related finding(s)</th>
              <th>Remediation</th>
            </tr>
          </thead>
          <tbody>
            {gaps.map((gap, i) => (
              <tr key={i}>
                <td>{gap.framework}</td>
                <td>
                  {gap.clause}
                  <div className="muted" style={{ fontSize: "0.8rem" }}>
                    {gap.clause_title}
                  </div>
                </td>
                <td>
                  <StatusBadge status={gap.status} />
                </td>
                <td style={{ fontSize: "0.85rem" }}>{gap.finding_refs.join("; ")}</td>
                <td style={{ fontSize: "0.85rem" }}>{gap.remediation ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
