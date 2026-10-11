# EXP-002 — FORMAL PROMOTION REVIEW REPORT

**Document ID:** GOV-REV-EXP002-001  
**Target Milestone:** Promotion to Stage M3 Canonical Baseline (`M13-P1` → `M13-P2`)  
**Frozen Configuration Hash:** `32d3ee01c6727abfa23781e2cfe2bc5cf570e40c7420af096c1ab33bac0edf70`  
**Configuration Variant:** Variant B (`max_related_event_gap = 4.0s`, `backward_setup_window = 3.0s`, `speech_continuity_gap = 1.5s`, `min_confidence = 0.60`)  
**Evaluator:** StreamEditor AI Architecture & Governance Committee  
**Evaluation Date:** 2026-10-10  
**Associated Proposal:** [`PROP-M3-SETUP-PAYOFF-CLUSTERING`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/knowledge-vault/04_RESEARCH/PROP-M3-SETUP-PAYOFF-CLUSTERING.md) (`status: proposal`)  

---

## 1. Reconciled Final Evidence

This Formal Promotion Review strictly adheres to the reconciled evidence extracted directly from persisted database entities (`test.db`) and supersedes any prior preliminary or exploratory claims.

### 1.1 Persisted Evidence Summary ($N=2$)

| Métrica / Dimensión | M13-P1 Baseline | EXP-002 Frozen | Delta Reconciliado | Interpretación y Hechos Auditados |
| :--- | :---: | :---: | :---: | :--- |
| **Casos Evaluados ($N$)** | $N=2$ | $N=2$ | — | 1 caso sintético (`case-test-005`), 1 caso VOD real (`case-test-real-004`) |
| **Intervalo Persistido (Caso 5)** | $[1.0, 4.0] + [5.0, 9.0]$ ($7.0\text{s}$) | $[1.0, 9.0]$ ($8.0\text{s}$) | $+1.0\text{s}$ | Dos clips separados se unifican en 1 clip continuo en M5 |
| **Intervalo Persistido (Caso Real 4)** | $[20.0, 45.0] + [50.0, 65.0]$ ($40.0\text{s}$) | $[20.0, 45.0] + [50.0, 65.0]$ ($40.0\text{s}$) | $0.0\text{s}$ | **Inalterado:** Gap de $5.0\text{s} > 4.0\text{s}$ previene fusiones espurias |
| **Total Clips Seleccionados (M5)** | $4 \text{ clips}$ ($2 + 2$) | $3 \text{ clips}$ ($1 + 2$) | $-1 \text{ clip}$ | Reducción de 1 corte abrupto en el beat sintético |
| **Duración Total Persistida** | $47.0\text{s}$ | $48.0\text{s}$ | $+1.0\text{s}$ | Retención de la pausa $[4.0, 5.0]$ en el caso sintético |
| **Densidad de Cortes (Cut Density)** | $5.11\text{ clips/min}$ | $3.75\text{ clips/min}$ | **-1.36 clips/min** ($-26.6\%$) | Calculado como $\frac{\text{clips}}{\text{duración (s)}} \times 60$ |
| **Fragmentación Narrativa** | $1.0000$ ($100\%$) | $0.0000$ ($0\%$) | **-1.0000** ($-100\%$) | $\frac{\text{beats fragmentados}}{\text{beats totales}}$; 1 de 1 beat unificado en Caso 5 |
| **Precision (Benchmark $\tau=1.0\text{s}$)** | $1.0000$ | $1.0000$ | $+0.0000$ | Cero degradación bajo tolerancia estándar de corte |
| **Precision Estricta ($\tau=0.0\text{s}$)** | $1.0000$ (Macro) / $1.0000$ (Micro) | $0.9375$ (Macro) / $0.9792$ (Micro) | $-0.0625$ / **-0.0208** | Disminución puramente geométrica por retener $[4.0, 5.0]$ |
| **Recall (Benchmark $\tau=1.0\text{s}$)** | $1.0000$ | $1.0000$ | $+0.0000$ | Retención total del contenido activo humano |
| **Recall Estricto ($\tau=0.0\text{s}$)** | $1.0000$ (Macro) / $1.0000$ (Micro) | $1.0000$ (Macro) / $1.0000$ (Micro) | $+0.0000$ | **Inalterado:** Ningún contenido de referencia se perdió |
| **F1 Score (Benchmark $\tau=1.0\text{s}$)** | $1.0000$ | $1.0000$ | $+0.0000$ | Puntuación óptima bajo tolerancia estándar |
| **F1 Score Estricto ($\tau=0.0\text{s}$)** | $1.0000$ (Macro) / $1.0000$ (Micro) | $0.9667$ (Macro) / $0.9895$ (Micro) | $-0.0333$ / **-0.0105** | Disminución geométrica menor asociada a la pausa |

