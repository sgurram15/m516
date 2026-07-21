"""Module 3 orchestrator + ComplianceMapping (docs/03_DOMAIN_MODEL.md, docs/21_COMPLIANCE_PACKS.md step
4): finding -> retrieved clause(s) -> LLM classifies status + remediation, constrained to what was
retrieved.

No LLM is wired yet (no key configured — see docs/15_PROGRESS.md). Retrieval is real and always runs;
without an `llm_client`, mappings come back with `status="unmapped"` — an honest partial result ("here
is the relevant clause, no classification yet"), never a fabricated compliant/non-compliant verdict
(BR-5: no fabrication).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from chromadb.api.models.Collection import Collection

from m516.compliance.pack_loader import CompliancePack
from m516.compliance.retrieve import retrieve_clauses
from m516.findings import Finding

UNMAPPED = "unmapped"


@dataclass
class ComplianceMapping:
    framework: str
    clause: str
    status: str  # "compliant" | "partial" | "non-compliant" | "unmapped" (no LLM configured)
    remediation: str | None


class LLMClient(Protocol):
    """Minimal interface mapper.py needs from any LLM provider — deliberately small so wiring a real
    one later (Anthropic, etc.) is an isolated adapter, not a mapper.py rewrite."""

    def classify(self, finding: Finding, clause_title: str, clause_summary: str) -> tuple[str, str]:
        """Returns (status, remediation) for one finding/clause pair."""
        ...


def map_finding(
    finding: Finding,
    pack: CompliancePack,
    collection: Collection,
    llm_client: LLMClient | None = None,
    top_k: int = 3,
) -> list[ComplianceMapping]:
    matches = retrieve_clauses(collection, finding, top_k=top_k)

    mappings = []
    for match in matches:
        if llm_client is None:
            status, remediation = UNMAPPED, None
        else:
            clause = _find_clause(pack, match.ref)
            status, remediation = llm_client.classify(
                finding, clause.title if clause else match.title, clause.summary if clause else ""
            )
        mappings.append(ComplianceMapping(framework=match.framework_id, clause=match.ref, status=status, remediation=remediation))

    return mappings


def _find_clause(pack: CompliancePack, ref: str):
    for framework in pack.frameworks:
        for clause in framework.clauses:
            if clause.ref == ref:
                return clause
    return None
