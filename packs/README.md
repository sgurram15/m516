# Compliance packs

`nigeria-banking` (NDPR + CBN) is the one real pack the POC needs, and it's **not authored yet** — it's
blocked on the client providing real NDPR + CBN source documents (open gating decision, see
`docs/15_PROGRESS.md`).

Do not draft NDPR/CBN clause content from memory into a `nigeria-banking/` directory here. Per
`docs/21_COMPLIANCE_PACKS.md`, this pack's content "must be complete and real" and "must be validated by
a qualified compliance professional before any client relies on the output" — placeholder regulatory
clause numbers under the real pack name risk being mistaken for authoritative material later.

The pack format is fully specified in `docs/21_COMPLIANCE_PACKS.md`. A working example (fictional
framework, proves the engine loads/embeds/retrieves generically with zero pack-specific engine code) is
in `tests/fixtures/packs/test-stub/`.
