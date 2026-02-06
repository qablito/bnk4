# BeetsNKeys (BnK) — Documento Fundacional (bnk4)

## 1. Qué es BeetsNKeys

BeetsNKeys (BnK) es una web app de **análisis musical técnico** orientada a:
- DJs
- productores
- ingenieros de mezcla y master
- creadores que necesitan **información musical precisa, honesta y utilizable**

BnK NO es:
- un generador de contenido
- un “oráculo musical”
- una app que inventa datos para “parecer inteligente”

BnK existe para **reducir errores humanos** en análisis musical y **mejorar decisiones técnicas reales**.

---

## 2. Principio rector (el más importante)

> **BnK nunca debe engañar al usuario.**

Si un dato no es 100% fiable:
- se indica explícitamente,
- se muestra ambigüedad,
- se aportan candidatos,
- se comunica el límite del análisis.

La confianza del usuario es más importante que:
- métricas bonitas,
- respuestas rápidas,
- features vistosas.

---

## 3. Qué problema resuelve

Los análisis musicales actuales suelen:
- simplificar en exceso,
- ocultar ambigüedad,
- presentar resultados “definitivos” cuando no lo son,
- no explicar límites técnicos.

BnK corrige esto ofreciendo:
- análisis técnicos con **contrato de precisión**,
- resultados contextualizados,
- información útil para decisiones reales (mezcla, DJing, producción).

---

## 4. Contrato de Precisión (Precision Contract)

Cada métrica devuelta por el motor de análisis debe cumplir:

```json
{
  "value": "...",            // opcional si hay ambigüedad
  "confidence": 0.0-1.0,     // obligatorio
  "candidates": [...],       // obligatorio si confidence < umbral
  "method": "string",        // algoritmo / heurística
  "limits": "string"         // cuándo NO es fiable
}
```

Referencia (spec): `ANALYSIS_ENGINE_V1.md`.
