---
id: PROP-M3-SETUP-PAYOFF-001
title: Promotion Proposal - M3 Setup/Payoff Clustering & Context Windowing
status: proposal
author: StreamEditor AI Architecture & Governance
created: 2026-10-10
references:
  - EXP-002
  - M13-P1
---

# PROP-M3-SETUP-PAYOFF-CLUSTERING: Promotion Proposal for Relational Event Clustering

## 1. Executive Summary

This proposal evaluates promoting the Stage M3 relational clustering and context expansion mechanism (**EXP-002**, frozen configuration hash: `32d3ee01c6727abfa23781e2cfe2bc5cf570e40c7420af096c1ab33bac0edf70`) from experimental holdout evaluation into the canonical production pipeline of StreamEditor AI (`M13-P1`).

EXP-002 replaces blind $1.0\text{s}$ temporal proximity clustering in Stage M3 with relational clustering governed by semantic event relations, an upper temporal gap ($\Delta t \le 4.0\text{s}$), scene-boundary hard stops, and speech-snapped backward context expansion ($3.0\text{s}$).

**Current Status:** `proposal` (Pending formal conditional validation).

---

## 2. Reconciled Empirical Evidence

The empirical findings are derived strictly from persisted SQLite records in `test.db` across the discriminative holdout ($N=2$: 1 synthetic, 1 real in-distribution VOD slice):

| Dimensión / Métrica | M13-P1 Baseline | EXP-002 Frozen (Variant B) | Delta Reconciliado | Notas de Auditoría |
| :--- | :---: | :---: | :---: | :--- |
| **Casos Evaluados ($N$)** | $N=2$ | $N=2$ | — | 1 sintético (`case-test-005`), 1 real (`case-test-real-004`) |
| **Clips Seleccionados (M5)** | $4$ clips | $3$ clips | $-1$ clip | Caso 5 unificado de 2 clips a 1 clip continuo |
| **Duración Total Persistida** | $47.0\text{s}$ | $48.0\text{s}$ | $+1.0\text{s}$ | Retiene la pausa de $1.0\text{s}$ en Caso 5 |
| **Caso Real 4 (EditPlan)** | $[20,45] + [50,65]$ ($40.0\text{s}$) | $[20,45] + [50,65]$ ($40.0\text{s}$) | $0.0\text{s}$ | Gap $5.0\text{s} > 4.0\text{s} \to 0$ fusiones (rechazo correcto) |
| **Precision (Benchmark $\tau=1.0\text{s}$)** | $1.0000$ | $1.0000$ | $+0.0000$ | Sin pérdida bajo tolerancia estándar |
| **Precision Estricta ($\tau=0.0\text{s}$)** | $1.0000$ (Macro) / $1.0000$ (Micro) | $0.9375$ (Macro) / $0.9792$ (Micro) | $-0.0625$ / $-0.0208$ | Penalización puramente geométrica por la pausa $[4.0, 5.0]$ |
| **Recall (Benchmark $\tau=1.0\text{s}$)** | $1.0000$ | $1.0000$ | $+0.0000$ | $100\%$ de referencia humana activa retenida |
| **Recall Estricto ($\tau=0.0\text{s}$)** | $1.0000$ (Macro) / $1.0000$ (Micro) | $1.0000$ (Macro) / $1.0000$ (Micro) | $+0.0000$ | Retención íntegra de bloques activos |
| **F1 Score (Benchmark $\tau=1.0\text{s}$)** | $1.0000$ | $1.0000$ | $+0.0000$ | Óptimo editorial con tolerancia estándar |
| **F1 Score Estricto ($\tau=0.0\text{s}$)** | $1.0000$ (Macro) / $1.0000$ (Micro) | $0.9667$ (Macro) / $0.9895$ (Micro) | $-0.0333$ / $-0.0105$ | Compensación geométrica por pausa de timing |
| **Fragmentación Narrativa** | $1.0000$ ($100\%$) | $0.0000$ ($0\%$) | **-1.0000** ($-100\%$) | Beat de Caso 5 unificado en 1 solo clip |
| **Densidad de Cortes** | $5.11\text{ clips/min}$ | $3.75\text{ clips/min}$ | **-1.36 clips/min** ($-26.6\%$) | Menor fragmentación de ritmo |
| **Sobre-Fusiones (Over-Merge)** | NOT APPLICABLE | $0.0000$ ($0\%$) | **N/A** | 0 eventos espurios fusionados |
| **Controles Causales Negativos** | — | $8/8$ pasados | — | Rechazos estrictos de gaps, escenas y hablantes |

