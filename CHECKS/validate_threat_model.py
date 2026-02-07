#!/usr/bin/env python3
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "THREAT_MODEL.md"

BANNED = [
    {
        "name": "fingerprint_hash_pop",
        "pattern": re.compile(
            r"fingerprint[-\s]*hash|fingerprint[-\s]*based|fingerprint.*pop|pop.*fingerprint", re.I
        ),
        "allow_negation": True,
        "negation_strength": "strong_only",
    },
    {
        "name": "dpop_proof_header",
        "pattern": re.compile(r"\bDPoP-Proof\b", re.I),
        "allow_negation": False,
    },
    {
        "name": "ownership_device_id",
        "pattern": re.compile(
            r"auth\.jwt\(\)\s*->>?\s*'device_id'|\bdevice_id\b.*\bownership\b|\bownership\b.*\bdevice_id\b",
            re.I,
        ),
        "allow_negation": False,
    },
    {
        "name": "redis_audio_blob_setex",
        # Flag explicit blob storage examples only (SET/SETEX/redis.set/redis.setex on audio keys).
        "pattern": re.compile(
            r"(\bSETEX\b|\bSET\b)\s+['\"]?audio(?::|\{)|\bredis\.setex\b.*audio(?::|\{)|\bredis\.set\b.*audio(?::|\{)",
            re.I,
        ),
        "allow_negation": False,
    },
    {
        "name": "permissive_rls_without_ownership",
        "pattern": re.compile(
            r"permissive.*qual\s+is\s+null|qual\s+is\s+null.*permissive|permissive.*\btrue\b|\bqual\s*=\s*true\b",
            re.I,
        ),
        "allow_negation": True,
        "negation_strength": "strong_only",
    },
    {
        "name": "test_prefix",
        "pattern": re.compile(r"\btest_", re.I),
        "allow_negation": False,
    },
    {
        "name": "tests_de_alto_impacto",
        "pattern": re.compile(r"Tests de Alto Impacto", re.I),
        "allow_negation": False,
    },
    {
        "name": "absolute_path",
        "pattern": re.compile(r"(/Users/|[A-Za-z]:\\)", re.I),
        "allow_negation": False,
    },
]

WEAK_NEGATION = re.compile(r"\b(no|not|sin)\b", re.I)
STRONG_NEGATION = re.compile(r"\b(forbid|forbidden|prohibit|prohibido|deny)\b", re.I)

LEGACY_HINT = re.compile(r"\b(legacy|deprecated)\b", re.I)

PURE_SECURITY_SPEC_REF = re.compile(r"^\s*[-*]?\s*`?SECURITY_SPEC\.md`?\s*$", re.I)


def is_pure_security_spec_reference(line: str) -> bool:
    return bool(PURE_SECURITY_SPEC_REF.match(line))


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: {TARGET} not found")
        return 1

    errors = []
    last_lines = []
    for i, raw in enumerate(TARGET.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        last_lines.append(line.lower())
        if len(last_lines) > 5:
            last_lines.pop(0)
        negated_weak = bool(WEAK_NEGATION.search(line))
        negated_strong = bool(STRONG_NEGATION.search(line))
        for rule in BANNED:
            matched = bool(rule["pattern"].search(line))
            if not matched:
                continue
            if rule["name"] == "permissive_rls_without_ownership":
                # Allow pg_policies audit queries that search for forbidden policies.
                if any("from pg_policies" in prev for prev in last_lines):
                    continue
            if rule["name"] == "ownership_device_id":
                # Allow legacy references only if explicitly called out.
                if LEGACY_HINT.search(line):
                    continue

            if rule["name"] in (
                "test_prefix",
                "tests_de_alto_impacto",
            ) and is_pure_security_spec_reference(raw):
                continue

            if rule.get("allow_negation", True):
                strength = rule.get("negation_strength", "any")
                if strength == "strong_only" and negated_strong:
                    continue
                if strength == "any" and (negated_strong or negated_weak):
                    continue
            if matched:
                errors.append((i, rule["name"], raw))

    if errors:
        print("FAILED: banned patterns found in THREAT_MODEL.md")
        for i, name, raw in errors:
            print(f"- line {i}: {name}: {raw}")
        return 1

    print("OK: THREAT_MODEL.md passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
