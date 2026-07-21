# 21 · Compliance Packs (the extensibility mechanism)

> **Status:** Living · This is the most important doc for the "scale to any sector/country" goal.
> A pack is how M516 goes from Nigerian-banking to anything else **without engine changes**.

## What a pack is

A **compliance pack** bundles everything sector/country-specific: which frameworks apply, the source
regulatory documents, structured clause metadata, mapping hints, and report labels. The engine loads a
pack and operates generically against it. **The engine contains zero pack-specific knowledge.**

For the POC we author exactly one pack: **`nigeria-banking`** (NDPR + CBN). It must be complete and real.

## Why this design (ADR-009, ADR-012)

- **Build-for-one, architect-for-many.** One real vertical now; new verticals are data later.
- **No rewrite to extend.** `nigeria-telecom`, `kenya-banking`, `uk-healthcare` = new packs.
- **Authorable without deep coding.** Framework metadata + clauses in YAML; only novel mapping logic
  needs Python.

## Pack layout (on disk)

```
packs/
  nigeria-banking/
    pack.yaml                 # id, display_name, home_country, sector, frameworks list, report_labels
    frameworks/
      ndpr.yaml               # framework metadata + clause list
      cbn.yaml
    documents/
      ndpr.pdf|.txt           # source text to embed
      cbn_framework.pdf|.txt
    mapping.py                # OPTIONAL: pack-specific mapping hints/overrides (subclass of base)
```

## pack.yaml (shape)

```yaml
id: nigeria-banking
display_name: "Nigeria — Banking"
home_country: NG            # drives is_locally_hosted in the engine
sector: banking
frameworks: [ndpr, cbn]
report_labels:
  primary_regulator: "CBN"
  report_title: "Regulatory Exposure & Compliance Assessment"
```

## framework yaml (shape)

```yaml
id: NDPR
display_name: "Nigeria Data Protection Regulation"
issuing_body: NITDA
documents:
  - documents/ndpr.txt
clauses:
  - ref: "NDPR 2.6"
    title: "Technical security measures"
    summary: "Controllers must implement appropriate technical measures to protect personal data."
    finding_hints: ["exposed database", "unencrypted", "public service", "PII exposure"]
  - ref: "NDPR 4.1(3)"
    title: "Access restriction"
    summary: "Access to personal data restricted to authorised personnel."
    finding_hints: ["open port", "admin panel", "default credentials"]
```

`finding_hints` improve RAG retrieval by giving the engine keywords that connect finding-types to
clauses. They are optional but valuable.

## How the engine uses a pack (generic flow)

1. Load `pack.yaml` → know home_country, sector, frameworks, report labels.
2. For each framework: ingest `documents` into the vector store (embedded once, cached).
3. For each finding: build a query from the finding + any `finding_hints`; retrieve top clauses.
4. LLM maps finding → clause(s) with status + remediation, constrained to retrieved clauses.
5. Report module uses `report_labels` (e.g. addresses the report to the pack's regulator).

## Authoring a NEW pack (future — the payoff)

1. `mkdir packs/<new-pack>`; write `pack.yaml` (set `home_country`, `sector`, `frameworks`).
2. Add framework YAMLs + source documents.
3. (Optional) `mapping.py` for any sector-specific mapping nuance.
4. Point the engine at the pack id. **No engine code changes.**

## POC scope for packs

- Author `nigeria-banking` only.
- Prove the engine loads it generically (no hard-coded "NDPR"/"CBN"/"NG" in engine code).
- A trivial second stub pack (even empty) may be added in tests to prove genericity — optional.

## Validation note

Clause metadata and mappings in `nigeria-banking` must be validated by a qualified compliance
professional before any client relies on the output (NFR-SEC, `08_SECURITY.md`).
