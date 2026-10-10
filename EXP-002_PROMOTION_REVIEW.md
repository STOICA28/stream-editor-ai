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

### 3. Real Audiovisual Editorial Validation & M9 Rendering

Pursuant to final promotion blocker resolution requirements, genuine audiovisual evidence was extracted, rendered, and validated across genuine media assets to evaluate setups, triggers, reactions, conversational pauses, and scene transitions with strictly valid temporal coordinates.

### 3.1 Media Metadata & Coordinate Audit (FFprobe)

Every media file was audited using FFprobe to establish exact format durations, stream timestamps, and boundary constraints:

| Example ID | Source Media File | SHA-256 Fingerprint (First 16 chars) | Stream Codecs | Stream Duration | Time Base | Sampling / FPS |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `real-eval-001` | [`tests/fixtures/real_clutch_reaction.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/fixtures/real_clutch_reaction.mp4) | `49d5a1558555adc2...` | AV1 / Opus | $35.007\text{s}$ (v) / $35.001\text{s}$ (a) | $1/15360$ (v) / $1/48000$ (a) | $60\text{ fps}$ / $48\text{kHz}$ |
| `real-eval-002` | [`tests/fixtures/source_0.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/fixtures/source_0.mp4) | `c46179a3e96d1e13...` | MPEG-4 / AAC | $10.000\text{s}$ (v) | $1/10240$ | $10\text{ fps}$ |
| `real-eval-003` | [`data/projects/real-5h-65655576/source/source_5hr.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/data/projects/real-5h-65655576/source/source_5hr.mp4) | `99e00ebfd8101676...` | AV1 / Opus | $18000.406\text{s}$ (v) / $18000.427\text{s}$ (a) | $1/15360$ (v) / $1/48000$ (a) | $60\text{ fps}$ / $48\text{kHz}$ |
| `real-eval-004` | [`data/projects/real-5h-65655576/source/source_5hr.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/data/projects/real-5h-65655576/source/source_5hr.mp4) | `99e00ebfd8101676...` | AV1 / Opus | $18000.406\text{s}$ (v) / $18000.427\text{s}$ (a) | $1/15360$ (v) / $1/48000$ (a) | $60\text{ fps}$ / $48\text{kHz}$ |

### 3.2 Root-Cause Audit of Previous Invalid Temporal Intervals & Overlaps

An exhaustive root-cause investigation resolved the previous anomalies:
1. **Clip Exceeding Source Duration (`real-eval-001` ending at $35.75\text{s}$ vs source $35.007\text{s}$):**
   - *Actual Cause:* In the prior exploratory script, event `ev-3` ($[29.5, 34.0]$, duration $4.5\text{s}$) was shorter than `min_duration = 8.0s`. `CandidateWindowBuilder` padded it forward unconditionally (`core_start + 8.0 = 35.75s`) without checking source duration, and emitted candidate intervals without validation.
   - *Audit Verdict:* The prior evaluation was **genuinely invalid**. It was rejected and regenerated using valid source coordinates ($[12.0, 19.0]$ and $[20.2, 28.0]$) strictly $\le 35.007\text{s}$.
2. **Clip Exceeding Source Duration (`real-eval-002` ending at $10.65\text{s}$ vs source $10.000\text{s}$):**
   - *Actual Cause:* `min_duration = 8.0s` was applied to a 10-second file. Extracting two separate 8-second clips from a 10-second file is mathematically impossible without exceeding file duration ($8 + 8 = 16 > 10$) and overlapping by 6 seconds.
   - *Audit Verdict:* The prior evaluation was **genuinely invalid**. The corrected evaluation applies `min_duration = 3.5s`, keeping all clips strictly $\le 10.0\text{s}$.
3. **Overlapping Clips & Timeline Duplication (`0.25\text{s}` in `real-eval-001` and `1.5\text{s}` in `real-eval-003`):**
   - *Actual Cause:* In M3, candidate windows that overlap by less than `overlap_threshold = 0.5` remain separate candidate options. The prior script dumped raw unmerged candidate segments directly into sequential clips. In output playback, overlapping sequential source clips replay the overlapping interval twice (**timeline duplication**).
   - In `real-eval-003`, unconstrained padding had crossed a visual scene cut at $15059.0\text{s}$.
   - *Audit Verdict:* The overlaps were **timeline duplication defects**, not intentional transitions. The regression suite now guarantees zero timeline duplication:
     - `EditPlanValidator.validate` strictly rejects sequential source overlaps (`curr.source_start < prev.source_end - 0.001`) and clips exceeding source duration.
     - `TimelineCompiler.compile` enforces strict source duration bounds.
     - Regression tests added to [`tests/unit/planning/test_validator.py`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/unit/planning/test_validator.py) and [`tests/unit/rendering/test_compiler.py`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/unit/rendering/test_compiler.py).

### 3.3 Genuine M9 Rendered Videos & Media Validation

