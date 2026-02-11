# BeetsNKeys (bnk4) Security Specification

**Versión:** 1.0
**Última actualización:** 2026-02-05
**Scope:** Security invariants, error model, y test mapping. NO incluye implementación de backend.

---

## 1. Modelo de Errores JSON (Normalizado)

### 1.1 Formato Obligatorio

Todas las respuestas de error (4xx, 5xx) DEBEN ser JSON con la siguiente estructura:

```json
{
  "error": "ERROR_CODE",
  "message": "Human-readable description",
  "details": {},
  "request_id": "uuid-v4"
}
```

### 1.2 Campos

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `error` | string | ✅ | Código de error en UPPER_SNAKE_CASE (sin espacios, sin puntos) |
| `message` | string | ✅ | Descripción legible para humanos (sin información sensible) |
| `details` | object | ⚠️ | Contexto adicional estructurado (opcional, NUNCA incluye secrets) |
| `request_id` | string | ✅ | UUID v4 para correlación con logs |

### 1.3 Códigos de Error Definidos

#### Autenticación (401)
```json
{
  "error": "AUTH_TOKEN_MISSING",
  "message": "Authorization header required",
  "details": {},
  "request_id": "..."
}
```
```json
{
  "error": "AUTH_TOKEN_INVALID",
  "message": "Token signature verification failed",
  "details": {},
  "request_id": "..."
}
```
```json
{
  "error": "AUTH_TOKEN_EXPIRED",
  "message": "Token has expired",
  "details": {"expired_at": 1704113280},
  "request_id": "..."
}
```
```json
{
  "error": "AUTH_DPOP_MISSING",
  "message": "DPoP header required for guest tokens",
  "details": {},
  "request_id": "..."
}
```
```json
{
  "error": "AUTH_DPOP_INVALID",
  "message": "DPoP proof validation failed",
  "details": {"reason": "signature_mismatch"},
  "request_id": "..."
}
```
```json
{
  "error": "AUTH_DPOP_REPLAY",
  "message": "DPoP jti already used",
  "details": {},
  "request_id": "..."
}
```

#### Autorización (403)
```json
{
  "error": "AUTHZ_FORBIDDEN",
  "message": "Insufficient permissions",
  "details": {},
  "request_id": "..."
}
```
```json
{
  "error": "AUTHZ_GUEST_NOT_ALLOWED",
  "message": "This endpoint requires authenticated user",
  "details": {"required_scope": "user"},
  "request_id": "..."
}
```

#### Recurso No Encontrado (404)
```json
{
  "error": "RESOURCE_NOT_FOUND",
  "message": "Requested resource does not exist or access denied",
  "details": {},
  "request_id": "..."
}
```

**Nota:** 404 se usa también cuando RLS oculta un recurso (no exponer existencia).