---

## 3. Delimitación Científica y Limitaciones de Generalización

1. **Tamaño Muestral Reducido ($N=2$):** La evidencia empírica se basa exclusivamente en 2 casos de prueba.
2. **Ausencia de Diferencia en Caso Real:** En `case-test-real-004`, la brecha temporal entre el setup y el payoff clutch es de $5.0\text{s}$, excediendo el umbral congelado $\Delta t \le 4.0\text{s}$. Por consiguiente, el clasificador ejecutó **0 fusiones**, dejando el EditPlan real inalterado ($40.0\text{s}$).
3. **Generalización No Demostrada:** La mejora demostrada se limita a la continuidad más fluida en un único ejemplo sintético. No existe base estadística para proclamar generalización universal ni superioridad en VODs arbitrarios.
4. **Trade-off Métrico:** Las reducciones en precisión estricta ($-0.0208$) y F1 estricto ($-0.0105$) bajo $\tau=0.0\text{s}$ son compensaciones geométricas reales debidas a la retención de la pausa $[4.0, 5.0]$.

---

## 4. Estado de la Pausa Retenida y Validación Audiovisual Real ($N=4$)

En el caso sintético `case-test-005`, la referencia humana activa comprende $[1.0, 4.0]$ y $[5.0, 9.0]$. EXP-002 selecciona $[1.0, 9.0]$, absorbiendo el segundo $[4.0, 5.0]$.
- **Inspección Audiovisual Sintética:** El archivo físico `case-test-005_src.mp4` no existe en disco (es una entidad sintética definida en metadatos y fixtures). Su valor editorial en el fixture sintético se clasifica estrictamente como **`UNKNOWN`**.

### 4.1 Evidencia Audiovisual Real Renderizada ($N=4$)
Para evaluar casos reales con coordenadas estrictamente validadas y confirmadas por FFprobe, se ejecutó y renderizó a través de M9 (`RenderingEngine`):
1. **`real-eval-001` (Gameplay Clutch $\to$ Streamer Reaction):** [`tests/fixtures/real_clutch_reaction.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/fixtures/real_clutch_reaction.mp4) (SHA-256: `49d5a155...`, $35.007\text{s}$). Gap $1.2\text{s} \le 2.0\text{s}$. EXP-002 unifica $[12.0, 28.0]$ ($16.0\text{s}$), eliminando el corte abrupto en $19.5\text{s}$ que Baseline introduce ($[11.5, 19.5] + [20.1, 28.1]$). Ambos intervalos $\le 35.007\text{s}$, 0 duplicación.
2. **`real-eval-002` (Setup Conversacional con Pausa $\to$ Punchline):** [`tests/fixtures/source_0.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/fixtures/source_0.mp4) (SHA-256: `c46179a3...`, $10.000\text{s}$). Gap $1.3\text{s} \le 1.5\text{s}$. EXP-002 produce $[1.0, 8.5]$ ($7.5\text{s}$), reteniendo la pausa de respiración natural y reduciendo la densidad de cortes de $17.14$ a $8.0\text{ cpm}$ frente a Baseline ($[0.75, 4.25] + [5.15, 8.65]$, $7.0\text{s}$). Ambos intervalos $\le 10.0\text{s}$.
3. **`real-eval-003` (Setup a Payoff en VOD de 5h):** [`data/projects/real-5h-65655576/source/source_5hr.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/data/projects/real-5h-65655576/source/source_5hr.mp4) (SHA-256: `99e00ebf...`, $18000.427\text{s}$). Gap $1.6\text{s} \le 2.0\text{s}$. EXP-002 genera 1 clip continuo $[1200.0, 1217.6]$ ($17.6\text{s}$), preservando el timing cómico frente a Baseline ($[1200.0, 1208.0] + [1209.6, 1217.6]$, $16.0\text{s}$).
4. **`real-eval-004` (Control Negativo Entre Escenas):** [`data/projects/real-5h-65655576/source/source_5hr.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/data/projects/real-5h-65655576/source/source_5hr.mp4) (SHA-256: `99e00ebf...`, $18000.427\text{s}$). Gap $2.0\text{s} \le 4.0\text{s}$ a través de corte de cámara en $15059.0\text{s}$. EXP-002 mantiene los 2 clips separados ($[15050.0, 15058.0] + [15060.0, 15068.0]$, $16.0\text{s}$), confirmando $0$ sobre-fusiones.

