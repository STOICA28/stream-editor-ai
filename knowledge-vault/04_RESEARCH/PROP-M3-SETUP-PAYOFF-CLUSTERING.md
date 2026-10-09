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

## 4. Estado de la Pausa Retenida y Validación Audiovisual Real ($N=3$)

En el caso sintético `case-test-005`, la referencia humana activa comprende $[1.0, 4.0]$ y $[5.0, 9.0]$. EXP-002 selecciona $[1.0, 9.0]$, absorbiendo el segundo $[4.0, 5.0]$.
- **Inspección Audiovisual Sintética:** El archivo físico `case-test-005_src.mp4` no existe en disco (es una entidad sintética definida en metadatos y fixtures). Su valor editorial en el fixture sintético se clasifica estrictamente como **`UNKNOWN`**.

### 4.1 Evidencia Audiovisual Real ($N=3$)
Para resolver esta incertidumbre con material audiovisual real, se evaluaron tres grabaciones auténticas y contrastadas:
1. **`real-eval-001` (Gameplay Clutch $\to$ Streamer Reaction):** [`tests/fixtures/real_clutch_reaction.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/fixtures/real_clutch_reaction.mp4) (SHA-256: `49d5a155...`). Gap $1.2\text{s} \le 4.0\text{s}$. EXP-002 ajusta a $[18.0, 28.0] + [27.75, 35.75]$, eliminando $2.0\text{s}$ de silencio inicial inactivo conservando íntegro el clímax.
2. **`real-eval-002` (Setup Conversacional con Pausa $\to$ Punchline):** [`tests/fixtures/source_0.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/fixtures/source_0.mp4) (SHA-256: `c46179a3...`). Gap $1.3\text{s} \le 4.0\text{s}$. EXP-002 produce $[0.6, 8.6]$, eliminando $2.65\text{s}$ de ruido muerto inicial/final y manteniendo la pausa de respiración natural de $1.3\text{s}$ dentro del beat.
3. **`real-eval-003` (Control Negativo Entre Escenas):** [`data/projects/real-5h-65655576/source/source_5hr.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/data/projects/real-5h-65655576/source/source_5hr.mp4) (SHA-256: `99e00ebf...`). Gap $3.5\text{s} \le 4.0\text{s}$ a través de corte de cámara en $15059.0\text{s}$. EXP-002 mantiene los 2 clips separados ($0$ sobre-fusiones gracias al hard stop de escena).

---

## 5. Comparativa Editorial Humana y Paquete Ciego A/B

- **Paquete de Evaluación Ciega Generado:** Los tres pares comparativos fueron serializados con orden aleatorizado en [`exp002_real_ab_evaluation_package.json`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_real_ab_evaluation_package.json).
- **Estado de Evaluación Humana:** **`PENDING HUMAN EDITORIAL EVALUATION`**.
- **Regla Estricta Anti-Simulación:** No se fabrican votos ni se simulan preferencias mediante agentes de IA. La aprobación editorial final requiere un panel de revisores humanos independientes.

---

## 6. Correctitud de Configuración, Caché y PostgreSQL

### 6.1 Endurecimiento de Firmas de Derivación e Invalidación de Caché (VERIFICADO)
- Se implementó `_compute_m2_signature` en `CandidateGenerator` incorporando la huella digital del `MediaAsset`, la firma de `TranscriptRun`, la secuencia ordenada de `TimelineEvents` y la firma de `VisualAnalysisRun`.
- `_run_sig` integra `m2_signature`, `asset_fingerprint` y el hash íntegro de configuración.
- `_candidate_sig` vincula permanentemente `parent_run_sig` y `evidence_ids`.
- **Suite de Regresión:** Superadas **7/7 pruebas** en [`tests/unit/benchmark/test_exp_002_cache_invalidation.py`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/unit/benchmark/test_exp_002_cache_invalidation.py).

### 6.2 Verificación PostgreSQL
- La persistencia e idempotencia fueron validadas en SQLite (`test.db`).
- Se verificó que el host actual no posee servicio Docker ni binarios PostgreSQL instalados (`CommandNotFoundException`).
- **Estado:** Se registra como **bloqueador técnico de entorno** para la activación canónica por defecto en producción.

---

## 7. Estrategia de Rollout Controlado

Para mitigar riesgos editoriales y operativos:
1. **Conservar M13-P1 como Baseline Operacional por Defecto:** La configuración estándar del pipeline mantiene `clustering_variant = "default"` (clustering por proximidad simple).
2. **Activación Opcional Mediante Feature Flag:** EXP-002 estará disponible bajo el flag explícito `ENABLE_M3_RELATIONAL_CLUSTERING = true` o seleccionando `clustering_variant = "variant_b"`.
3. **Evaluación Shadow / Canary:** Monitorizar sobre-fusiones, dead air y densidad de cortes en VODs reales representativos.
4. **Reversibilidad:** Rollback inmediato a M13-P1 sin migración destructiva de esquema ni pérdida de artefactos históricos.
5. **No Crear M13-P2 Canónico:** No se designará `M13-P2` canónico hasta que se satisfagan todas las condiciones de validación.

---

## 8. Decisión y Condiciones de Promoción

**Decisión:** **`EXP-002 PROMOTION CONDITIONAL — EDITORIAL VALIDATION PENDING`**

### Estado de Condiciones Resolutorias:
| Condición | Estado | Evidencia |
| :--- | :---: | :--- |
| **1. Validación Audiovisual Real ($N \ge 3$)** | **CUMPLIDA** | 3 casos reales analizados con huellas SHA-256 e intervalos evaluados. |
| **2. Endurecimiento de Claves de Caché** | **CUMPLIDA** | Upstream M2 integrado en firmas M3; 7/7 tests de regresión superados. |
| **3. Paquete Blinded A/B para Revisores** | **CUMPLIDA** | Serializado en `exp002_real_ab_evaluation_package.json`. |
| **4. Panel de Revisión Editorial Ciega Humana** | **PENDIENTE** | En espera de evaluación por revisores humanos reales (sin votos simulados por IA). |
| **5. Validación Staging PostgreSQL** | **BLOQUEADA** | Bloqueador técnico de entorno local (ausencia de Docker/Postgres en host). |