#### Rate Limiting (429)
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Too many requests",
  "details": {
    "retry_after_seconds": 60,
    "limit": "5 requests per hour",
    "scope": "analyze_endpoint"
  },
  "request_id": "..."
}
```

**Headers adicionales obligatorios:**
- `Retry-After: 60` (segundos)
- `X-RateLimit-Limit: 5`
- `X-RateLimit-Remaining: 0`
- `X-RateLimit-Reset: 1704113340` (unix timestamp)

#### Validación de Input (400)
```json
{
  "error": "VALIDATION_FAILED",
  "message": "Request validation failed",
  "details": {
    "field": "audio_file",
    "reason": "invalid_format"
  },
  "request_id": "..."
}
```
```json
{
  "error": "FILE_TOO_LARGE",
  "message": "Upload exceeds maximum size",
  "details": {
    "max_size_bytes": 52428800,
    "received_bytes": 60000000
  },
  "request_id": "..."
}
```
```json
{
  "error": "FILE_INVALID_FORMAT",
  "message": "Audio format not supported",
  "details": {
    "allowed_formats": ["wav", "mp3", "flac", "ogg"],
    "detected": "unknown"
  },
  "request_id": "..."
}
```

#### Timeout (408)
```json
{
  "error": "ANALYZE_TIMEOUT",
  "message": "Analysis exceeded time limit",
  "details": {
    "timeout_seconds": 60
  },
  "request_id": "..."
}
```

#### Export Errors (410, 400)
```json
{
  "error": "EXPORT_EXPIRED",
  "message": "Signed URL has expired",
  "details": {},
  "request_id": "..."
}
```
```json
{
  "error": "EXPORT_INVALID_SIGNATURE",
  "message": "URL signature verification failed",
  "details": {},
  "request_id": "..."
}
```

#### Errores Internos (500)
```json
{
  "error": "INTERNAL_ERROR",
  "message": "An internal error occurred",
  "details": {},
  "request_id": "..."
}
```
```json
{
  "error": "DATABASE_ERROR",
  "message": "Database operation failed",
  "details": {},
  "request_id": "..."
}
```

**⚠️ CRITICAL:** En producción, errores 5xx NUNCA incluyen:
- Stack traces
- Paths de archivos
- Nombres de variables
- Mensajes SQL raw
- Versiones de librerías

### 1.4 Reglas de Sanitización en Producción

**Prohibido en `message` o `details`:**
- Tokens (completos o parciales)
- Passwords
- API keys
- Device fingerprints completos (`cnf.jkt`)
- User emails/IDs en mensajes de error público
- Stack traces
- Paths absolutos del filesystem
- Nombres de tablas/columnas de DB
- IP addresses (salvo en logs internos)

**Permitido en `details`:**
- Límites numéricos (max_size, timeout)
- Enums de valores permitidos (allowed_formats)
- Timestamps públicos (expires_at)
- Retry delays (retry_after_seconds)

---

## 2. Security Invariants (NO NEGOCIABLES)

### 2.1 AUTH: Autenticación

#### AUTH-01: Guest Token Binding (cnf.jkt)
**Regla:** Todo token guest DEBE incluir claim `cnf.jkt` (SHA-256 thumbprint de la clave pública del dispositivo). Servidor DEBE rechazar tokens guest sin `cnf.jkt`.

**Formato JWT mínimo:**
```json
{
  "scope": "guest",
  "iat": 1704113280,
  "exp": 1704116880,
  "cnf": {
    "jkt": "0ZcOCORZNYy-DWpqq30jZyJGHTN0d2HglBV3uiguA4I"
  }
}
```

**Verificación:**
- Parsear JWT, extraer `cnf.jkt`
- Si `scope == "guest"` y `cnf.jkt` ausente → **401 AUTH_TOKEN_INVALID**
- Almacenar `jkt` en contexto de request para validación DPoP

**Componente:** API (auth middleware)
**Test:** `test_guest_token_requires_cnf_jkt`

---

#### AUTH-02: Proof-of-Possession (DPoP JWT)
**Regla:** Todo request con token guest DEBE incluir header `DPoP` con un JWT firmado por la clave privada correspondiente a `cnf.jkt`. Servidor DEBE validar:
1. Firma del DPoP JWT con clave pública derivada de `cnf.jkt`
2. Claims: `htu`, `htm`, `iat`, `jti` (y opcionalmente `ath`)
3. Anti-replay: `jti` único en ventana temporal (ej. 60s)
4. Canonicalizacion de `htu` consistente entre cliente y servidor
5. `jwk` presente en el header del DPoP JWT y consistente con `cnf.jkt`

**Formato DPoP JWT:**
```json
{
  "typ": "dpop+jwt",
  "alg": "ES256",
  "jwk": { /* clave pública del dispositivo */ }
}
{
  "jti": "uuid-v4",
  "htm": "POST",
  "htu": "https://api.beetsnkeys.com/analyze",
  "iat": 1704113280,
  "ath": "sha256-hash-of-access-token"  // opcional pero recomendado
}
```

**Validación:**
1. Extraer header `DPoP`
2. Parsear como JWT, requerir `jwk` en el header del DPoP JWT
3. Calcular el JWK thumbprint (RFC 7638, SHA-256, base64url) del `jwk` y verificar `thumbprint == cnf.jkt` del access token
4. Validar firma del DPoP JWT usando el `jwk` del header
5. Validar `htm` == método HTTP actual (uppercase)
6. Canonicalizar la URL del request y validar `htu` == `htu_canonical`
7. Validar `iat` dentro de ventana aceptable (ej. ±5min)
8. Verificar `jti` no usado previamente (anti-replay store con TTL=60s)
9. Si falla cualquier paso → **401 AUTH_DPOP_INVALID** o **401 AUTH_DPOP_REPLAY**

**Canonicalizacion `htu` (normativa):**
- `htu` DEBE ser la URL absoluta del request, sin fragment (`#...`).
- `htu` DEBE incluir query string si existe, sin reordenar parametros.
- `scheme` y `host` se comparan en lowercase.
- Puertos default se omiten: `:443` para `https`, `:80` para `http`.
- El `path` se compara tal como fue recibido (sin percent-decode ni re-encode).
- El servidor DEBE construir `htu_canonical` desde un origen confiable.
  - Si esta detras de proxy, solo confiar en `X-Forwarded-*` desde proxies de confianza.

**Componente:** API (auth middleware)
**Test:** `test_guest_requires_dpop_and_validates_claims`, `test_dpop_replay_rejected`

---

#### AUTH-03: Token TTL Máximo
**Regla:**
- Tokens guest: `exp - iat <= 3600` (1 hora)
- Tokens autenticados: `exp - iat <= 86400` (24 horas)
- NO se permite refresh de tokens guest

**Verificación:**
```python
if token.scope == "guest":
    assert token.exp - token.iat <= 3600, "AUTH_TOKEN_INVALID: TTL exceeded"
else:
    assert token.exp - token.iat <= 86400, "AUTH_TOKEN_INVALID: TTL exceeded"

if token.exp < now():
    return 401, "AUTH_TOKEN_EXPIRED"
```

**Componente:** API (auth middleware)
**Test:** `test_token_ttl_limits_guest_and_authed`, `test_expired_token_rejected`

---

#### AUTH-04: Export Endpoint Autenticación
**Regla:** Todos los endpoints bajo `/exports/*` DEBEN rechazar requests con `scope=guest`. Solo usuarios autenticados con sesión válida pueden generar exports.

