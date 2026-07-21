# Compliance packs

## `nigeria-banking` (NDPR + CBN) — authored

The real source documents arrived (placed by the client into `regulations/`, verified genuine, and
copied into `nigeria-banking/documents/`):

- **NDPR** — Nigeria Data Protection Regulation 2019: Implementation Framework (NITDA, issued
  November 2020).
- **CBN** — Risk-Based Cybersecurity Framework and Guidelines for Deposit Money Banks and Payment
  Service Providers (Central Bank of Nigeria, Banking Supervision Dept., October 2018).

`pack.yaml` + `frameworks/ndpr.yaml` + `frameworks/cbn.yaml` contain real clause metadata: every
`ref`, `title` and `summary` cites an actual article/section of the source documents above — nothing
is fabricated. 9 NDPR clauses + 12 CBN clauses, covering the themes most relevant to passive
attack-surface findings (exposed/unpatched services, access control, data breach notification
timelines, DPO/CISO governance, vulnerability management, cross-border data transfer).

**Still required before any client relies on the output** (per `docs/21_COMPLIANCE_PACKS.md`'s
validation note, NFR-SEC): a qualified compliance professional must review the clause selection and
citations. This pack is a solid engineering-grade first draft, not a legal sign-off.

The pack format is fully specified in `docs/21_COMPLIANCE_PACKS.md`. A second, obviously-fictional
pack (`tests/fixtures/packs/test-stub/`) proves the engine loads/embeds/retrieves generically with
zero pack-specific engine code — keep using that one for engine-generic tests, not `nigeria-banking`.