All four comparative cases were compiled into deterministic timelines and rendered through the M9 `RenderingEngine` into playable MP4 videos (`libx264/aac`, 720p 30fps) at [`data/renders/ab_eval/`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/data/renders/ab_eval):

| Example ID | Narrative Scenario | M13-P1 Baseline Interval | EXP-002 Frozen Interval | Video A File | Video B File | MediaValidator Status |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `real-eval-001` | Clutch trigger to streamer reaction | 2 clips: $[11.5, 19.5] + [20.1, 28.1]$ ($16.0\text{s}$) | 1 clip: $[12.0, 28.0]$ ($16.0\text{s}$) | `real-eval-001_video_A.mp4` ($16.0\text{s}$) | `real-eval-001_video_B.mp4` ($16.0\text{s}$) | **VALID** ($3.2\text{MB}$ each, valid streams, exact duration) |
| `real-eval-002` | Conversational setup to punchline | 2 clips: $[0.75, 4.25] + [5.15, 8.65]$ ($7.0\text{s}$) | 1 clip: $[1.0, 8.5]$ ($7.5\text{s}$) | `real-eval-002_video_A.mp4` ($7.5\text{s}$) | `real-eval-002_video_B.mp4` ($7.0\text{s}$) | **VALID** ($88\text{KB}$ each, valid video stream, exact duration) |
| `real-eval-003` | Comedic setup to punchline in 5h VOD | 2 clips: $[1200.0, 1208.0] + [1209.6, 1217.6]$ ($16.0\text{s}$) | 1 clip: $[1200.0, 1217.6]$ ($17.6\text{s}$) | `real-eval-003_video_A.mp4` ($16.0\text{s}$) | `real-eval-003_video_B.mp4` ($17.6\text{s}$) | **VALID** ($11.7\text{MB} / 12.9\text{MB}$, valid streams, exact duration) |
| `real-eval-004` | Unrelated moments across scene cut (Negative Control) | 2 clips: $[15050.0, 15058.0] + [15060.0, 15068.0]$ ($16.0\text{s}$) | 2 clips: $[15050.0, 15058.0] + [15060.0, 15068.0]$ ($16.0\text{s}$) | `real-eval-004_video_A.mp4` ($16.0\text{s}$) | `real-eval-004_video_B.mp4` ($16.0\text{s}$) | **VALID** ($13.3\text{MB}$ each, exact duration, zero false merges) |

### 3.4 Decoupled Blinded Reviewer Package & Restricted Evaluation Key

The evaluation artifacts are strictly decoupled:
1. **Blinded Reviewer Package:** [`exp002_real_ab_reviewer_package.json`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_real_ab_reviewer_package.json)
   - Contains neutral case titles, relative video paths, durations, and clip counts.
   - Contains an unanswered evaluation questionnaire (`selected: null`) covering:
     - Narrative clarity and context progression
     - Naturalness of pacing and rhythm
     - Pause utility (reaction anticipation vs dead air)
     - Cut abruptness
     - Channel publish preference
   - Contains **zero fabricated votes** or pre-filled ratings.
2. **Restricted Evaluation Key:** [`exp002_real_ab_evaluation_key.json`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_real_ab_evaluation_key.json)
   - Contains true variant mapping (Video A / Video B to M13-P1 / EXP-002).
   - Contains randomization seed (`42`), source SHA-256 fingerprints, and run signatures.
   - Contains explicit limitation disclosure regarding master VOD provenance.

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
| **1. Coordenadas Temporales Válidas y Cero Duplicación** | **CUMPLIDA** | Auditado con FFprobe. Tests de regresión en `validator.py` y `compiler.py` previenen intervalos fuera de límites y timeline duplication. |
| **2. Dirección de Dependencia de Caché Upstream** | **CUMPLIDA** | M7 eliminado de `_compute_m2_signature`. 10/10 tests pasando en `test_exp_002_cache_invalidation.py`. |
| **3. Generación de Vídeos Reproducibles A/B (M9)** | **CUMPLIDA** | 4 pares de vídeos MP4 reproducibles renderizados en `data/renders/ab_eval/` y validados con `MediaValidator`. |
| **4. Paquete Blinded Decoupled para Revisores** | **CUMPLIDA** | `exp002_real_ab_reviewer_package.json` desacoplado de `exp002_real_ab_evaluation_key.json` con cuestionario listo y 0 votos fabricados. |
| **5. Suite de Integración PostgreSQL para CI** | **CUMPLIDA** | Implementado `tests/integration/test_exp_002_postgres.py`, omitido localmente por ausencia de daemon y ejecutable en CI. |
| **6. Divulgación de Provenance de VOD Maestro** | **CUMPLIDA** | Grabaciones 1 y 3 documentadas como derivadas del mismo VOD maestro de 5 horas. |
| **7. Panel de Revisión Editorial Ciega Humana** | **PENDIENTE** | En espera de evaluación por revisores humanos reales. Prohibida la simulación de votos por IA. |

