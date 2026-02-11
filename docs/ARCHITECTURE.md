# Architecture

## Repository Layout
- `engine/`: analysis pipeline and tests (v1).
- `apps/`: product surfaces (local API/UI; in progress).
- `docs/`: project and developer documentation.
- `scripts/`: developer helper scripts.
- `.github/`: CI workflows.

## Engine v1 Overview
Engine v1 is a deterministic, contract-first analysis pipeline.

Pipeline stages:
1. `engine/ingest`: decode + input validation + metadata extraction.
2. `engine/preprocess`: low-level signal hints (tempo and tonal evidence).
3. `engine/features`: BPM and key/mode features with conservative emission policy.
4. `engine/aggregation`: confidence policy and candidate ranking.
5. `engine/packaging`: role-based output shaping (`guest`, `free`, `pro`).

Cross-cutting rules:
- Accuracy-first: omit instead of guessing.
- Determinism: stable ordering of candidates and reason codes.
- Role safety: guest payload strips advanced diagnostics.

## Public Contract
- Public examples and v1 contract freeze: `docs/ENGINE_V1_CONTRACT.md`
- Canonical output schema and gating details: `CONTRACTS/analysis_output.md`
- Security invariants: `docs/SECURITY_SPEC.md`

## Apps Boundary
`apps/` consumes engine outputs. It must not change engine internals or contract semantics directly; changes to contract are owned by `engine/` plus contract docs/tests.