**Verificación:**
```python
if request.path.startswith("/exports/") and token.scope == "guest":
    return 403, "AUTHZ_GUEST_NOT_ALLOWED"
```

**Componente:** API (exports routes)
**Test:** `test_guest_cannot_access_exports`

---

### 2.2 RLS: Row-Level Security

#### RLS-01: Universal RLS Enforcement
**Regla:** TODAS las tablas que contienen datos de usuario DEBEN tener RLS habilitado (`ALTER TABLE ... ENABLE ROW LEVEL SECURITY`). Tablas críticas:
- `public.audio_hashes`
- `public.analysis_results`
- `public.exports`

**Verificación SQL:**
```sql
SELECT tablename
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('audio_hashes', 'analysis_results', 'exports')
  AND rowsecurity = false;
-- Resultado esperado: 0 filas
```

**Componente:** DB (migrations)
**Test:** `test_rls_enabled_on_core_tables`

---

#### RLS-02: Deny-by-Default Policies
**Regla:** Todas las políticas RLS DEBEN seguir deny-by-default. Sin política explícita que permita acceso, el acceso DEBE ser denegado. **Prohibido:** políticas PERMISSIVE con `qual IS NULL`.

**Verificación SQL:**
```sql
SELECT schemaname, tablename, policyname, qual
FROM pg_policies
WHERE permissive = 'PERMISSIVE'
  AND qual IS NULL
  AND schemaname = 'public';
-- Resultado esperado: 0 filas
```

**Componente:** DB (migrations)
**Test:** `test_no_permissive_policies_without_qual`

---

#### RLS-03: Ownership-Based Policies
**Regla:** Políticas RLS DEBEN verificar ownership:
- **Autenticados:** `auth.uid() = user_id`
- **Guests:** `auth.jwt()->'cnf'->>'jkt' = device_jkt`

**NO se permite:** condiciones `true` o políticas sin verificación de ownership.

**Ejemplo válido (autenticados):**
```sql
CREATE POLICY "Users can only see their own analyses"
ON analysis_results FOR SELECT
USING (auth.uid() = user_id);
```

**Ejemplo válido (guests):**
```sql
CREATE POLICY "Guests can only see their device analyses"
ON analysis_results FOR SELECT
USING (auth.jwt()->'cnf'->>'jkt' = device_jkt);
```

**Verificación SQL (buscar políticas permisivas sin ownership):**
```sql
SELECT policyname, qual
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('audio_hashes', 'analysis_results', 'exports')
  AND qual !~ '(auth\.uid|auth\.jwt.*cnf.*jkt)';
-- Resultado esperado: 0 filas (excepto políticas admin justificadas)
```

**Componente:** DB (migrations)
**Test:** `test_rls_ownership_enforced_authed_and_guest`

---

### 2.3 UPLOAD: Validación de Subidas

#### UPLOAD-01: File Size Limit
**Regla:** Audio uploads DEBEN rechazarse si exceden 50MB (52,428,800 bytes). Validación DEBE ocurrir **antes** de leer el cuerpo completo del request.

**Verificación:**
```python
content_length = request.headers.get("Content-Length")
if content_length and int(content_length) > 52_428_800:
    return 413, {
        "error": "FILE_TOO_LARGE",
        "message": "Upload exceeds maximum size",
        "details": {"max_size_bytes": 52428800}
    }
```

**Stream processing:** Abortar lectura si bytes acumulados > límite.

**Componente:** API (upload endpoint)
**Test:** `test_upload_rejects_oversize`

---

#### UPLOAD-02: Magic Bytes Validation
**Regla:** Archivos DEBEN validarse mediante **magic bytes** (primeros 8-16 bytes). Extensión de archivo NO es suficiente. Formatos permitidos: WAV, MP3, FLAC, OGG.

**Whitelist de magic bytes:**
```python
ALLOWED_MAGIC = {
    b'RIFF': {'offset': 8, 'marker': b'WAVE', 'format': 'wav'},
    b'ID3': {'offset': 0, 'marker': b'ID3', 'format': 'mp3'},
    b'\xff\xfb': {'offset': 0, 'marker': b'\xff\xfb', 'format': 'mp3'},
    b'\xff\xf3': {'offset': 0, 'marker': b'\xff\xf3', 'format': 'mp3'},
    b'fLaC': {'offset': 0, 'marker': b'fLaC', 'format': 'flac'},
    b'OggS': {'offset': 0, 'marker': b'OggS', 'format': 'ogg'}
}
```

**Verificación:**
```python
header = file.read(16)
detected_format = detect_audio_format(header)
if detected_format not in ['wav', 'mp3', 'flac', 'ogg']:
    return 400, {
        "error": "FILE_INVALID_FORMAT",
        "message": "Audio format not supported",
        "details": {"allowed_formats": ["wav", "mp3", "flac", "ogg"]}
    }
```

**Componente:** API (upload validation)
**Test:** `test_upload_magic_bytes_validation`, `test_upload_rejects_fake_extension`

---

