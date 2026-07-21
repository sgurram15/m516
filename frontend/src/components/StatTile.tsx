interface Props {
  label: string;
  value: string | number;
}

export function StatTile({ label, value }: Props) {
  return (
    <div className="stat-tile">
      <div className="value">{value}</div>
      <div className="label">{label}</div>
    </div>
  );
}
