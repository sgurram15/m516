import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, createScan as apiCreateScan, getScan } from "../api/client";
import type { ScanStatusOut } from "../api/types";

const POLL_INTERVAL_MS = 1500;

interface UseScanResult {
  scan: ScanStatusOut | null;
  startError: string | null;
  start: (domain: string, packId?: string) => Promise<void>;
  reset: () => void;
}

// Scan id lives only in this hook's React state — lost on refresh, same POC-scope simplification as
// m516/api/state.py's in-memory ScanState (docs/06_FRONTEND_ARCHITECTURE.md).
export function useScan(): UseScanResult {
  const [scan, setScan] = useState<ScanStatusOut | null>(null);
  const [startError, setStartError] = useState<string | null>(null);
  const intervalRef = useRef<number | undefined>(undefined);

  const stopPolling = useCallback(() => {
    if (intervalRef.current !== undefined) {
      window.clearInterval(intervalRef.current);
      intervalRef.current = undefined;
    }
  }, []);

  useEffect(() => stopPolling, [stopPolling]);

  const start = useCallback(
    async (domain: string, packId?: string) => {
      setStartError(null);
      try {
        const created = await apiCreateScan({ domain, pack_id: packId });
        setScan(created);

        stopPolling();
        intervalRef.current = window.setInterval(async () => {
          try {
            const updated = await getScan(created.scan_id);
            setScan(updated);
            if (updated.status === "done" || updated.status === "error") {
              stopPolling();
            }
          } catch {
            stopPolling();
          }
        }, POLL_INTERVAL_MS);
      } catch (err) {
        setStartError(err instanceof ApiError ? err.message : "Could not start scan");
      }
    },
    [stopPolling],
  );

  const reset = useCallback(() => {
    stopPolling();
    setScan(null);
    setStartError(null);
  }, [stopPolling]);

  return { scan, startError, start, reset };
}
