# Threat Model - BeetsNKeys (bnk4) Audio Analysis Web App

## 1. Threat Model Priorizado

### 1.1 Actores

| Actor | Motivación | Capacidades |
|-------|-----------|-------------|
| **Atacante externo no autenticado** | Abuso de recursos, DoS, acceso a datos | HTTP requests, automated tools, bypass attempts |
| **Atacante con cuenta guest** | Acceso a datos de otros usuarios, persistencia no autorizada | Token theft/replay attempts, IDOR, automation |
| **Atacante con cuenta registrada** | Acceso horizontal/vertical, exfiltración de datos | Session hijacking, RLS bypass attempts, abuse of exports |
| **Atacante interno (insider)** | Exfiltración masiva de datos | DB access, logs access, infrastructure access |
| **Analyzer container escape** | Compromiso del host, acceso lateral | Container vulnerabilities, kernel exploits |

### 1.2 Activos Críticos

| Activo | Confidencialidad | Integridad | Disponibilidad | Valor |
|--------|------------------|------------|----------------|-------|
| Audio files (efímeros) | ALTA | MEDIA | MEDIA | ALTO |
| Audio hashes | MEDIA | ALTA | MEDIA | MEDIO |
| Resultados de análisis | ALTA | ALTA | MEDIA | ALTO |
| User credentials/tokens | CRÍTICA | CRÍTICA | ALTA | CRÍTICO |
| Supabase RLS policies | CRÍTICA | CRÍTICA | CRÍTICA | CRÍTICO |
| Export URLs firmadas | ALTA | CRÍTICA | MEDIA | ALTO |
| API keys/secrets | CRÍTICA | CRÍTICA | ALTA | CRÍTICO |
| Logs de aplicación | MEDIA | MEDIA | BAJA | MEDIO |

### 1.3 Superficies de Ataque

#### 1.3.1 Guest Flow (PoP fuerte)
```
┌─────────────┐
│   Client │ generates per-device keypair
└──────┬──────┘
│ guest access token bound to device pubkey (cnf.jkt)
│ + DPoP JWT per request (proof-of-possession)
▼
┌─────────────────────┐
│   FastAPI + Auth    │ ← validates token + DPoP + anti-replay
└──────┬──────────────┘
│
▼
┌─────────────────────┐
│  Supabase (RLS)     │ ← guest scope restrictions (if any rows exist)
└─────────────────────┘
```

**Vectores de ataque:**
- Token theft + replay (sin key)
- DPoP bypass (missing/invalid proof)
- jti replay (anti-replay weakness)
- TTL manipulation

#### 1.3.2 Audio Upload & Processing
```
┌─────────────┐
│   Upload    │
└──────┬──────┘
       │ Audio file + validation
       ▼
┌─────────────────────┐
│  FastAPI Validator  │ ← Size, format, magic bytes
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Temp Storage (TTL)  │ ← Ephemeral storage (no DB/Redis blob)
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│ Analyzer Container  │ ← Isolated, CPU/RAM/timeout limits
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  Supabase (hash +   │
│  results + metadata)│
└─────────────────────┘
```

**Vectores de ataque:**
- Malicious file upload (zip bombs, polyglots)
- Path traversal en nombres de archivo
- DoS via análisis costoso
- Container escape
- Resource exhaustion (CPU/RAM)
- Timeout bypass

#### 1.3.3 Export Flow (Authenticated Only)
```
┌──────────────────┐
│ Logged User Only │
└────────┬─────────┘
         │
         ▼
┌──────────────────────┐
│  Export Request      │
│  (PDF/JSON/DAW)      │
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  RLS Check           │ ← Ownership verification (RLS enforced)
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Generate Signed URL │ ← Short TTL, HMAC-signed
└────────┬─────────────┘
         │
         ▼
┌──────────────────────┐
│  Storage/Download     ← Signature + TTL validation
└──────────────────────┘
```

**Vectores de ataque:**
- IDOR en export requests
- RLS bypass
- Signed URL manipulation/replay
- TTL extension attacks
- Guest access to exports

### 1.4 Ataques Priorizados