### 4.2 Divulgación de Provenance Compartido
- **Limitación Metodológica:** La Grabación 1 (`real_clutch_reaction.mp4`) y la Grabación 3 (`source_5hr.mp4`) proceden del mismo VOD maestro de 5 horas. Comparten codificación AV1/Opus idéntica y no representan generalización independiente entre diferentes creadores.

---

## 5. Comparativa Editorial Humana y Paquetes Desacoplados

- **Paquete Ciego para Revisores:** [`exp002_real_ab_reviewer_package.json`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_real_ab_reviewer_package.json) (rutas relativas a los MP4 renderizados, preguntas estructuradas, cero etiquetas de variantes, cero votos fabricados).
- **Clave Restringida de Evaluación:** [`exp002_real_ab_evaluation_key.json`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_real_ab_evaluation_key.json) (asignación de verdad, semilla 42, firmas y huellas SHA-256).
- **Estado de Evaluación Humana:** **`PENDING HUMAN EDITORIAL REVIEW`**. Prohibida la simulación de votos por IA.

---

## 6. Correctitud de Configuración, Caché y PostgreSQL

### 6.1 Restauración de Dependencias de Caché Upstream (VERIFICADO)
- Se eliminó completamente la dependencia hacia atrás de M7 (`VisualAnalysisRun`) en `_compute_m2_signature` en `CandidateGenerator`.
- La firma M3 incorpora estrictamente entradas M1/M2: `MediaAsset`, `TranscriptRun`, `TimelineEvents`, `Scene` y `AudioEvent`.
- **Suite de Regresión:** Superadas **10/10 pruebas** en [`tests/unit/benchmark/test_exp_002_cache_invalidation.py`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/unit/benchmark/test_exp_002_cache_invalidation.py).

### 6.2 Verificación PostgreSQL
- Persistencia e idempotencia validadas en SQLite (`test.db`).
- Suite de integración completa implementada en [`tests/integration/test_exp_002_postgres.py`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/integration/test_exp_002_postgres.py), omitida limpiamente en el host local por carecer de daemon PostgreSQL/Docker y lista para ejecutarse en CI contra contenedor PostgreSQL.

---

## 7. Estrategia de Rollout Controlado

1. **Conservar M13-P1 como Baseline Operacional por Defecto:** `clustering_variant = "default"`.
2. **Activación Opcional Mediante Feature Flag:** `clustering_variant = "variant_b"` o `ENABLE_M3_RELATIONAL_CLUSTERING = true`.
3. **Evaluación Canary:** Monitorización de sobre-fusiones y densidad de cortes en producción controlada.
4. **Reversibilidad:** Rollback instantáneo sin migración destructiva.
5. **No Promocionar Canónicamente a M13-P2 Automáticamente.**

---

## 8. Decisión y Condiciones de Promoción

**Decisión:** **`EXP-002 PROMOTION CONDITIONAL — HUMAN EDITORIAL REVIEW PENDING`**

### Estado de Condiciones Resolutorias:
| Condición | Estado | Evidencia |
| :--- | :---: | :--- |
| **1. Coordenadas Temporales Válidas y Cero Duplicación** | **CUMPLIDA** | Auditado con FFprobe. Tests de regresión en `validator.py` y `compiler.py` impiden rebasar duración o duplicar timeline. |
| **2. Dirección de Dependencia de Caché Upstream** | **CUMPLIDA** | M7 eliminado de `_compute_m2_signature`; 10/10 tests pasando en `test_exp_002_cache_invalidation.py`. |
| **3. Generación de Vídeos Reproducibles A/B (M9)** | **CUMPLIDA** | 4 pares de vídeos MP4 reproducibles renderizados en `data/renders/ab_eval/` y validados con `MediaValidator`. |
| **4. Paquete Blinded Desacoplado para Revisores** | **CUMPLIDA** | `exp002_real_ab_reviewer_package.json` desacoplado de `exp002_real_ab_evaluation_key.json` con cuestionario listo y 0 votos simulados. |
| **5. Suite de Integración PostgreSQL para CI** | **CUMPLIDA** | Implementado `tests/integration/test_exp_002_postgres.py`, listo para ejecución en pipeline CI. |
| **6. Divulgación de Provenance de VOD Maestro** | **CUMPLIDA** | Grabaciones 1 y 3 documentadas como derivadas del mismo VOD maestro de 5 horas. |
| **7. Panel de Revisión Editorial Ciega Humana** | **PENDIENTE** | En espera de evaluación por revisores humanos reales (sin votos simulados por IA). |

