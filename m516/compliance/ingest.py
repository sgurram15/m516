"""Embed a pack's clauses into ChromaDB (ADR-005: ChromaDB for POC scale, zero-ops).

Retrieval unit is **clauses**, not raw source-document text. `docs/21_COMPLIANCE_PACKS.md`'s flow says
"ingest documents... retrieve top clauses" — the robust reading for finding-to-clause mapping is to
embed each clause's own curated text (title + summary + finding_hints), since that is the actual thing
we need to retrieve. Raw source-document ingestion (for report-citation evidence) is deliberately out of
scope here — a later addition, not an oversight.

Uses ChromaDB's default embedding function (`all-MiniLM-L6-v2` via ONNX Runtime) explicitly — local, no
API key, free (ADR-002 spirit). Downloads model weights once on first use (~80MB from ChromaDB's model
cache), then runs fully offline.
"""

from __future__ import annotations

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.utils import embedding_functions

from m516.compliance.pack_loader import CompliancePack

_DEFAULT_CHROMA_PATH = ".chroma"


def ingest_pack(pack: CompliancePack, chroma_path: str = _DEFAULT_CHROMA_PATH) -> Collection:
    """Embeds every clause across every framework in `pack` into a collection named after the pack id.
    Re-running is idempotent — `add()` with the same ids upserts, it doesn't duplicate."""
    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(
        pack.id, embedding_function=embedding_functions.DefaultEmbeddingFunction()
    )

    ids, documents, metadatas = [], [], []
    for framework in pack.frameworks:
        for clause in framework.clauses:
            ids.append(clause.ref)
            hints = ", ".join(clause.finding_hints)
            documents.append(f"{clause.title}. {clause.summary} Keywords: {hints}" if hints else f"{clause.title}. {clause.summary}")
            metadatas.append({"framework_id": framework.id, "title": clause.title})

    if ids:
        collection.add(ids=ids, documents=documents, metadatas=metadatas)

    return collection
