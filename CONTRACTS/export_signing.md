# Export Signing Contract

Exports are authenticated-only and use short-lived signed URLs.

Download model:
- Generation is authenticated-only.
- Download is auth-gated: requests MUST include `Authorization` for an authenticated user session.
- The `user_id` query parameter MUST match the authenticated user id (e.g. `auth.uid()`); mismatch is forbidden.

## Signed URL Format

```
GET /exports/{resource_id}?user_id={user_id}&iat={unix_ts}&expires={unix_ts}&nonce={hex16}&sig={hmac}
```

Fields:
- `resource_id`: UUID of the export resource
- `user_id`: UUID of the authenticated user
- `iat`: unix seconds (issued-at)
- `expires`: unix seconds
- `nonce`: 16 random bytes, hex-encoded (32 chars)
- `sig`: HMAC-SHA256 over all fields in order

Signing string:

```
{resource_id}|{user_id}|{iat}|{expires}|{nonce}
```

## Parameter Format Rules
- `resource_id`: UUID (RFC 4122 canonical text format)
- `user_id`: UUID (RFC 4122 canonical text format)
- `iat`: integer unix seconds (base-10)
- `expires`: integer unix seconds (base-10)
- `nonce`: 16 random bytes, hex-encoded (32 hex chars)
- `sig`: HMAC-SHA256 hex digest (64 hex chars)

## TTL Rules
- `expires - iat` MUST be <= 900 seconds.
- Expired URLs MUST be rejected.
- URLs with TTL longer than 900 seconds MUST be rejected.

Clock-skew note:
- Validators SHOULD allow a small clock skew window for `iat` vs server time (example: +/- 300 seconds). If `iat` is too far in the future, reject as malformed (400).

## Time Validation Rules
- Reject if `expires <= iat` (400).
- Reject if `expires - iat > 900` (400).
- Reject if `iat > now + skew_seconds` (400).
- Treat as expired if `expires < now - skew_seconds` (410).

## Status Codes
- 200: valid signature + not expired + authenticated + user match
- 400: malformed parameters, invalid time window, invalid formats, or `iat` too far in the future
- 401: missing/invalid authentication for the download endpoint
- 403: signature invalid OR `user_id` mismatch OR forbidden
- 410: expired URL

All error responses MUST be normalized JSON. For 429 (if applicable), include `Retry-After` and `details.retry_after_seconds`.
