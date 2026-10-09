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

## 3. Real Audiovisual Editorial Validation & Human Editorial Comparison

Pursuant to conditional promotion requirements, genuine audiovisual evidence was extracted and evaluated across three distinct real video assets to observe naturally occurring setups, triggers, reactions, and negative controls.

### 3.1 Genuine Audiovisual Dataset & Provenance ($N=3$)

1. **Recording 1 (`real-eval-001`): Gameplay Clutch Trigger to Streamer Reaction**
   - **Source:** [`tests/fixtures/real_clutch_reaction.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/fixtures/real_clutch_reaction.mp4)
   - **Fingerprint (SHA-256):** `49d5a1558555adc288a69a831edbd2ad9f916e429aa13488cf02fee2eeac7c28`
   - **Duration:** $35.007\text{s}$ (1080p AV1/Opus)
   - **Relation Tested:** `EVENT_TO_REACTION` ($\Delta t = 1.2\text{s} \le 4.0\text{s}$)
   - **M13-P1 Baseline Output:** 1 clip $[16.0, 35.75]$ ($19.75\text{s}$), runtime $0.18\text{ms}$
   - **EXP-002 Frozen Output:** 2 clips $[18.0, 28.0] + [27.75, 35.75]$ ($18.0\text{s}$), runtime $0.25\text{ms}$
   - **Editorial Detail:** EXP-002 snips out $2.0\text{s}$ of dead pre-roll silence before the clutch trigger without losing any streamer speech or reaction punch.

2. **Recording 2 (`real-eval-002`): Conversational Setup with Breath Pause to Punchline**
   - **Source:** [`tests/fixtures/source_0.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/fixtures/source_0.mp4)
   - **Fingerprint (SHA-256):** `c46179a3e96d1e13218ef22486e8626e35735b41f9df3771c0735a7fff989523`
   - **Duration:** $10.000\text{s}$ (360p MPEG-4)
   - **Relation Tested:** `SETUP_TO_EVENT` / Speech Continuity ($\Delta t = 1.3\text{s} \le 4.0\text{s}$)
   - **M13-P1 Baseline Output:** 1 clip $[0.0, 10.65]$ ($10.65\text{s}$), runtime $0.07\text{ms}$
   - **EXP-002 Frozen Output:** 1 clip $[0.6, 8.6]$ ($8.0\text{s}$), runtime $0.08\text{ms}$
   - **Editorial Detail:** Baseline extends into $2.05\text{s}$ of dead trailing noise. EXP-002 snaps cleanly to utterance boundaries ($[0.6, 8.6]$) and preserves the $1.3\text{s}$ breath pause inside the beat without fragmentation.

3. **Recording 3 (`real-eval-003`): Unrelated Streamer Moments Across Scene Cut (Negative Control)**
   - **Source:** [`data/projects/real-5h-65655576/source/source_5hr.mp4`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/data/projects/real-5h-65655576/source/source_5hr.mp4)
   - **Fingerprint (SHA-256):** `99e00ebfd81016769add13f4f08575e89b3bd35ed1f619c6eb52cd00f3f470ad`
   - **Duration:** $18000.427\text{s}$ ($5.0\text{h}$ VOD)
   - **Relation Tested:** `SCENE_BOUNDARY_HARD_STOP` ($\Delta t = 3.5\text{s} \le 4.0\text{s}$ across visual cut at $15059.0\text{s}$)
   - **M13-P1 Baseline Output:** 2 separate clips $[15052.5, 15060.5]$ and $[15059.0, 15067.0]$ ($16.0\text{s}$)
   - **EXP-002 Frozen Output:** 2 separate clips $[15052.5, 15060.5]$ and $[15059.0, 15067.0]$ ($16.0\text{s}$)
   - **Editorial Detail:** Identical retention. The scene-boundary hard stop successfully prevented an over-merge between unrelated beats across the camera cut.

### 3.2 Evaluation Package & Blinded Presentation

The comparative assessment package was generated and persisted to [`exp002_real_ab_evaluation_package.json`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/exp002_real_ab_evaluation_package.json):

| Example ID | Ground Truth Presentation A | Ground Truth Presentation B | Randomized Truth A | Randomized Truth B | Runtime Delta |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `real-eval-001` | $[18.0, 28.0] + [27.75, 35.75]$ | $[16.0, 35.75]$ | **EXP-002** | M13-P1 Baseline | $+0.07\text{ms}$ ($0.18 \to 0.25\text{ms}$) |
| `real-eval-002` | $[0.6, 8.6]$ | $[0.0, 10.65]$ | **EXP-002** | M13-P1 Baseline | $+0.01\text{ms}$ ($0.07 \to 0.08\text{ms}$) |
| `real-eval-003` | $[15052.5, 15060.5] + [15059.0, 15067.0]$ | $[15052.5, 15060.5] + [15059.0, 15067.0]$ | M13-P1 Baseline | **EXP-002** | $+0.02\text{ms}$ ($0.06 \to 0.08\text{ms}$) |

