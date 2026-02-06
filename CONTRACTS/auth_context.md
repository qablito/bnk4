# Auth Context Contract

This document defines the minimum JWT claims and DPoP requirements for BeetsNKeys.

Normative security invariants live in `SECURITY_SPEC.md`. This document mirrors the minimum protocol surface area.

## Token Classes

### Authenticated Token (registered user)
Required claims:
- `scope`: `"authenticated"`
- `sub`: user id (UUID)
- `iat`: issued-at (unix seconds)
- `exp`: expiry (unix seconds), `exp - iat <= 86400`

Optional:
- `role`: `"free" | "pro"`
- `aud`, `iss`

### Guest Token (device-bound strong)
Required claims:
- `scope`: `"guest"`
- `iat`: issued-at (unix seconds)
- `exp`: expiry (unix seconds), `exp - iat <= 3600`
- `cnf.jkt`: base64url JWK thumbprint of the device public key

Notes:
- Guest tokens MUST be rejected if `cnf.jkt` is missing.
- Guest tokens MUST NOT be refreshable.

## DPoP (Proof-of-Possession) Requirements
Every request that presents a guest token MUST include a `DPoP` header. The header value is a DPoP JWT signed by the device private key corresponding to `cnf.jkt`.

DPoP JWT requirements:
- Header: `typ = "dpop+jwt"`, `alg` per supported key type, and `jwk` (device public key) MUST be present
- Claims:
  - `htu`: HTTPS URI of the request (absolute URL, no fragment; canonicalization as per SECURITY_SPEC)
  - `htm`: HTTP method (uppercase)
  - `iat`: issued-at (unix seconds)
  - `jti`: unique identifier for anti-replay
  - `ath` (optional): access token hash (base64url of SHA-256 of access token)

Validation rules:
- DPoP header `jwk` MUST be present; its RFC 7638 SHA-256 thumbprint MUST equal the access token `cnf.jkt`.
- Signature MUST verify against the DPoP header `jwk`.
- `htu` and `htm` MUST match the current request.
- `iat` MUST be within an accepted clock skew window (example: +/- 300 seconds).
- `jti` MUST be unique within the anti-replay window; replays are rejected.

Proxy note:
- Behind proxies/load balancers, the server MUST compute `htu` using a trusted external origin configuration (or trusted `X-Forwarded-*` from known proxies). Do not accept arbitrary forwarded headers from the public internet.

Failure behavior:
- Missing/invalid DPoP for guest requests => 401/403 with normalized JSON error.
- Authenticated users do not require DPoP unless explicitly enabled in the future.
