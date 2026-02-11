"""
Ingest stage (v1).

Responsibilities:
- Enforce upload invariants (`docs/SECURITY_SPEC.md`)
- Validate format and size
- Decode to internal PCM representation
- Produce canonical track metadata

No analysis logic here (no BPM, no key, no grid).
"""

from .ingest import IngestLimits as IngestLimits
from .ingest import ingest_v1 as ingest_v1
from .types import DecodedAudio as DecodedAudio

__all__ = ["DecodedAudio", "IngestLimits", "ingest_v1"]
