// Thin typed fetch wrapper over docs/05_API_DESIGN.md. No business logic — every function here maps
// 1:1 to an endpoint; pages/components decide what to do with the data.

import type {
  AssetSummaryOut,
  ComplianceGapOut,
  FindingOut,
  PackOut,
  ScanCreateRequest,
  ScanStatusOut,
  ScanSummaryOut,
} from "./types";

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

export class ApiError extends Error {
  status: number;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new ApiError(response.status, body.detail ?? response.statusText);
  }

  return response.json() as Promise<T>;
}

export function createScan(payload: ScanCreateRequest): Promise<ScanStatusOut> {
  return request<ScanStatusOut>("/scans", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getScan(scanId: string): Promise<ScanStatusOut> {
  return request<ScanStatusOut>(`/scans/${scanId}`);
}

export function getDashboard(scanId: string): Promise<ScanSummaryOut> {
  return request<ScanSummaryOut>(`/scans/${scanId}/dashboard`);
}

export function getAssets(scanId: string): Promise<AssetSummaryOut[]> {
  return request<AssetSummaryOut[]>(`/scans/${scanId}/assets`);
}

export function getFindings(scanId: string): Promise<FindingOut[]> {
  return request<FindingOut[]>(`/scans/${scanId}/findings`);
}

export function getCompliance(scanId: string): Promise<ComplianceGapOut[]> {
  return request<ComplianceGapOut[]>(`/scans/${scanId}/compliance`);
}

export function getPacks(): Promise<PackOut[]> {
  return request<PackOut[]>("/packs");
}

export function reportPdfUrl(scanId: string): string {
  return `${BASE_URL}/scans/${scanId}/report.pdf`;
}
