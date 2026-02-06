"""
Ingest stage (v1).

Responsibilities:
- Enforce upload invariants (SECURITY_SPEC.md)
- Validate format and size
- Decode to internal PCM representation
- Produce canonical track metadata

No analysis logic here (no BPM, no key, no grid).
"""
from .types import DecodedAudio
from .ingest import ingest_v1, IngestLimits