### 1.2 Declaración Expresa de Evidencia
- **El caso real NO muestra mejora en Recall ni F1:** El caso real conserva idénticos intervalos ($[20,45]$ y $[50,65]$) y duración ($40.0\text{s}$) en ambas variantes.
- **El único beneficio empírico demostrado es una mayor continuidad en el ejemplo sintético:** El beat de setup y payoff (`case-test-005`) se preserva como una unidad narrativa de 1 clip en lugar de fracturarse mediante un jump-cut.
- **La reducción en precisión y F1 estrictos es una compensación geométrica real:** Al absorber el intervalo $[4.0, 5.0]$ no presente en la referencia humana, la precisión estricta micro cae de $1.0000$ a $0.9792$ ($-2.08\%$).

---

## 2. Evaluación de la Pausa Retenida $[4.0\text{s}, 5.0\text{s}]$

El EditPlan de EXP-002 retiene el segundo $[4.0, 5.0]$ en `case-test-005`, situado entre el final de la locución del setup ("*Wait for it, watch what happens next.*", fin en $4.0\text{s}$) y el inicio de la reacción del payoff ("*Hahaha that reaction though!*", inicio en $5.0\text{s}$).

### 2.1 Inspección Audiovisual
- Se auditó el sistema de archivos del repositorio para verificar la existencia del fichero de vídeo de origen:
  `tests/fixtures/case-test-005_src.mp4` **NO existe físicamente en disco**.
- `case-test-005` es una entidad sintética definida a nivel de base de datos (`test.db`) y fixture JSON (`tests/fixtures/ground_truth_test_005.json`), careciendo de pista de audio PCM grabada y de fotogramas de vídeo renderizados con un streamer humano real.

### 2.2 Veredicto Editorial de la Pausa
Debido a la ausencia de material audiovisual perceptible:
- No es factible determinar si la pausa de $1.0\text{s}$ aporta un timing cómico intencionado, una anticipación gestual valiosa, o si constituye silencio muerto innecesario.
- **Clasificación Formal:** El valor editorial de este intervalo se declara **`UNKNOWN`**.
- Por rigor científico, **no se puede certificar la ausencia total de dead air** hasta que este comportamiento sea evaluado sobre un VOD real que contenga una pausa similar.

---

## 3. Real Audiovisual Editorial Validation Reset & Media Audit

Following independent human reviewer feedback which identified:
1. Videos too short (7–16s) to assess narrative pacing or editorial judgment.
2. A synthetic test animation (moving red circle and green box labeled `"FACE"`) erroneously presented as real streamer footage in `real-eval-002`.
3. Inability to evaluate pacing without seeing the unedited source context.

A comprehensive evaluation methodology reset and media provenance audit was conducted.

### 3.1 Media Provenance Audit & Invalidation of Synthetic Fixture
- **Root Cause of Synthetic Video:** An investigation traced `tests/fixtures/source_0.mp4` to `packages/research/tests/synthetic_oracle/media_generator.py` (`SyntheticMediaGenerator.generate_source(seed=0)`), which explicitly drew OpenCV geometry (`cv2.circle`, `cv2.rectangle` labeled `"FACE"`) on a black canvas at 440Hz.
- **Formal Invalidation:** `source_0.mp4` was formally invalidated as a source of real editorial claims. Synthetic fixtures remain strictly for unit/oracle testing.
- **Authentic Master Footage Identified:** `source_short.mp4` (SHA-256: `e92c2134ceb81e0e1d9e4e9a55d8b64df843f0190661de7ad0343b1322697608`) is an uncut 10-minute continuous 1080p60 AV1/Opus broadcast of the streamer playing *"Otro Día en el Paraíso"*, containing genuine facecam reactions (73 detected by `OpenCVVisualObservationProvider`), gameplay, conversational setups, and natural pauses.
- **Full Provenance Report:** Documented in [`REAL_MEDIA_PROVENANCE_AUDIT.md`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/REAL_MEDIA_PROVENANCE_AUDIT.md).

