# Export Sharing Contract (Design Reserved)

This document reserves a future share-link feature that is explicitly bearer-accessed. It is OUT OF SCOPE for current implementation.

## Purpose
Allow an authenticated owner to create a revocable, expiring link that grants access to a specific export to recipients without requiring them to authenticate.

## Conceptual Data Model (Future)
- `share_id` (UUID): primary identifier (unguessable)
- `export_id` (UUID): target export
- `owner_user_id` (UUID): creator/owner
- `created_at` (timestamp)
- `expires_at` (timestamp, optional but recommended)
- `revoked_at` (timestamp, nullable)
- `max_downloads` (int, optional)
- `audience` (enum): `anyone_with_link` | `allowlist`
- `scope` (enum): `download_only` (future extension: `view_metadata`)

## Endpoint Shape (Future, High-Level)
- `POST /exports/{export_id}/share` (auth required): create share link
- `DELETE /export-shares/{share_id}` (auth required): revoke
- `GET /export-shares/{share_id}/download` (bearer): download by share id

Bearer access definition:
- No `Authorization` header required.
- Possession of `share_id` (plus any associated signature/token, if introduced) is the bearer credential.

## Security Constraints (Future)
- Anti-enumeration:
  - Use unguessable UUIDs, do not use sequential ids.
  - Apply rate limiting on share download endpoints.
  - Add audit logging (creation, download, revoke).
- Expiry and revocation:
  - If `revoked_at` is set: deny (403 or 404 depending on disclosure policy).
  - If `expires_at` is in the past: deny as expired (410).
- Optional controls:
  - `max_downloads` enforced with atomic counters.
  - `audience=allowlist` requires recipient validation (mechanism defined later).

## Non-Goals (Current)
- No implementation is provided here.
- Current export downloads remain auth-gated; bearer-only access is reserved for this share-link contract.