| # | Ataque | Impacto | Probabilidad | Riesgo | Mitigaciones |
|---|--------|---------|--------------|--------|--------------|
| **1** | **IDOR en análisis/exports** | CRÍTICO | ALTA | **CRÍTICO** | RLS forzado, ownership checks, tests automatizados |
| **2** | **RLS bypass** | CRÍTICO | MEDIA | **CRÍTICO** | RLS en todas las tablas, deny-by-default, tests E2E |
| **3** | **Token theft/replay (guest)** | ALTO | ALTA | **ALTO** | PoP real (DPoP JWT), anti-replay (jti), short TTL |
| **4** | **Analyzer DoS** | ALTO | ALTA | **ALTO** | CPU/RAM limits, timeout enforcement, rate limiting |
| **5** | **Malicious file upload** | ALTO | MEDIA | **ALTO** | Magic bytes validation, sandboxing |
| **6** | **Container escape** | CRÍTICO | BAJA | **ALTO** | Minimal privileges, seccomp, read-only filesystem |
| **7** | **Secrets in logs/errors** | ALTO | MEDIA | **ALTO** | Sanitized logging, no stack traces in prod |
| **8** | **Rate limit bypass** | MEDIO | ALTA | **MEDIO** | Multi-layer rate limiting (IP + user + endpoint) |
| **9** | **Path traversal** | ALTO | BAJA | **MEDIO** | UUID-based storage keys, filename discard |
| **10** | **Export URL enumeration** | MEDIO | MEDIA | **MEDIO** | HMAC signature, nonce, short TTL |


---

## 2. Security Invariants (NO NEGOCIABLES)

**Nota:** Los invariants normativos y el modelo de error estan definidos en `SECURITY_SPEC.md`. Esta seccion es un resumen y puede omitir detalles.

### AUTH-01: Guest Token Binding (PoP)
**Regla:** Todo token guest DEBE estar ligado a una clave pública de dispositivo mediante `cnf.jkt` (thumbprint). El servidor DEBE rechazar tokens guest sin `cnf.jkt`.

**Verificación:**
- Payload mínimo: `{"scope":"guest","iat":<unix_ts>,"exp":<unix_ts>,"cnf":{"jkt":"<thumbprint>"}}`

### AUTH-02: Proof-of-Possession (DPoP JWT) + Anti-Replay
**Regla:** Todo request con token guest DEBE incluir header `DPoP` que sea un JWT firmado por la clave privada del dispositivo correspondiente a `cnf.jkt`. El servidor DEBE validar firma, `htu`, `htm`, `iat`, y aplicar anti-replay por `jti`.

**Verificación (mínima):**
- Header `DPoP` presente
- Claims: `htu`, `htm`, `iat`, `jti` (y opcional `ath`)
- `jti` único por ventana (cache TTL corto)

### AUTH-03: Token TTL Maximum
**Regla:** Tokens guest DEBEN expirar en máximo 1 hora. Tokens de autenticados en máximo 24 horas. NO se permite refresh de tokens guest.

**Verificación:**
- `exp - iat <= 3600` (guest)
- `exp - iat <= 86400` (authenticated)

### AUTH-04: Export Endpoint Authentication
**Regla:** Endpoints `/exports/*` DEBEN rechazar cualquier request con scope=guest. Solo usuarios autenticados pueden generar exports.

**Verificación:**
- `if token.scope == "guest" and request.path.startswith("/exports/"): return 403`

### RLS-01: Universal RLS Enforcement
**Regla:** TODAS las tablas que contienen datos de usuario (`audio_hashes`, `analysis_results`, `exports`) DEBEN tener RLS habilitado. NO se permiten excepciones.

**Verificación:**
```sql
SELECT tablename FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('audio_hashes', 'analysis_results', 'exports')
  AND rowsecurity = false;
-- Esperado: 0 filas
```

### RLS-02: Deny-by-Default Policies
**Regla:** Todas las políticas RLS DEBEN seguir deny-by-default. Sin política explícita que permita acceso, el acceso DEBE ser denegado. Prohibido qual IS NULL en políticas permisivas.

**Verificación:**
```sql
-- Verificar que no exista política PERMISSIVE sin condiciones
SELECT schemaname, tablename, policyname FROM pg_policies
WHERE permissive = 'PERMISSIVE' AND qual IS NULL;
-- Esperado: 0 filas
```

