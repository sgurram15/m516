# 12 · Decision Log (ADRs)

> **Status:** Living · Why decisions were made. Never delete; supersede + mark old ones. Format:
> Context · Decision · Reason · Consequences.

## ADR-001 · Strictly passive POC
- **Context:** Attack-surface discovery can be active (scan targets) or passive (query indexes).
- **Decision:** Passive only; never send scan traffic to a target.
- **Reason:** Legal safety (Cybercrimes Act 2015) + simplicity.
- **Consequences:** Slightly stale data (accepted). Any future live-scan gated behind authorisation.

## ADR-002 · Provider-agnostic abstraction
- **Decision:** Pipeline depends on `BaseProvider`; each provider is an adapter.
- **Reason:** Free tiers, coverage via combination, cross-check, no lock-in, one-file adds.
- **Consequences:** Small upfront abstraction; every provider normalises to common shape.

## ADR-003 · FastAPI / Python
- **Reason:** Matches skillset + AI/RAG ecosystem (LangChain, ChromaDB, NVD clients Python-native).
- **Consequences:** Python end-to-end except frontend.

## ADR-004 · Netlas + Criminal IP first
- **Context:** Coverage test on gtbank.com / interswitchgroup.com / nitda.gov.ng.
- **Decision:** Start with Netlas (deep: banners/CPEs/certs) + Criminal IP (summary/risk/tech stack).
- **Reason:** Best combined coverage of locally-hosted NG infra. Tier-1 banks are WAF-hidden;
  government/mid-tier reveal real findings.
- **Consequences:** Demo targets government/mid-tier-style domains, not WAF-fronted Tier-1 banks.

## ADR-005 · ChromaDB for POC vector store
- **Reason:** Handful of documents; zero-ops; Milvus overkill at this scale.
- **Consequences:** Revisit for scale; keep store swappable.

## ADR-006 · NVD/CVE as vulnerability source
- **Reason:** Free, authoritative, geography-independent (applies to NG targets identically).
- **Consequences:** NVD backlog/latency accepted for POC; supplement feeds if productised.

## ADR-007 · Rules-based risk scoring, not LLM
- **Reason:** Must be explainable, reproducible, cheap. LLM scores opaque/non-deterministic — bad for a
  compliance product.
- **Consequences:** Explicit auditable rules; LLM reserved for mapping + narrative.

## ADR-008 · NDPR + CBN for the POC
- **Decision:** POC pack loads only NDPR + CBN.
- **Reason:** Two frameworks prove the capability; more multiply validation burden without more proof.
- **Consequences:** More frameworks = new pack content, no code change.

## ADR-009 · Engine + compliance-pack architecture (build-for-one, architect-for-many)
- **Context:** Deliver Nigerian-banking now, but must scale to any sector/country without rewrite.
- **Decision:** Universal engine + swappable **compliance packs**. Author one pack (`nigeria-banking`)
  for the POC against a real pack interface. Not hard-coded; not fully multi-pack-productised.
- **Reason:** Avoids both over-fitting (rewrite to extend) and over-generalising (wasting POC budget).
- **Consequences:** Engine must never reference a specific framework/country/sector (golden rule).
  Extending = authoring a pack. See `21_COMPLIANCE_PACKS.md`.

## ADR-010 · Tenant-aware data model, no auth built
- **Decision:** Core records carry a nullable `tenant_id`; no login/roles in POC.
- **Reason:** Avoids a painful future migration to multi-tenant; costs nothing now; no wasted auth work.
- **Consequences:** `tenant_id` present but unused in POC.

## ADR-011 · Shodan InternetDB as a free enrichment provider
- **Context:** Free, no-key endpoint returning ports/CPEs/vulns by IP.
- **Decision:** Add as an IP-enrichment provider behind the same interface.
- **Reason:** Shodan-quality data with no key/quota; cross-checks other providers; passive.
- **Consequences:** **Non-commercial licence** — free for POC/build/demo, but **commercial use needs a
  Shodan enterprise licence**. Flag before any commercial launch (see `13_RISK_REGISTER.md`). Takes an
  IP not a domain, so runs after domain→IP resolution. Weekly freshness, no banners.

## ADR-012 · Pack format = YAML metadata + optional Python mapping
- **Decision:** Framework metadata + clauses in YAML; novel mapping logic (if any) in a pack `mapping.py`.
- **Reason:** Authorable without deep coding for the common case; Python escape hatch for nuance.
- **Consequences:** Most new packs are pure data; engine stays generic.

## ADR-013 · Documentation-first, Claude-Code-optimised memory
- **Decision:** Maintain `CLAUDE.md` + a right-sized `docs/` set as the single source of truth; every
  session reads docs first and updates them last.
- **Reason:** Project spans many sessions with context limits; markdown is the only durable memory.
- **Consequences:** Stale docs = a bug. `15_PROGRESS.md` + `16_SESSION_LOG.md` must always reflect reality.

## Superseded / historical
*(none yet)*