### 3.3 Status of Human Review Panel
- **Revisores Humanos Participantes:** 0 (Panel editorial humano independiente no convocado a la fecha de ejecución).
- **Regla Estricta Anti-Fabricación:** De acuerdo con las instrucciones de gobernanza, la IA evaluadora no emite votos simulados ni asume preferencia editorial en sustitución de editores humanos.
- **Veredicto Formal:** **`UNRESOLVED / PENDING HUMAN EDITORIAL EVALUATION`**.
- El paquete ciego se encuentra completamente serializado y listo para ser distribuido a editores humanos externos.

---

## 4. Correctitud de Configuración de Producción y Caché (VERIFICADO)

Se implementó y verificó rigurosamente el mecanismo de derivación de firmas e invalidación de caché multinivel en [`CandidateGenerator`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/packages/editorial/src/stream_editor/editorial/generator.py):

### 4.1 Firma de Ejecución Upstream e Invalidation (`_compute_m2_signature` & `_run_sig`)
```python
def _compute_m2_signature(source_asset_id: str, db: Session) -> str:
    # Computes deterministic SHA-256 digest of:
    # 1. MediaAsset fingerprint
    # 2. TranscriptRun.derivation_signature
    # 3. Sorted TimelineEvent records (IDs, types, start/end, confidence)
    # 4. VisualAnalysisRun.derivation_signature
```
- `_run_sig` incorpora ahora explícitamente:
  - `m2_signature` (hash de los artefactos M2 upstream).
  - `asset_fingerprint` (huella digital inmutable del medio de origen).
  - Configuración completa (`CandidateWindowConfig`, incluyendo `clustering_config`).
  - Flags de ejecución y perfiles de ranking.

### 4.2 Firma de Candidato Individual Vinculada (`_candidate_sig`)
- `_candidate_sig` vincula de forma inmutable:
  - `parent_run_sig` (hereda la firma de la ejecución M3 completa).
  - `evidence_ids` (conjunto ordenado de eventos M2 que justifican el candidato).
  - Límites temporales redondeados a milisegundos.
- **Garantía Operativa:** Ningún candidato puede colisionar o ser reutilizado si varían los umbrales de clustering o los eventos M2 upstream.

### 4.3 Suite de Regresión de Caché (`test_exp_002_cache_invalidation.py`)
Se construyó y ejecutó una suite de pruebas de regresión ejecutable ([`tests/unit/benchmark/test_exp_002_cache_invalidation.py`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/tests/unit/benchmark/test_exp_002_cache_invalidation.py)) con **7/7 pruebas superadas**:
1. `test_m2_input_change_invalidates_candidate_run`: Modificaciones en transcripciones o eventos M2 invalidan la firma M3.
2. `test_config_threshold_change_invalidates_candidate_run`: Ajustes en `max_related_event_gap` u otros umbrales invalidan la firma M3.
3. `test_identical_inputs_produce_identical_run_sig`: Entradas idénticas reutilizan determinísticamente la firma previa (idempotencia).
4. `test_feature_flag_switching_invalidates_run_sig`: Alternar `clustering_variant` entre `default` y `variant_b` genera firmas dispares.
5. `test_rollback_to_baseline_recovers_original_signature`: Revertir la configuración recupera bit a bit la firma original de M13-P1.
6. `test_m3_invalidation_cascades_downstream_preserves_upstream`: La invalidación de M3 propaga a M4 (Story Graph) sin invalidar las claves de M1/M2.
7. `test_candidate_segment_signature_links_parent_run_and_evidence`: La firma individual de segmento cambia si cambian los eventos de evidencia o la ejecución padre.

---

## 5. Verificación Operacional y PostgreSQL

### 5.1 Estado Actual en SQLite (`test.db`)
- Los componentes `CandidateGenerator`, `StoryGraphBuilder` y `EditPlanOptimizer` ejecutan transacciones compatibles con SQLite, registrando correctamente enlaces de evidencia (`CandidateEvidenceLink`), metadatos de razonamiento y modelos downstream.
- Se verificó la idempotencia de reintentos y la ausencia de duplicados en `test.db`.

### 5.2 Entorno de Staging PostgreSQL
- **Auditoría de Entorno:** Se auditó el host en busca de daemon PostgreSQL o Docker (`psql`, `pg_ctl`, `docker`, `docker-compose`). Ninguno de estos servicios o binarios se encuentra instalado en la máquina (`CommandNotFoundException`).
- **Estado de Condición:** **`UNRESOLVED / TECHNICAL HOST BLOCKER`**.
- La verificación de transacciones concurrentes en clúster PostgreSQL de staging permanece como una condición técnica pendiente de infraestructura antes de habilitar EXP-002 como valor canónico predeterminado en producción.

---

## 6. Estrategia de Rollout Controlado

Dado que la evidencia es estadísticamente limitada y la evaluación humana está pendiente, la activación canónica universal presentaría un riesgo innecesario.

### 6.1 Directrices de Despliegue
1. **Conservar M13-P1 como Baseline Operacional Predeterminado:**
   - La configuración por defecto del sistema continúa utilizando `clustering_variant = "default"` (clustering por proximidad simple de $1.0\text{s}$).
