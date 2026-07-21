// Mirrors m516/api/schemas.py exactly — reconcile there first if these ever diverge (docs/05_API_DESIGN.md).

export type ScanStatus = "pending" | "running" | "done" | "error";

export interface ScanStatusOut {
  scan_id: string;
  domain: string;
  pack_id: string;
  status: ScanStatus;
  stage: string | null;
  error: string | null;
  started_at: string;
  finished_at: string | null;
}

export interface ScanSummaryOut {
  domain: string;
  generated_at: string;
  report_title: string;
  primary_regulator: string | null;
  pack_display_name: string | null;
  executive_summary: string;
  severity_counts: Record<string, number>;
  asset_count: number;
  service_count: number;
  finding_count: number;
}

export interface AssetSummaryOut {
  ip: string | null;
  hostname: string | null;
  domain: string | null;
  country: string | null;
  is_behind_waf: boolean;
  service_count: number;
  cert_detection_level: string | null;
  sources: string[];
}

export interface ServiceOut {
  port: number;
  protocol: string;
  name: string | null;
  product: string | null;
  version: string | null;
  cpe: string | null;
}

export interface AssetRefOut {
  ip: string | null;
  hostname: string | null;
  domain: string | null;
  country: string | null;
  is_behind_waf: boolean;
}

export interface ComplianceMappingOut {
  framework: string;
  clause: string;
  status: string;
  remediation: string | null;
}

export interface FindingOut {
  asset: AssetRefOut;
  service: ServiceOut;
  cve_ids: string[];
  cvss: number;
  contextual_score: number;
  severity: "critical" | "high" | "medium" | "low";
  explanation: string;
  match_confidence: "exact" | "broad";
  exploitability_score: number | null;
  impact_score: number | null;
  compliance: ComplianceMappingOut[];
}

export interface ComplianceGapOut {
  framework: string;
  clause: string;
  clause_title: string;
  status: string;
  remediation: string | null;
  finding_refs: string[];
}

export interface PackOut {
  id: string;
  display_name: string;
  sector: string;
  home_country: string;
}

export interface ScanCreateRequest {
  domain: string;
  pack_id?: string;
}

export const UNMAPPED = "unmapped";