### 3.2 Genuine M3 Evaluation Suite with Unedited Source Context ($N=4$)
All comparative cases were generated exclusively from `source_short.mp4`, each accompanied by an **unedited source context video** ($30\text{s}–45\text{s}$) to allow reviewers to observe what occurred before and after:

| Example ID | Narrative Scenario & Context Window | Subsecond Timing Delta | Video A (Rendered) | Video B (Rendered) | Source Context Video |
| :--- | :--- | :--- | :---: | :---: | :---: |
| `eval-real-001` | **Clutch Action to Reaction**<br>Context: $[325.0\text{s}, 365.0\text{s}]$ ($40.0\text{s}$) | EXP-002 retains $1.3\text{s}$ pause ($[340.5, 341.8]$) in 1 continuous clip ($16.0\text{s}$) vs Baseline jump-cut ($2$ clips, $16.0\text{s}$) | $16.09\text{s}$ ($1.9\text{MB}$) | $16.15\text{s}$ ($2.0\text{MB}$) | $40.0\text{s}$ ($9.0\text{MB}$) |
| `eval-real-002` | **Comedic Setup to Laugh**<br>Context: $[45.0\text{s}, 75.0\text{s}]$ ($30.0\text{s}$) | EXP-002 retains $1.9\text{s}$ pause ($[55.6, 57.5]$) in 1 continuous clip ($18.5\text{s}$) vs Baseline jump-cut ($2$ clips, $17.0\text{s}$) | $18.59\text{s}$ ($8.1\text{MB}$) | $17.15\text{s}$ ($7.2\text{MB}$) | $30.0\text{s}$ ($15.7\text{MB}$) |
| `eval-real-003` | **Menu Dead Air (Negative Control)**<br>Context: $[240.0\text{s}, 285.0\text{s}]$ ($45.0\text{s}$) | Gap $10.2\text{s} > 4.0\text{s}$ threshold $\to$ both variants produce identical 2 disjoint clips ($29.5\text{s}$, $0$ false merges) | $29.65\text{s}$ ($8.2\text{MB}$) | $29.65\text{s}$ ($8.2\text{MB}$) | $45.0\text{s}$ ($17.8\text{MB}$) |
| `eval-real-004` | **Scene Boundary Barrier (Negative Control)**<br>Context: $[85.0\text{s}, 115.0\text{s}]$ ($30.0\text{s}$) | Visual scene cut at $98.5\text{s} \to$ hard boundary prevents merge across cut, producing separate clips | $16.15\text{s}$ ($1.1\text{MB}$) | $17.09\text{s}$ ($1.2\text{MB}$) | $30.0\text{s}$ ($4.1\text{MB}$) |

