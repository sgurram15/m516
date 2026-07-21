import { useEffect, useState } from "react";
import { getAssets } from "../api/client";
import type { AssetSummaryOut, ScanStatus } from "../api/types";
import { Waiting } from "../components/Waiting";

interface Props {
  scanId: string;
  status: ScanStatus;
}

// FR-5.3: the discovered asset table. AssetSummaryOut (m516/report/template.py's AssetSummary) is
// exactly what's shown here — no per-asset raw service list is exposed by the API today, so there's
// no expandable port detail row; that level of detail is available per-finding on Risk Scoring instead.
export function AssetDiscovery({ scanId, status }: Props) {
  const [assets, setAssets] = useState<AssetSummaryOut[] | null>(null);

  useEffect(() => {
    if (status !== "done") return;
    getAssets(scanId).then(setAssets);
  }, [scanId, status]);

  if (status !== "done") return <Waiting status={status} />;
  if (!assets) return <p className="muted">Loading assets…</p>;

  return (
    <div>
      <div className="page-header">
        <div>
          <h2>Asset Discovery</h2>
          <p>{assets.length} discovered asset(s)</p>
        </div>
      </div>

      <div className="card" style={{ overflowX: "auto" }}>
        <table>
          <thead>
            <tr>
              <th>IP</th>
              <th>Hostname</th>
              <th>Country</th>
              <th>WAF / CDN</th>
              <th>Services</th>
              <th>Cert status</th>
              <th>Sources</th>
            </tr>
          </thead>
          <tbody>
            {assets.map((asset, i) => (
              <tr key={`${asset.ip}-${i}`}>
                <td>{asset.ip ?? "—"}</td>
                <td>{asset.hostname ?? asset.domain ?? "—"}</td>
                <td>{asset.country ?? "—"}</td>
                <td>{asset.is_behind_waf ? "Yes" : "No"}</td>
                <td>{asset.service_count}</td>
                <td>
                  {asset.cert_detection_level ? (
                    <span className={`badge badge-${asset.cert_detection_level}`}>
                      {asset.cert_detection_level.toUpperCase()}
                    </span>
                  ) : (
                    <span className="muted">n/a</span>
                  )}
                </td>
                <td>{asset.sources.join(", ") || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
