"""Retrieve candidate clauses for a Finding (docs/21_COMPLIANCE_PACKS.md step 3).

Query text is built from the finding itself — no pack-specific knowledge here, the engine only knows
"a finding has a service, an explanation, a severity" (golden rule).
"""

from __future__ import annotations

from dataclasses import dataclass

from chromadb.api.models.Collection import Collection

from m516.findings import Finding

_DEFAULT_TOP_K = 3


@dataclass
class ClauseMatch:
    ref: str
    title: str
    framework_id: str
    distance: float


def _query_text(finding: Finding) -> str:
    product = finding.service.product or "unidentified service"
    return (
        f"{finding.explanation} Service: {product} on port {finding.service.port}/"
        f"{finding.service.protocol}. Severity: {finding.severity}."
    )


def retrieve_clauses(collection: Collection, finding: Finding, top_k: int = _DEFAULT_TOP_K) -> list[ClauseMatch]:
    if collection.count() == 0:
        return []

    results = collection.query(query_texts=[_query_text(finding)], n_results=min(top_k, collection.count()))

    matches = []
    ids = results.get("ids", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    for ref, meta, distance in zip(ids, metadatas, distances):
        matches.append(
            ClauseMatch(
                ref=ref,
                title=(meta or {}).get("title", ""),
                framework_id=(meta or {}).get("framework_id", ""),
                distance=distance,
            )
        )
    return matches