### RLS-03: Ownership-Based Policies
**Regla:** Políticas RLS DEBEN verificar ownership mediante `auth.uid() = user_id` (autenticados) o `auth.jwt()->'cnf'->>'jkt' = device_jkt` (guests). NO se permite `true` como condición.

**Verificación:**
```sql
-- Buscar políticas que permitan acceso sin verificación de ownership
SELECT policyname, qual FROM pg_policies
WHERE qual ~ 'true' AND schemaname='public';
-- Esperado: 0 filas (salvo admin estrictamente justificado)
```

### UPLOAD-01: File Size Limit
**Regla:** Audio uploads DEBEN rechazarse si exceden 50MB. Validación DEBE ocurrir antes de leer el cuerpo del request completo.

**Verificación:**
- `Content-Length > 52428800: return 413`
- Stream processing con abort si excede límite

### UPLOAD-02: Magic Bytes Validation
**Regla:** Audio files DEBEN validarse mediante magic bytes (primeros 8-16 bytes) contra whitelist de formatos permitidos (WAV, MP3, FLAC, OGG). Extensión de archivo NO es suficiente.

**Verificación:**
```python
ALLOWED_MAGIC = {
    b'RIFF....WAVE': 'wav',
    b'ID3': 'mp3',
    b'\xff\xfb': 'mp3',
    b'fLaC': 'flac',
    b'OggS': 'ogg'
}
```