#### UPLOAD-03: Filename Sanitization
**Regla:** Nombres de archivo originales DEBEN ser descartados y reemplazados por UUIDs. Path traversal sequences DEBEN ser bloqueados explícitamente.

**Prohibido en nombres de archivo:**
- `..` (path traversal)
- `/`, `\` (separadores de path)
- `%00` (null byte)
- Control characters (ASCII < 32)

**Storage key generado:**
```python
storage_key = f"{uuid4()}.{validated_extension}"
# Ejemplo: "a3f8b2c1-4e5d-6f7a-8b9c-0d1e2f3a4b5c.wav"
```

**Verificación:**
```python
if any(char in original_filename for char in ['..', '/', '\\', '\x00']):
    return 400, {
        "error": "VALIDATION_FAILED",
        "message": "Invalid filename",
        "details": {"field": "filename"}
    }
```

**Componente:** API (upload handler) + Storage layer
**Test:** `test_upload_filename_sanitization`, `test_upload_blocks_path_traversal`

---

### 2.4 ANALYZE: Container de Análisis

#### ANALYZE-01: Container Resource Limits
**Regla:** Analyzer container DEBE tener límites **hard** configurados:
- **CPU:** 1 core (1000m)
- **RAM:** 512MB
- **Timeout:** 60 segundos

Exceder límites DEBE terminar el proceso sin analizar.

**Verificación (Docker Compose):**
```yaml
services:
  analyzer:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
    stop_grace_period: 5s
```

**Verificación (Kubernetes):**
```yaml
resources:
  limits:
    cpu: "1000m"
    memory: "512Mi"
  requests:
    cpu: "500m"
    memory: "256Mi"
```

**Timeout enforcement:** Wrapper script con `timeout 60s` o signal SIGKILL después de 60s.

**Componente:** Analyzer (container config)
**Test:** `test_analyzer_resource_limits`, `test_analyzer_timeout_enforced`

---

#### ANALYZE-02: Network Isolation
**Regla:** Analyzer container DEBE ejecutarse en red aislada sin acceso a internet ni servicios internos. **NO DNS, NO egress.**

**Verificación (Docker):**
```yaml
services:
  analyzer:
    network_mode: none
```

**Verificación (Kubernetes NetworkPolicy):**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: analyzer-deny-all-egress
spec:
  podSelector:
    matchLabels:
      app: analyzer
  policyTypes:
    - Egress
  egress: []  # Deny all
```

**Excepción:** Si se necesita comunicar resultados, permitir egress SOLO al servicio backend específico (no internet).

**Componente:** Analyzer (network config)
**Test:** `test_analyzer_no_network_egress`, `test_analyzer_dns_blocked`

---

#### ANALYZE-03: Filesystem Restrictions
**Regla:** Analyzer container DEBE montar filesystem como **read-only** excepto `/tmp` (tmpfs). NO se permite escritura en paths arbitrarios.

**Verificación (Docker):**
```yaml
services:
  analyzer:
    read_only: true
    tmpfs:
      - /tmp:size=100m,noexec,nosuid,nodev
```

**Verificación (Kubernetes):**
```yaml
securityContext:
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 65534  # nobody
  capabilities:
    drop:
      - ALL
```

**Componente:** Analyzer (container config)
**Test:** `test_analyzer_readonly_fs`, `test_analyzer_cannot_write_outside_tmp`

---

#### ANALYZE-04: Input Sanitization
**Regla:** Antes de pasar audio al analyzer, DEBE validarse:
1. **NO ZIP bombs:** compression ratio < 100
2. **NO polyglots:** un solo formato válido (sin múltiples magic bytes)
3. **NO trailing data:** archivo termina donde debe

**Verificación:**
```python
# ZIP bomb detection
compressed_size = len(file_data)
uncompressed_size = detect_uncompressed_size(file_data)
if uncompressed_size / compressed_size > 100:
    return 400, {
        "error": "VALIDATION_FAILED",
        "message": "Compression ratio exceeds limit",
        "details": {"reason": "zip_bomb_suspected"}
    }

# Polyglot detection
magic_bytes = file_data[:16]
detected_formats = detect_all_formats(magic_bytes)
if len(detected_formats) > 1:
    return 400, {
        "error": "FILE_INVALID_FORMAT",
        "message": "Multiple file formats detected",
        "details": {"reason": "polyglot"}
    }
```

**Componente:** API (pre-analyzer validation)
**Test:** `test_analyzer_input_sanitization`, `test_analyzer_rejects_zip_bombs`, `test_analyzer_rejects_polyglots`

---

### 2.5 EXPORT: Exports Firmados
**Contrato:** ver `CONTRACTS/export_signing.md` (auth-gated downloads). Links bearer-only quedan reservados para `CONTRACTS/export_sharing.md` (design reserved).

#### EXPORT-01: Signed URL Generation
**Regla:** Export URLs DEBEN incluir:
- `resource_id` (UUID del análisis)
- `user_id` (UUID del usuario)
- `iat` (unix timestamp de emision)
- `expires` (unix timestamp, <= 15 min desde emisión)
- `nonce` (16 bytes aleatorios, hex)
- `sig` (HMAC-SHA256 sobre `resource_id|user_id|iat|expires|nonce`)

