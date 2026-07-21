import { UNMAPPED } from "../api/types";

interface Props {
  status: string;
}

// "unmapped" means no llm_client is wired yet (docs/05_API_DESIGN.md) — a candidate clause, not a
// verdict. Never render it as though it were a real compliance determination (BR-5, no fabrication).
export function StatusBadge({ status }: Props) {
  const label = status === UNMAPPED ? "Not yet classified" : status.replace("-", " ").toUpperCase();
  return <span className={`badge badge-${status}`}>{label}</span>;
}
