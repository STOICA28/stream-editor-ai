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

### 4.1 Auditoría Criptográfica y Visual de Procedencia de Medios (Octubre 2026)
Tras el feedback crítico del revisor humano que detectó una animación sintética (círculo rojo y recuadro verde `"FACE"`) en la evaluación previa:
- **Invalidación Formal de `source_0.mp4`:** Se auditó el código de generación en `packages/research/tests/synthetic_oracle/media_generator.py` (`SyntheticMediaGenerator.generate_source(seed=0)`). Se confirmó que `source_0.mp4` es un fixture de prueba sintético de 360p a 440Hz, NO metraje real de streaming. Se invalidaron formalmente todas las afirmaciones editoriales previas derivadas de este archivo.
- **Identificación de la Fuente Maestra Auténtica:** Se auditó `source_short.mp4` (SHA-256: `e92c2134ceb81e0e1d9e4e9a55d8b64df843f0190661de7ad0343b1322697608`). Es una grabación continua y sin cortes de 10 minutos (600.01s), 1080p60 AV1/Opus, del streamer jugando *"Otro Día en el Paraíso"*, con facecam real (73 reacciones detectadas por `OpenCVVisualObservationProvider`), juego dinámico y diálogo continuo.
- **Informe de Auditoría Completo:** Véase [`REAL_MEDIA_PROVENANCE_AUDIT.md`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/REAL_MEDIA_PROVENANCE_AUDIT.md).

### 4.2 Nueva Suite de Evaluación Editorial Genuina ($N=4$)
Extraída exclusivamente de `source_short.mp4`, cada caso incluye ahora un **vídeo de contexto fuente sin editar** ($30\text{s}–45\text{s}$) junto con las variantes A/B enmascaradas y renderizadas a través de M9:
1. **`eval-real-001` (Gameplay Clutch Action $\to$ Streamer Reaction):** Contexto $[325.0\text{s}, 365.0\text{s}]$ ($40.0\text{s}$). EXP-002 unifica acción y reacción en 1 clip ($16.0\text{s}$) reteniendo la pausa anticipatoria de $1.3\text{s}$ ($[340.5\text{s}, 341.8\text{s}]$), frente a Baseline que introduce un salto de eje ($2$ clips, $16.0\text{s}$).
2. **`eval-real-002` (Conversational Comedic Setup $\to$ Laugh Reaction):** Contexto $[45.0\text{s}, 75.0\text{s}]$ ($30.0\text{s}$). EXP-002 preserva el beat cómico en 1 clip continuo ($18.5\text{s}$) reteniendo la pausa de respiración de $1.9\text{s}$ ($[55.6\text{s}, 57.5\text{s}]$), frente a Baseline que fragmenta la conversación ($2$ clips, $17.0\text{s}$).
3. **`eval-real-003` (Control Negativo: Menú Dead Air > 4.0s):** Contexto $[240.0\text{s}, 285.0\text{s}]$ ($45.0\text{s}$). Pausa de navegación silenciosa de $10.2\text{s} > 4.0\text{s}$. Ambas variantes generan idénticamente 2 clips disjuntos ($29.5\text{s}$), demostrando $0$ sobre-fusiones.
4. **`eval-real-004` (Control Negativo: Corte Duro de Escena):** Contexto $[85.0\text{s}, 115.0\text{s}]$ ($30.0\text{s}$). Transición visual en $98.5\text{s}$. Ambas variantes respetan la barrera dura de escena, produciendo clips separados ($16.0\text{s}$ y $17.0\text{s}$), demostrando integridad absoluta de la barrera.

### 4.3 Demostración End-to-End Multiclip del Pipeline Completo
Para satisfacer la necesidad de evaluar el flujo editorial de producto más allá de cortes aislados:
- **Archivo:** [`data/renders/demo/streameditor_e2e_real_edit.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/data/renders/demo/streameditor_e2e_real_edit.mp4) (SHA-256: `f8d40b28...`, $43.79\text{s}$, $12.4\text{MB}$).
- **Composición Narrativa:** 4 beats estructurados (Intro conversacional $\to$ Acción de cosecha $\to$ Reacción con zoom de facecam Etapa M8 $\to$ Outro y progresión).
- **Efectos M8:** Zoom a facecam ($1.8\times$) en la ROI detectada del streamer ($x=0.015, y=0.045, w=0.170, h=0.300$) sincronizado con el pico de reacción.

---

## 5. Comparativa Editorial Humana y Aplicación Web Interactiva

- **Aplicación Web Local Autónoma:** [`exp002_ab_review_app.html`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_ab_review_app.html) — Aplicación interactiva con reproductores HTML5 embebidos para vídeo de contexto, Vídeo A y Vídeo B, registro de votos por clic y exportación de feedback JSON en un solo clic (sin edición manual de JSON).
- **Paquete Ciego para Revisores:** [`exp002_real_ab_reviewer_package.json`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_real_ab_reviewer_package.json) (incluye explicaciones de delta subsegundo y preguntas narrativas específicas).
- **Clave Restringida de Evaluación:** [`exp002_real_ab_evaluation_key.json`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_real_ab_evaluation_key.json) (asignación de verdad, semilla 20261011, firmas y huellas SHA-256).
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
| **1. Coordenadas Temporales Válidas y Cero Duplicación** | **CUMPLIDA** | Auditado con FFprobe sobre metraje continuo de 10 min. Tests en `validator.py` y `compiler.py` impiden rebasar duración o duplicar timeline. |
| **2. Dirección de Dependencia de Caché Upstream** | **CUMPLIDA** | M7 eliminado de `_compute_m2_signature`; 10/10 tests pasando en `test_exp_002_cache_invalidation.py`. |
| **3. Auditoría de Procedencia y Exclusión de Fixtures Sintéticos** | **CUMPLIDA** | `source_0.mp4` invalidado formalmente en `REAL_MEDIA_PROVENANCE_AUDIT.md`. Toda la evaluación se deriva de `source_short.mp4` (10m continuo 1080p60). |
| **4. Paquete Blinded con Vídeo de Contexto y App Web** | **CUMPLIDA** | 4 contextos unedited ($30\text{s}–45\text{s}$), 8 vídeos A/B enmascarados, demo E2E ($43.5\text{s}$), y app web interactiva `exp002_ab_review_app.html`. |
| **5. Suite de Integración PostgreSQL para CI** | **CUMPLIDA** | Implementado `tests/integration/test_exp_002_postgres.py`, listo para ejecución en pipeline CI. |
| **6. Demostración de Producto End-to-End (M1-M9)** | **CUMPLIDA** | Renderizado `streameditor_e2e_real_edit.mp4` ($43.79\text{s}$) con 4 beats y zoom facecam M8. |
| **7. Panel de Revisión Editorial Ciega Humana** | **PENDIENTE** | En espera de evaluación por revisores humanos reales a través de `exp002_ab_review_app.html` (cero votos simulados por IA). |