**Formato URL:**
```
/exports/{resource_id}?user_id={uid}&iat={iat}&expires={ts}&nonce={hex}&sig={hmac}
```

**Generación:**
```python
import hmac
import hashlib
import secrets
from time import time

iat = int(time())
expires = iat + 900  # 15 min
nonce = secrets.token_hex(16)
message = f"{resource_id}|{user_id}|{iat}|{expires}|{nonce}"
sig = hmac.new(
    key=SECRET_KEY.encode(),
    msg=message.encode(),
    digestmod=hashlib.sha256
).hexdigest()

url = f"/exports/{resource_id}?user_id={user_id}&iat={iat}&expires={expires}&nonce={nonce}&sig={sig}"
```

**Componente:** API (export signing)
**Test:** `test_export_signed_url_fields_and_signature`, `test_export_invalid_signature_rejected`

---

#### EXPORT-02: RLS Pre-Check
**Regla:** Antes de generar signed URL, DEBE ejecutarse query **RLS-enforced** para verificar ownership. Generar URL sin verificación está **prohibido**.

**Verificación:**
```python
# Supabase client con contexto de usuario actual
result = supabase.from_('analysis_results')\
    .select('id')\
    .eq('id', resource_id)\
    .single()\
    .execute()

if not result.data:
    # RLS bloqueó acceso o recurso no existe
    return 404, {"error": "RESOURCE_NOT_FOUND", "message": "..."}

# Solo si pasa RLS, generar URL
signed_url = generate_signed_url(resource_id, user_id)
```

**CRÍTICO:** NO usar queries con service role que bypass RLS.

**Componente:** API (export endpoint)
**Test:** `test_export_requires_rls_precheck`, `test_export_idor_blocked`

---

#### EXPORT-03: TTL Enforcement
**Regla:** Export signed URLs DEBEN expirar en máximo 15 minutos (900s). Backend DEBE rechazar:
- URLs expiradas (`expires < now()`) -> 410
- URLs donde `expires - iat > 900s` -> 400
- URLs donde `iat` esta en el futuro mas alla de skew permitido -> 400

**Verificación:**
```python
now = int(time())

# Expirado
if expires < now:
    return 410, {"error": "EXPORT_EXPIRED", "message": "Signed URL has expired"}

# TTL demasiado largo
if expires - iat > 900:
    return 400, {
        "error": "VALIDATION_FAILED",
        "message": "Export URL TTL exceeds maximum",
        "details": {"max_ttl_seconds": 900}
    }
```

**Componente:** API/Storage (export download handler)
**Test:** `test_export_ttl_enforced`, `test_export_expired_url_rejected`

---

### 2.6 LOGGING: Sanitización de Logs

#### LOGGING-01: Secrets Sanitization
**Regla:** Logs NUNCA contienen:
- Tokens completos (mostrar solo últimos 4 chars o hash)
- Passwords
- API keys
- Device fingerprints completos (`cnf.jkt` completo, solo hash)
- Audio content (binario)

**Sanitización obligatoria:**
```python
import re

def sanitize_log(message: str) -> str:
    # Tokens (Bearer ...)
    message = re.sub(
        r'(Bearer\s+)([A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_]+)',
        r'\1****',
        message
    )
    # API keys
    message = re.sub(
        r'(api[_-]?key["\s:=]+)([^\s"]+)',
        r'\1****',
        message,
        flags=re.IGNORECASE
    )
    # Passwords
    message = re.sub(
        r'(password["\s:=]+)([^\s"]+)',
        r'\1****',
        message,
        flags=re.IGNORECASE
    )
    return message
```

**Componente:** API (logging middleware)
**Test:** `test_logs_do_not_emit_secrets`, `test_tokens_sanitized_in_logs`

---

#### LOGGING-02: Error Message Sanitization
**Regla:** Error responses en producción NO incluyen:
- Stack traces
- Paths absolutos del filesystem
- Versiones de librerías
- Mensajes SQL raw
- Nombres de tablas/columnas

**Producción:**
```python
try:
    # operación
except Exception as e:
    logger.error(f"Internal error: {type(e).__name__}", exc_info=True)  # Log completo interno
    return 500, {
        "error": "INTERNAL_ERROR",
        "message": "An internal error occurred",
        "details": {},
        "request_id": request_id
    }
```

**Desarrollo (solo en entorno no-producción):**
```python
return 500, {
    "error": "INTERNAL_ERROR",
    "message": str(e),
    "details": {"traceback": traceback.format_exc()},
    "request_id": request_id
}
```

**Componente:** API (error handlers)
**Test:** `test_errors_are_sanitized`, `test_no_stack_traces_in_prod`

---

### 2.7 RATE: Rate Limiting

#### RATE-01: Multi-Layer Rate Limiting
**Regla:** Rate limiting DEBE aplicarse en 3 capas:
1. **IP:** 100 req/min (todos los endpoints)
2. **User:** 50 req/min (autenticados)
3. **Endpoint crítico:** `/analyze` tiene límites específicos por rol

