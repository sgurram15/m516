interface Props {
  severity: string;
}

// Matches m516/enrichment/scoring.py's severity buckets and the same colors as m516/report/render.py.
export function SeverityBadge({ severity }: Props) {
  return <span className={`badge badge-${severity}`}>{severity.toUpperCase()}</span>;
}
