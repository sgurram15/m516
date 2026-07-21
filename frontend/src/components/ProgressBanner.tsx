import type { ScanStatus } from "../api/types";

const STAGE_LABELS: Record<string, string> = {
  discovery: "Discovering internet-facing assets",
  enrichment: "Matching services to known CVEs",
  compliance: "Retrieving relevant regulatory clauses",
  report: "Building the report",
  done: "Done",
};

interface Props {
  status: ScanStatus;
  stage: string | null;
}

// FR-5.1's "live progress" — polled via useScan, not pushed. There is no queue/worker behind this
// (docs/05_API_DESIGN.md); it just reflects m516/pipeline.py's on_stage() callback.
export function ProgressBanner({ status, stage }: Props) {
  if (status === "done" || status === "error") {
    return null;
  }

  const label = stage ? STAGE_LABELS[stage] ?? stage : "Starting scan";
  return (
    <div className="progress-banner">
      <span>{label}...</span>
      <span className="muted">status: {status}</span>
    </div>
  );
}