**Verificación:**
```python
# Layer 1: IP
ip_key = f"rate:ip:{client_ip}"
if redis.incr(ip_key) > 100:
    return 429, rate_limit_error("IP limit", retry_after=60)
redis.expire(ip_key, 60)

# Layer 2: User (si autenticado)
if user_id:
    user_key = f"rate:user:{user_id}"
    if redis.incr(user_key) > 50:
        return 429, rate_limit_error("User limit", retry_after=60)
    redis.expire(user_key, 60)
```

**Headers de respuesta:**
- `X-RateLimit-Limit: 100`
- `X-RateLimit-Remaining: 42`
- `X-RateLimit-Reset: 1704113340` (unix timestamp)

**Componente:** API (rate limit middleware)
**Test:** `test_rate_limits_multi_layer`, `test_rate_limit_headers_present`

---

#### RATE-02: Analyze Endpoint Restriction (Role-Based)
**Regla:** `/analyze` endpoint DEBE limitar requests por rol:
- **Guest:** 2 requests / hora
- **Free:** 5 requests / hora (o según plan de producto)
- **Pro:** 50 requests / hora (o según plan de producto)

**Nota:** Valores exactos definidos por roles de BeetsNKeys (producto). Esta spec define la estructura, no los números finales.

**Verificación:**
```python
role = token.get("role", "guest")
limits = {
    "guest": (2, 3600),     # 2 req / 1 hora
    "free": (5, 3600),      # 5 req / 1 hora
    "pro": (50, 3600)       # 50 req / 1 hora
}

limit, window = limits[role]
key = f"rate:analyze:{user_id or device_jkt}"
count = redis.incr(key)
if count == 1:
    redis.expire(key, window)
if count > limit:
    return 429, {
        "error": "RATE_LIMIT_EXCEEDED",
        "message": "Analysis rate limit exceeded",
        "details": {
            "limit": f"{limit} requests per {window} seconds",
            "scope": "analyze_endpoint",
            "retry_after_seconds": redis.ttl(key)
        }
    }
```

**Componente:** API (analyze endpoint)
**Test:** `test_rate_limits_role_based`, `test_guest_analyze_limit`, `test_free_analyze_limit`

---

#### RATE-03: 429 Response Format
**Regla:** Respuestas 429 DEBEN incluir:
- Header `Retry-After` (segundos)
- JSON normalizado según modelo de errores
- `details.retry_after_seconds` (para parsing programático)

**Ejemplo:**
```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704116880
Content-Type: application/json

{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Analysis rate limit exceeded",
  "details": {
    "limit": "5 requests per 3600 seconds",
    "scope": "analyze_endpoint",
    "retry_after_seconds": 3600
  },
  "request_id": "a3f8b2c1-4e5d-6f7a-8b9c-0d1e2f3a4b5c"
}
```

**Componente:** API (rate limit middleware)
**Test:** `test_429_includes_retry_after_and_json`

---

### 2.8 DATA: Persistencia de Datos

#### DATA-01: Audio Ephemeral Storage
**Regla:** Audio SOLO en storage efímero (tmpfs, ephemeral volume, object storage con TTL). **Prohibido** guardar audio binario en:
- PostgreSQL (Supabase)
- Redis (excepto metadata con TTL)
- Cualquier storage permanente

**Verificación DB:**
```sql
-- Buscar columnas sospechosas en tablas críticas
SELECT table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('audio_hashes', 'analysis_results', 'exports')
  AND (column_name ILIKE '%audio%'
       OR column_name ILIKE '%content%'
       OR column_name ILIKE '%blob%'
       OR data_type = 'bytea');
-- Resultado esperado: 0 filas (solo hash TEXT permitido)
```

**Cleanup job:** Background task cada 1h que purga archivos temporales > 24h.

**Componente:** Storage layer + Background jobs
**Test:** `test_no_audio_blob_in_db_or_redis`, `test_audio_ephemeral_cleanup`

---

#### DATA-02: Hash-Only Persistence
**Regla:** En DB solo se persiste:
- SHA-256 hash del audio (para deduplicación)
- Resultados de análisis (JSON)
- Metadata mínimo

**NO persistir:**
- Paths de archivos (riesgo de path traversal)
- URLs de storage (pueden cambiar)
- Audio content

**Schema esperado:**
```sql
CREATE TABLE audio_hashes (
  hash TEXT PRIMARY KEY,           -- SHA-256 del audio
  duration_seconds INTEGER,
  format TEXT,
  sample_rate INTEGER,
  bitrate INTEGER,
  channels INTEGER,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- PROHIBIDAS estas columnas:
-- audio_content BYTEA,
-- file_path TEXT,
-- storage_url TEXT
```

**Componente:** DB schema
**Test:** `test_only_hash_and_results_persisted`, `test_no_audio_content_column_exists`

---

#### DATA-03: Metadata Minimization
**Regla:** Metadata persistida DEBE limitarse a campos técnicos necesarios:
- `duration` (segundos)
- `format` (wav, mp3, flac, ogg)
- `sample_rate` (Hz)
- `bitrate` (kbps)
- `channels` (1=mono, 2=stereo)

**Prohibido persistir:**
- Metadata EXIF (geolocation, device model, etc.)
- Original filename
- User agent del upload
- IP address del uploader
- Cualquier PII

