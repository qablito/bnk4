# Security Checklist

## Authentication & Authorization
- [ ] New endpoints enforce auth middleware
- [ ] Guest tokens are device-bound using DPoP (`cnf.jkt` + DPoP JWT)
- [ ] Guest token TTL <= 1h; authed token TTL <= 24h
- [ ] `/exports/*` rejects guest access

## RLS
- [ ] RLS enabled on user tables
- [ ] Policies are deny-by-default (no permissive `qual IS NULL`)
- [ ] Ownership checks are enforced (`auth.uid()` or `cnf.jkt`)

## Upload/Analyze
- [ ] Upload size limit enforced pre-body
- [ ] Magic bytes validation for audio formats
- [ ] Analyzer limits: CPU/RAM/timeout, no network, read-only FS

## Exports
- [ ] Signed URLs include resource_id, user_id, expires, nonce, signature
- [ ] RLS pre-check before signing
- [ ] TTL <= 900s, expired => 410

## Logging & Errors
- [ ] No secrets in logs
- [ ] Errors are normalized JSON and sanitized
- [ ] 429 includes Retry-After

## Data
- [ ] Audio is temp-only (no DB/Redis audio blobs)
- [ ] Persist only hash + minimal metadata + results

# Severity Levels

| Severity | Criteria | Action |
| --- | --- | --- |
| BLOCKER | Auth bypass, RLS missing, secret exposure | Do not merge |
| CRITICAL | IDOR possible, export signing failure | Fix before merge |
| HIGH | Logging leakage, weak crypto, missing tests | Fix or follow-up issue |
| MEDIUM | Missing security headers, verbose errors | Follow-up issue |
