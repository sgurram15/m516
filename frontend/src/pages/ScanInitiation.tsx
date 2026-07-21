import { useEffect, useState } from "react";
import { getPacks } from "../api/client";
import type { PackOut } from "../api/types";

interface Props {
  onStart: (domain: string, packId?: string) => void;
  startError: string | null;
}

// FR-5.1: enter a domain, start a scan. Pack picker is populated from GET /api/packs — no hard-coded
// pack name here either (golden rule extends to the frontend).
export function ScanInitiation({ onStart, startError }: Props) {
  const [domain, setDomain] = useState("");
  const [packId, setPackId] = useState<string>("");
  const [packs, setPacks] = useState<PackOut[]>([]);

  useEffect(() => {
    getPacks()
      .then(setPacks)
      .catch(() => setPacks([]));
  }, []);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!domain.trim()) return;
    onStart(domain.trim(), packId || undefined);
  }

  return (
    <div className="center-screen">
      <form className="scan-form" onSubmit={handleSubmit}>
        <h1>M516</h1>
        <p className="muted">
          Passive external attack-surface &amp; compliance-intelligence scan. No active scan traffic is
          ever sent to the target (ADR-001).
        </p>

        <div className="field">
          <label htmlFor="domain">Domain</label>
          <input
            id="domain"
            type="text"
            placeholder="example.com"
            value={domain}
            onChange={(e) => setDomain(e.target.value)}
            required
          />
        </div>

        {packs.length > 0 && (
          <div className="field">
            <label htmlFor="pack">Compliance pack</label>
            <select id="pack" value={packId} onChange={(e) => setPackId(e.target.value)}>
              <option value="">Use server default</option>
              {packs.map((pack) => (
                <option key={pack.id} value={pack.id}>
                  {pack.display_name}
                </option>
              ))}
            </select>
          </div>
        )}

        {startError && <p style={{ color: "var(--color-critical)" }}>{startError}</p>}

        <button type="submit" className="btn" style={{ width: "100%" }}>
          Start scan
        </button>
      </form>
    </div>
  );
}