**Verificación:**
```python
ALLOWED_METADATA = ['duration', 'format', 'sample_rate', 'bitrate', 'channels']

def sanitize_metadata(raw_metadata: dict) -> dict:
    return {k: v for k, v in raw_metadata.items() if k in ALLOWED_METADATA}
```

**Componente:** API (metadata extraction)
**Test:** `test_metadata_minimization`, `test_exif_stripped_from_metadata`

---

## 3. Invariant → Component → Test Mapping

| Invariant ID | Componente Futuro | Test Name | Prioridad |
|--------------|-------------------|-----------|-----------|
| **AUTH-01** | API (auth middleware) | `test_guest_token_requires_cnf_jkt` | CRÍTICA |
| **AUTH-02** | API (auth middleware) | `test_guest_requires_dpop_and_validates_claims` | CRÍTICA |
| **AUTH-02** | API (auth middleware) | `test_dpop_replay_rejected` | CRÍTICA |
| **AUTH-03** | API (auth middleware) | `test_token_ttl_limits_guest_and_authed` | ALTA |
| **AUTH-03** | API (auth middleware) | `test_expired_token_rejected` | ALTA |
| **AUTH-04** | API (exports routes) | `test_guest_cannot_access_exports` | CRÍTICA |
| **RLS-01** | DB (migrations) | `test_rls_enabled_on_core_tables` | CRÍTICA |
| **RLS-02** | DB (migrations) | `test_no_permissive_policies_without_qual` | CRÍTICA |
| **RLS-03** | DB (migrations) | `test_rls_ownership_enforced_authed_and_guest` | CRÍTICA |
| **RLS-03** | DB (E2E) | `test_idor_analysis_results` | CRÍTICA |
| **RLS-03** | DB (E2E) | `test_direct_db_query_respects_rls` | CRÍTICA |
| **UPLOAD-01** | API (upload endpoint) | `test_upload_rejects_oversize` | ALTA |
| **UPLOAD-02** | API (upload validation) | `test_upload_magic_bytes_validation` | CRÍTICA |
| **UPLOAD-02** | API (upload validation) | `test_upload_rejects_fake_extension` | CRÍTICA |
| **UPLOAD-03** | API + Storage | `test_upload_filename_sanitization` | ALTA |
| **UPLOAD-03** | API + Storage | `test_upload_blocks_path_traversal` | CRÍTICA |
| **ANALYZE-01** | Analyzer (container) | `test_analyzer_resource_limits` | ALTA |
| **ANALYZE-01** | Analyzer (container) | `test_analyzer_timeout_enforced` | ALTA |
| **ANALYZE-02** | Analyzer (network) | `test_analyzer_no_network_egress` | CRÍTICA |
| **ANALYZE-02** | Analyzer (network) | `test_analyzer_dns_blocked` | ALTA |
| **ANALYZE-03** | Analyzer (container) | `test_analyzer_readonly_fs` | ALTA |
| **ANALYZE-03** | Analyzer (container) | `test_analyzer_cannot_write_outside_tmp` | ALTA |
| **ANALYZE-04** | API (pre-validation) | `test_analyzer_input_sanitization` | ALTA |
| **ANALYZE-04** | API (pre-validation) | `test_analyzer_rejects_zip_bombs` | CRÍTICA |
| **ANALYZE-04** | API (pre-validation) | `test_analyzer_rejects_polyglots` | ALTA |
| **EXPORT-01** | API (export signing) | `test_export_signed_url_fields_and_signature` | CRÍTICA |
| **EXPORT-01** | API (export signing) | `test_export_invalid_signature_rejected` | CRÍTICA |
| **EXPORT-02** | API (export endpoint) | `test_export_requires_rls_precheck` | CRÍTICA |
| **EXPORT-02** | API (export endpoint) | `test_export_idor_blocked` | CRÍTICA |
| **EXPORT-03** | API/Storage (download) | `test_export_ttl_enforced` | ALTA |
| **EXPORT-03** | API/Storage (download) | `test_export_expired_url_rejected` | ALTA |
| **LOGGING-01** | API (logging middleware) | `test_logs_do_not_emit_secrets` | CRÍTICA |
| **LOGGING-01** | API (logging middleware) | `test_tokens_sanitized_in_logs` | ALTA |
| **LOGGING-02** | API (error handlers) | `test_errors_are_sanitized` | ALTA |
| **LOGGING-02** | API (error handlers) | `test_no_stack_traces_in_prod` | CRÍTICA |
| **RATE-01** | API (rate middleware) | `test_rate_limits_multi_layer` | ALTA |
| **RATE-01** | API (rate middleware) | `test_rate_limit_headers_present` | MEDIA |
| **RATE-02** | API (analyze endpoint) | `test_rate_limits_role_based` | ALTA |
| **RATE-02** | API (analyze endpoint) | `test_guest_analyze_limit` | ALTA |
| **RATE-02** | API (analyze endpoint) | `test_free_analyze_limit` | MEDIA |
| **RATE-03** | API (rate middleware) | `test_429_includes_retry_after_and_json` | MEDIA |
| **DATA-01** | Storage + DB | `test_no_audio_blob_in_db_or_redis` | CRÍTICA |
| **DATA-01** | Background jobs | `test_audio_ephemeral_cleanup` | ALTA |
| **DATA-02** | DB schema | `test_only_hash_and_results_persisted` | CRÍTICA |
| **DATA-02** | DB schema | `test_no_audio_content_column_exists` | CRÍTICA |
| **DATA-03** | API (metadata) | `test_metadata_minimization` | ALTA |
| **DATA-03** | API (metadata) | `test_exif_stripped_from_metadata` | ALTA |

