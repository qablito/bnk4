"""
Ingest stage (v1).

Responsibilities:
- Enforce upload invariants (SECURITY_SPEC.md)
- Validate format and size
- Decode to internal PCM representation
- Produce canonical track metadata

No analysis logic here (no BPM, no key, no grid).
"""