### UPLOAD-03: Filename Sanitization
**Regla:** Nombres de archivo DEBEN ser descartados y reemplazados por UUIDs. Path traversal sequences (`../`, `..\`) DEBEN ser bloqueados explícitamente.

**Verificación:**
- Storage key: `{uuid4()}.{validated_extension}`
- Reject if filename contains: `..`, `/`, `\`, `%00`

### ANALYZE-01: Container Resource Limits
**Regla:** Analyzer container DEBE tener límites hard: CPU=1 core, RAM=512MB, timeout=60s. Exceder límites DEBE terminar el proceso sin analizar.

**Verificación:**
```yaml
# Docker/K8s config
resources:
  limits:
    cpu: "1000m"
    memory: "512Mi"
  requests:
    cpu: "500m"
    memory: "256Mi"
```

### ANALYZE-02: Network Isolation
**Regla:** Analyzer container DEBE ejecutarse en red aislada sin acceso a internet ni servicios internos (excepto resultado output). NO DNS, NO egress.

**Verificación:**
```yaml
# Docker
network_mode: none
# K8s NetworkPolicy
policyTypes:
  - Egress
egress: []
```

### ANALYZE-03: Filesystem Restrictions
**Regla:** Analyzer container DEBE montar filesystem como read-only excepto `/tmp` (tmpfs). NO se permite escritura en paths arbitrarios.

**Verificación:**
```yaml
# Docker
read_only: true
tmpfs:
  - /tmp:size=100m,noexec
```

### ANALYZE-04: Input Sanitization
**Regla:** Antes de pasar audio al analyzer, DEBE validarse: no ZIP bombs (compressed/uncompressed ratio <100), no polyglots (múltiples magic bytes), no archivos concatenados.

**Verificación:**
- Decompression ratio check
- Single format detection
- No trailing data after valid audio end

### EXPORT-01: Signed URL Generation
**Regla:** Export URLs DEBEN incluir: resource_id, user_id, expiry (<=15min), random nonce (16 bytes), y HMAC-SHA256 de todos los campos anteriores.

**Verificación:**
```python
url_format = "/exports/{resource_id}?user_id={uid}&expires={ts}&nonce={hex}&sig={hmac}"
hmac = HMAC-SHA256(secret, f"{resource_id}|{uid}|{ts}|{nonce}")
```

### EXPORT-02: RLS Pre-Check
**Regla:** Antes de generar signed URL, DEBE ejecutarse query RLS-enforced para verificar ownership. Generar URL sin verificación está prohibido.

**Verificación:**
```python
# En FastAPI
result = supabase.from_('analysis_results')\
  .select('id')\
  .eq('id', resource_id)\
  .eq('user_id', auth.uid())\
  .single()\
  .execute()
if not result.data:
    raise HTTPException(403)
```

### EXPORT-03: TTL Enforcement
**Regla:** Export signed URLs DEBEN expirar en  <=15 minutos. Backend DEBE rechazar URLs con `expires` > `now()` o `expires > issued + 900s`.

**Verificación:**
- `if now() > url.expires: return 410`
- `if url.expires - url.issued > 900: return 400`

### LOGGING-01: Secrets Sanitization
**Regla:** Logs NUNCA contienen tokens completos, passwords, API keys, device fingerprints cnf.jkt completos (solo hash/truncado), ni audio content.

**Verificación:**
```python
# Sanitizer regex
SECRETS_PATTERNS = [
    r'(token["\s:=]+)[^\s"]+',  # Reemplazar por \1****
    r'(password["\s:=]+)[^\s"]+',
    r'(api_key["\s:=]+)[^\s"]+',
]
```

### LOGGING-02: Error Message Sanitization
**Regla:** Error responses en producción NO deben incluir stack traces, paths absolutos, versiones de librerías, o mensajes SQL raw. Solo error code + mensaje genérico.

**Verificación:**
```python
# Producción
return JSONResponse(
    status_code=500,
    content={"error": "INTERNAL_ERROR", "code": "E500"}
)
# NO incluir: traceback, db error, file paths
```

### RATE-01: Multi-Layer Rate Limiting
**Regla:** Rate limiting DEBE aplicarse en 3 capas: IP (100 req/min), user_id (50 req/min), endpoint crítico (/analyze: 5 req/min).

**Verificación:**
- Middleware Redis-based counter
- 429 Too Many Requests si excede
- Headers: `X-RateLimit-Remaining`, `X-RateLimit-Reset`

### RATE-02: Analyze Endpoint Restriction
**Regla:** `/analyze` endpoint limitado por rol (Nota: reglas exactas definidas por roles guest/free/pro en BeetsNKeys).

**Verificación:**
```python
-
```

### DATA-01: Audio Ephemeral Storage
**Regla:** Audio solo en storage efímero (tmpfs/ephemeral volume) con TTL y limpieza. Prohibido guardar audio binario en DB o Redis.

**Verificación:**
- Ni existe columna/registro/clave que contenga el binario.
- Cleanup job/borrado garantizado

### DATA-02: Hash-Only Persistence
**Regla:** En DB solo se persiste SHA-256 del audio (para deduplicación) + resultados análisis + metadata mínimo (duración, formato). NO paths, NO contenido.

**Verificación:**
```sql
-- Tabla audio_hashes
CREATE TABLE audio_hashes (
  hash TEXT PRIMARY KEY,  -- SHA-256
  duration_seconds INT,
  format TEXT,
  created_at TIMESTAMP
);
-- NO DEBE existir columna 'content', 'file_path', 'url'
```

### DATA-03: Metadata Minimization
**Regla:** Metadata persistida DEBE limitarse a: duración, formato, sample rate, bitrate, channels. NO metadata EXIF, NO geolocation, NO original filename, NO user agent.

**Verificación:**
```python
ALLOWED_METADATA = ['duration', 'format', 'sample_rate', 'bitrate', 'channels']
stored_metadata = {k: v for k, v in metadata.items() if k in ALLOWED_METADATA}
```

---
---

## Resumen Ejecutivo

### Activos Más Críticos
1. Tokens de autenticación (guest + authenticated)
2. RLS policies en Supabase
3. Audio content (temporal pero sensible)
4. Export signed URLs

### Top 3 Riesgos
1. **IDOR + RLS bypass** → Acceso no autorizado a análisis de otros usuarios
2. **Analyzer DoS** → Resource exhaustion vía audio malicioso
3. **Token replay/forgery** → Bypass de device binding

### Mitigaciones Clave
- RLS forzado en todas las tablas con deny-by-default
- DPoP-style device binding para guests
- Container sandboxing con límites hard
- Multi-layer rate limiting
- Audio ephemeral con TTL estricto

---

## References

- `SECURITY_SPEC.md` (normative invariants and error model)
- `CONTRACTS/` (schemas and protocol contracts)
- `CHECKS/` (lint checks for docs/contracts)
- `PULL_REQUEST_TEMPLATE.md` (PR security checklist)