---

## 4. Test Implementation Guidelines

### 4.1 Prioridad de Tests

**CRÍTICA (debe pasar antes de merge):**
- Auth bypass (AUTH-01, AUTH-02, AUTH-04)
- RLS bypass (RLS-01, RLS-02, RLS-03)
- IDOR (RLS-03 E2E tests)
- Malicious uploads (UPLOAD-02, ANALYZE-04)
- Export security (EXPORT-01, EXPORT-02)
- Secret leakage (LOGGING-01, LOGGING-02)
- Data persistence (DATA-01, DATA-02)

**ALTA (debe pasar antes de release):**
- Token TTL (AUTH-03)
- File size limits (UPLOAD-01)
- Container sandboxing (ANALYZE-01, ANALYZE-02, ANALYZE-03)
- Rate limiting (RATE-01, RATE-02)

**MEDIA (nice to have):**
- Rate limit headers (RATE-01)
- 429 format (RATE-03)

### 4.2 Test Categories

```python
# tests/security/test_auth.py
def test_guest_token_requires_cnf_jkt():
    """AUTH-01: Verify guest tokens without cnf.jkt are rejected"""
    token_without_cnf = create_jwt({"scope": "guest", "iat": now(), "exp": now() + 3600})
    response = client.post("/analyze", headers={"Authorization": f"Bearer {token_without_cnf}"})
    assert response.status_code == 401
    assert response.json()["error"] == "AUTH_TOKEN_INVALID"

# tests/security/test_rls.py
def test_idor_analysis_results():
    """RLS-03: Verify user A cannot access user B's analysis"""
    # User A creates analysis
    analysis_id = create_analysis(user_id="user_a")

    # User B attempts access
    token_b = create_user_token(user_id="user_b")
    response = client.get(f"/analysis/{analysis_id}", headers={"Authorization": f"Bearer {token_b}"})

    assert response.status_code == 404  # RLS hides resource
    assert response.json()["error"] == "RESOURCE_NOT_FOUND"

# tests/security/test_upload.py
def test_upload_rejects_fake_extension():
    """UPLOAD-02: Verify magic bytes validation, not just extension"""
    fake_audio = io.BytesIO(b"<?php system($_GET['cmd']); ?>")
    fake_audio.name = "malicious.mp3"

    response = client.post("/upload", files={"audio": fake_audio})
    assert response.status_code == 400
    assert response.json()["error"] == "FILE_INVALID_FORMAT"

# tests/security/test_exports.py
def test_export_invalid_signature_rejected():
    """EXPORT-01: Verify tampered signatures are rejected"""
    legit_url = generate_export_url(resource_id="res123", user_id="user_a")
    tampered_url = legit_url.replace("res123", "res456")  # Change resource_id

    response = client.get(tampered_url)
    assert response.status_code == 403
    assert response.json()["error"] == "EXPORT_INVALID_SIGNATURE"
```

---

## 5. Compliance Checklist

Antes de cada release, verificar:

- [ ] Todos los tests CRÍTICOS pasan
- [ ] RLS habilitado en todas las tablas críticas (SQL check)
- [ ] Policies RLS tienen ownership checks (SQL audit)
- [ ] Tokens guest incluyen `cnf.jkt` (code review)
- [ ] DPoP validation implementada (code review)
- [ ] Magic bytes validation activa (unit test)
- [ ] Container limits configurados (config review)
- [ ] Network isolation aplicada (config review)
- [ ] Export signed URLs con HMAC (code review)
- [ ] Logs sanitizados en prod (manual test)
- [ ] Errores no exponen stack traces en prod (manual test)
- [ ] Rate limiting activo (manual test)
- [ ] Audio no persistido en DB (DB schema audit)
- [ ] Metadata mínima (code review)

---

## 6. Notas Finales

### 6.1 Fuera de Scope
Esta spec NO cubre:
- Implementación específica de backend (FastAPI routes, handlers)
- Lógica de negocio del análisis musical
- Frontend/UI
- Planes de suscripción (más allá de rate limiting por rol)
- Deployment infrastructure (más allá de container config)

### 6.2 Versionado
Esta spec es **living document**. Cambios a invariants requieren:
1. Discusión en equipo
2. Actualización de tests afectados
3. PR review con aprobación de security lead
4. Bump de versión semántica (MAJOR para breaking changes a invariants)

### 6.3 Referencias
- DPoP RFC: https://datatracker.ietf.org/doc/html/rfc9449
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Supabase RLS: https://supabase.com/docs/guides/auth/row-level-security
