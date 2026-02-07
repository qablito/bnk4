# Analysis Engine (v1)

This directory contains the **implementation scaffolding** for the BeetsNKeys
Analysis Engine v1.

Normative behavior is defined in:
- ANALYSIS_ENGINE_V1.md
- CONTRACTS/analysis_output.md
- SECURITY_SPEC.md

This code MUST:
- Match the v1 spec exactly
- Prefer omission over misleading outputs
- Never leak raw audio, waveforms, or blobs

Implementation order:
1. ingest
2. preprocess
3. features
4. aggregation
5. packaging

No module may bypass aggregation or packaging.