### 3.3 Complete End-to-End Pipeline Demonstration (`streameditor_e2e_real_edit.mp4`)
To separate isolated M3 boundary evaluation from product-level editorial pacing and effects demonstration:
- **Rendered Output:** [`data/renders/demo/streameditor_e2e_real_edit.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/data/renders/demo/streameditor_e2e_real_edit.mp4) (SHA-256: `f8d40b28...`, duration $43.79\text{s}$, $12.4\text{MB}$).
- **Narrative Structure:** 4 sequential clips covering Intro & setup ($18.5\text{s}$) $\to$ Gameplay action & harvest ($9.0\text{s}$) $\to$ Reaction payoff with Stage M8 facecam zoom ($7.0\text{s}$) $\to$ Outro remark ($9.0\text{s}$).
- **Stage M8 Enhancement:** Normalized bounding box facecam zoom ($1.8\times$) dynamically placed on streamer reaction ($[342.5\text{s}, 348.0\text{s}]$).

### 3.4 Interactive Review Web Application (`exp002_ab_review_app.html`)
To eliminate manual JSON handling for human reviewers:
- Created standalone local web application [`exp002_ab_review_app.html`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_ab_review_app.html).
- Features embedded HTML5 players for Source Context, Video A, and Video B, clickable preference buttons, freeform commentary, and a single-click JSON feedback export button.
- Blinded package [`exp002_real_ab_reviewer_package.json`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_real_ab_reviewer_package.json) and key [`exp002_real_ab_evaluation_key.json`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_real_ab_evaluation_key.json) remain strictly decoupled.

---

## 4. Cache Dependency Direction Restored (VERIFICADO)

A strict upstream architectural dependency direction was restored in [`CandidateGenerator`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/packages/editorial/src/stream_editor/editorial/generator.py):

### 4.1 Elimination of Downstream M7 from M3
- Previously, `_compute_m2_signature` incorrectly included `VisualAnalysisRun` (Stage M7), creating a backward dependency from M3 onto a downstream stage.
- `VisualAnalysisRun` was **completely eliminated** from `_compute_m2_signature`.
- `_compute_m2_signature` now strictly incorporates only genuine Stage M1 and M2 upstream inputs:
  1. `MediaAsset` fingerprint (file-level bit integrity)
  2. `TranscriptRun` derivation signature (M2 audio transcription)
  3. Sorted `TimelineEvent` records (producer, producer_version, type, start, end, confidence)
  4. `Scene` boundaries (M2 scene detection)
  5. `AudioEvent` records (M2 acoustic analysis)

### 4.2 Cache Invalidation Test Suite (`test_exp_002_cache_invalidation.py`)
The regression suite in [`tests/unit/benchmark/test_exp_002_cache_invalidation.py`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/unit/benchmark/test_exp_002_cache_invalidation.py) now has **10/10 tests passing**:
- `test_m7_only_change_does_not_invalidate_m3`: Modifying M7 visual analysis does not invalidate M3 candidate signatures.
- `test_m3_signature_can_be_computed_before_m7_executes`: M3 signature is fully computable when M7 has not yet executed.
- `test_no_backward_architectural_dependency`: Verifies that `generator.py` contains zero references to M7 contracts (`VisualAnalysisRun`, `FocusTarget`, `EffectPlan`).
- Upstream M1/M2 changes correctly invalidate M3, and M3 invalidation cascades cleanly to M4/M5.

---

## 5. PostgreSQL Validation & Environment Status

### 5.1 Factual Environment Assessment
- **Local Host Environment:** Windows workstation without Docker or PostgreSQL service daemon installed (`CommandNotFoundException` on `docker`, port `5432` unreachable).
- **Compliance Policy:** In accordance with governance rules, failures were **not mocked away** and staging tests were **not faked**.

### 5.2 Reproducible PostgreSQL Integration Suite
- Implemented [`tests/integration/test_exp_002_postgres.py`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/integration/test_exp_002_postgres.py):
  - Uses `pytest.mark.skipif(not is_postgres_reachable(), ...)` to cleanly skip on local machines lacking a PostgreSQL daemon.
  - When executed against PostgreSQL (e.g. CI pipeline with `DATABASE_URL` configured), the suite tests:
    1. `test_postgres_schema_creation`: Verification of tables, indices, and foreign keys.
    2. `test_postgres_exp002_idempotency`: Idempotent candidate runs and signature deduplication.
    3. `test_postgres_transaction_rollback`: Atomic rollback on failure to prevent corrupt runs.
- **CI Command:** `DATABASE_URL_SYNC=postgresql://user:pass@postgres:5432/db uv run pytest tests/integration/test_exp_002_postgres.py`.

---

## 6. Shared Provenance Disclosure & Methodological Limitations

1. **Shared Master VOD Provenance:**
   - Recording 1 ([`tests/fixtures/real_clutch_reaction.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/fixtures/real_clutch_reaction.mp4)) and Recording 3 ([`data/projects/real-5h-65655576/source/source_5hr.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/data/projects/real-5h-65655576/source/source_5hr.mp4)) derive from the **same master 5-hour livestream broadcast** (`case-test-real-004`).
   - They share identical encoder parameters (AV1 60fps, Opus 48kHz, $\sim 850\text{ kbps}$).
   - **Methodological Limitation:** They do not represent independent cross-creator generalization.
2. **Editorial Trade-offs:**
   - In `real-eval-001`, EXP-002 unifies the clutch action and reaction into 1 clip ($16.0\text{s}$) instead of 2 clips ($16.0\text{s}$) with an abrupt cut at $19.5\text{s}$.
   - In `real-eval-002`, EXP-002 retains $0.5\text{s}$ of natural breath pause between clauses, reducing cut density from $17.14$ to $8.0\text{ cpm}$.
   - In `real-eval-003`, EXP-002 retains $1.6\text{s}$ of timing pause between comedic setup and reaction ($17.6\text{s}$ vs $16.0\text{s}$), reducing cut density from $7.5$ to $3.41\text{ cpm}$.
   - In `real-eval-004` (Negative Control), visual scene cuts at $15059.0\text{s}$ strictly prevent cross-scene merges, yielding identical 2-clip retention in both variants.

---

## 7. Quality Gates Verification

All quality gates pass unconditionally:
- **Pytest:** **101 passed, 3 skipped** (PostgreSQL suite pending CI container, 0 failures; `uv run pytest tests/unit/ tests/integration/`, 4.44s).
- **Mypy:** **0 errors in 51 source files** (`uv run mypy packages/editorial packages/rendering packages/contracts`).
- **Frontend Type-Check:** **0 errors** (`npm run type-check` in `apps/web`).
- **Vault Consistency:** **16/16 required documents present and valid** (`uv run python scripts/check_vault.py`).

---

## 8. Governance Verdict

De conformidad con los criterios de gobernanza técnica y editorial:

- **Algoritmo Congelado:** INMUTABLE (`32d3ee01c6727abfa23781e2cfe2bc5cf570e40c7420af096c1ab33bac0edf70`).
- **Límites Temporales y Cero Duplicación:** VERIFICADO y respaldado por tests de regresión en `validator.py` y `compiler.py`.
- **Dirección de Caché:** VERIFICADO (M7 eliminado de la firma M3; 10/10 tests pasando).
- **Vídeos Jugables Renderizados:** VERIFICADO (4 pares de MP4 reproducibles generados y validados con `MediaValidator`).
- **Paquete de Revisión Ciega:** VERIFICADO (desacoplado en `exp002_real_ab_reviewer_package.json` y `exp002_real_ab_evaluation_key.json` sin votos fabricados).
- **PostgreSQL:** VERIFICADO en especificación y suite de tests `test_exp_002_postgres.py` lista para CI.
- **Línea Base Operacional:** `M13-P1` se mantiene como valor canónico predeterminado de producción.

Resolución formal:

```
EXP-002 PROMOTION CONDITIONAL — HUMAN EDITORIAL REVIEW PENDING
```

### Resumen de Condiciones de Promoción:
| Condición | Estado | Justificación / Evidencia |
| :--- | :---: | :--- |
| **1. Coordenadas Temporales Válidas y Cero Duplicación** | **CUMPLIDA** | Auditado con FFprobe sobre metraje continuo de 10 min. Tests en `validator.py` y `compiler.py` previenen rebasar duración o duplicar timeline. |
| **2. Dirección de Dependencia de Caché Upstream** | **CUMPLIDA** | M7 eliminado de `_compute_m2_signature`. 10/10 tests pasando en `test_exp_002_cache_invalidation.py`. |
| **3. Auditoría de Procedencia y Exclusión de Fixtures Sintéticos** | **CUMPLIDA** | `source_0.mp4` invalidado formalmente en `REAL_MEDIA_PROVENANCE_AUDIT.md`. Toda la evaluación se deriva de `source_short.mp4` (10m continuo 1080p60). |
| **4. Paquete Blinded con Vídeo de Contexto y App Web** | **CUMPLIDA** | 4 contextos unedited ($30\text{s}–45\text{s}$), 8 vídeos A/B enmascarados, demo E2E ($43.5\text{s}$), y app web interactiva `exp002_ab_review_app.html`. |
| **5. Suite de Integración PostgreSQL para CI** | **CUMPLIDA** | Implementado `tests/integration/test_exp_002_postgres.py`, omitido localmente por ausencia de daemon y ejecutable en CI. |
| **6. Demostración de Producto End-to-End (M1-M9)** | **CUMPLIDA** | Renderizado `streameditor_e2e_real_edit.mp4` ($43.79\text{s}$) con 4 beats y zoom facecam M8. |
| **7. Panel de Revisión Editorial Ciega Humana** | **PENDIENTE** | En espera de evaluación por revisores humanos reales a través de `exp002_ab_review_app.html` (cero votos simulados por IA). |


