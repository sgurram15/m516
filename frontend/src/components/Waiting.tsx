import type { ScanStatus } from "../api/types";

interface Props {
  status: ScanStatus;
}

export function Waiting({ status }: Props) {
  if (status === "error") {
    return <p className="muted">The scan failed — see the error banner above.</p>;
  }
  return <p className="muted">Waiting for the scan to finish…</p>;
}
