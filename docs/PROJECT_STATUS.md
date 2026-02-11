# Project Status

## Scope (Current)
- Repository: `bnk4`
- Engine v1 is the active, shipped core in this repo.
- Next product work is local analyzer UI + API under `apps/`.

## Engine v1 (Done)
- Global BPM (raw + reportable)
- Global Key/Mode (key may emit while mode is withheld)
- Metadata output
- Deterministic packaging and role gating

## Engine v1 (Out of Scope)
- Section-level key/mode
- Loudness/true-peak/clipping/dynamic-range as public v1 outputs
- Camelot as a first-class output block

## Contract Source Of Truth
- Public contract: `docs/ENGINE_V1_CONTRACT.md`
- Canonical output/gating details: `CONTRACTS/analysis_output.md`
- Security invariants: `docs/SECURITY_SPEC.md`
- Threat model: `docs/THREAT_MODEL.md`

## Near-Term Roadmap
1. Keep engine v1 stable, deterministic, and accuracy-first.
2. Build local analyzer API + UI under `apps/`.
3. Keep docs and tests aligned with shipped behavior.