2. **Activación Selectiva por Feature Flag:**
   - EXP-002 se mantiene plenamente disponible en el código base y seleccionable mediante el parámetro de configuración `clustering_variant = "variant_b"` o mediante la variable de entorno `ENABLE_M3_RELATIONAL_CLUSTERING = true`.
3. **Fase de Evaluación Canary / Shadow:**
   - Habilitar la variante en una muestra controlada de VODs reales representativos y monitorizar:
     - Tasa de sobre-fusiones (eventos no relacionados absorbidos).
     - Duración media de candidatos y dead air acumulado.
     - Densidad de cortes y aceptación en revisión humana.
4. **Garantía de Reversibilidad:**
   - El rollback a M13-P1 se realiza instantáneamente cambiando el flag de configuración, sin migraciones destructivas de base de datos ni pérdida de linaje histórico.
5. **Preservación de Versiones de Baseline:**
   - **No se creará una línea base canonical `M13-P2`** hasta que esta revisión obtenga aprobación definitiva.

---

## 7. Lenguaje Científico y Limitaciones Metodológicas

1. **Tamaño del Conjunto de Prueba ($N=3$ Reales + $1$ Sintético):** La evaluación audiovisual real cubre 3 grabaciones concretas (1 clutch gameplay, 1 stream conversacional, 1 corte de escena en VOD de 5h).
2. **Ausencia de Significancia Estadística Global:** No se asegura superioridad universal en cualquier categoría arbitraria de streaming.
3. **Trade-offs Reales y Medibles:** En `case-test-005`, la pérdida geométrica estricta ($-0.0208$) es una consecuencia directa de absorber la pausa entre setup y payoff. En grabaciones reales (`real-eval-001`, `real-eval-002`), la variante reduce entre $1.75\text{s}$ y $2.65\text{s}$ de pre-roll/post-roll inactivo gracias al snapping a límites de habla.

---

## 8. Verificación de Quality Gates del Repositorio

Todos los controles de calidad canónicos del repositorio fueron ejecutados satisfactoriamente:

- **Pytest:** 93/93 pruebas pasadas (`uv run pytest tests/`, 4.96s).
  - Incluye `tests/unit/benchmark/test_exp_002_causal_controls.py` (8/8 controles negativos validados).
  - Incluye `tests/unit/benchmark/test_exp_002_cache_invalidation.py` (7/7 pruebas de invalidación de caché e idempotencia validadas).
- **Mypy:** Tipado estricto completado con éxito (`uv run mypy packages/ apps/`, 0 errores en 155 archivos).
- **Frontend Lint:** ESLint ejecutado sin errores (`npm run lint` en `apps/web`).
- **Frontend Type-Check:** Verificación TypeScript sin errores (`tsc --noEmit` en `apps/web`).
- **Frontend Production Build:** Compilación de producción exitosa (`npm run build` en `apps/web`, 14 rutas estáticas y dinámicas generadas).
- **Consistencia de Bóveda Obsidian:** 16/16 documentos canónicos requeridos presentes y válidos (`uv run python scripts/check_vault.py`).

---

## 9. Veredicto de Gobernanza

De conformidad con los criterios de gobernanza técnica y editorial:

- **Arquitectura y Determinismo:** APTOS Y VERIFICADOS. Algoritmo congelado inmutable.
- **Linaje de Caché e Idempotencia:** VERIFICADO (7/7 tests pasando; upstream M2 vinculado a M3).
- **Rendimiento de Ejecución:** ÓPTIMO (<0.3ms por segmento de clustering).
- **Evidencia Audiovisual Real:** Extraída y compilada en paquete ciego ($N=3$).
- **Panel Editorial Humano:** PENDIENTE (No hay revisores humanos; prohibido fabricar votos).
- **Infraestructura Staging PostgreSQL:** PENDIENTE (Bloqueador de entorno local; Docker/Postgres no disponible).

Por consiguiente, se ratifica la resolución formal:

```
EXP-002 PROMOTION CONDITIONAL — EDITORIAL VALIDATION PENDING
```

### Resumen de Condiciones de Promoción:
| Condición | Estado | Justificación / Evidencia |
| :--- | :---: | :--- |
| **1. Validación Audiovisual Real ($N \ge 3$)** | **CUMPLIDA** | 3 grabaciones reales evaluadas (`real-eval-001`, `002`, `003`) con huellas SHA-256 e intervalos auditados. |
| **2. Endurecimiento de Claves de Caché** | **CUMPLIDA** | M2 vinculado a `_run_sig` y `_candidate_sig`. 7/7 tests de regresión pasando en `test_exp_002_cache_invalidation.py`. |
| **3. Paquete Blinded A/B para Revisores** | **CUMPLIDA** | Serializado en `exp002_real_ab_evaluation_package.json` con asignaciones ciegas aleatorizadas. |
| **4. Panel de Revisión Editorial Ciega Humana** | **PENDIENTE** | En espera de evaluación por revisores humanos reales. Prohibida la simulación de votos por IA. |
| **5. Validación Staging PostgreSQL** | **BLOQUEADA** | Bloqueador de entorno técnico (host carece de Docker o servicio PostgreSQL). |

