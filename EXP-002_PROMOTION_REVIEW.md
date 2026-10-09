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

## 3. Comparativa Editorial Humana

### 3.1 Disponibilidad de Salidas Renderizables
- Al no existir el archivo de origen físico de `case-test-005_src.mp4`, no se pueden generar vídeos finales reproducibles de los dos montajes (A: M13-P1 baseline vs B: EXP-002 frozen) para dicho caso sintético.
- Para el caso real `case-test-real-004`, ambas variantes producen exactamente los mismos intervalos $[20.0, 45.0]$ y $[50.0, 65.0]$, por lo que las salidas A y B son bit a bit idénticas.

### 3.2 Panel de Revisión a Ciegas
- **Revisores Participantes:** 0 (ningún panel de revisores humanos ha evaluado los montajes).
- **Veredicto Humano:** **`UNTESTED / PENDING HUMAN EVALUATION`**.
- No se fabrican puntuaciones subjetivas de coherencia, ritmo o timing cómico ni se asume preferencia humana sin evaluación perceptual fehaciente.

---

## 4. Correctitud de Configuración de Producción y Caché

Se realizó una auditoría minuciosa del mecanismo de firmas de derivación (`derivation_signature`) en [`CandidateGenerator`](file:///c:/Users/adria/Documents/EditorDirectos/stream-editor-ai/packages/editorial/src/stream_editor/editorial/generator.py):

### 4.1 Firma de Ejecución (`_run_sig`)
```python
def _run_sig(project_id, source_asset_id, config, provider_name, prompt_version, ranking_profile_name):
    data = {
        "project_id": project_id,
        "source_asset_id": source_asset_id,
        "config": config.model_dump(),
        "provider": provider_name,
        "prompt_version": prompt_version,
        "ranking_profile": ranking_profile_name,
        "generator_version": GENERATOR_VERSION,
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
```
- **Parámetros Incluidos:** Serializa íntegramente `CandidateWindowConfig` (incluyendo `clustering_config` con `max_related_event_gap`, `backward_setup_window`, `scene_boundary_hard_stop`, `minimum_relation_confidence` y `version`).
- **Deficiencia Detectada:** `_run_sig` **no incluye el hash de entrada de los artefactos M2** (`TranscriptRun.derivation_signature` o firma de `TimelineEvents`). Si la transcripción o la detección visual cambian pero el `source_asset_id` se mantiene, un `CandidateRun` completado previo podría ser reutilizado de forma inválida.

### 4.2 Firma de Candidato Individual (`_candidate_sig`)
```python
def _candidate_sig(project_id, source_asset_id, start_time, end_time, core_start, core_end, generator_version, clustering_version="default"):
    data = {
        "project_id": project_id,
        "source_asset_id": source_asset_id,
        "start_time": round(start_time, 3),
        "end_time": round(end_time, 3),
        "core_start": round(core_start, 3),
        "core_end": round(core_end, 3),
        "generator_version": generator_version,
        "clustering_version": clustering_version,
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
```
- **Deficiencia Detectada:** Solo incorpora el identificador de versión en cadena (`clustering_version`), pero no el hash de los parámetros detallados ni la firma de los eventos de entrada M2.
- **Riesgo Operativo:** Si se ajustan parámetros internos bajo la misma etiqueta de versión o si se evalúan variantes concurrentes, la búsqueda por firma de candidato podría recuperar registros generados con configuraciones dispares si los límites temporales coinciden.
- **Requisito para Activación Canónica:** Incorporar el hash completo de configuración y la firma de dependencias M2 en la clave de invalidación de candidatos.

---

## 5. Verificación Operacional y PostgreSQL

### 5.1 Estado Actual en SQLite (`test.db`)
- Los componentes `CandidateGenerator`, `StoryGraphBuilder` y `EditPlanOptimizer` ejecutan transacciones compatibles con SQLite, registrando correctamente enlaces de evidencia (`CandidateEvidenceLink`), metadatos de razonamiento y modelos downstream.
- Se verificó la idempotencia de reintentos y la ausencia de duplicados en `test.db`.

### 5.2 Entorno de Staging PostgreSQL
- El entorno local no cuenta con un contenedor Docker o daemon PostgreSQL en ejecución.
- Por tanto, la verificación en PostgreSQL de producción no ha podido ser ejecutada en esta sesión.
- **Condición Resolutoria:** Se registra la validación en staging PostgreSQL como una **condición pendiente obligatoria** antes de habilitar EXP-002 como valor canónico por defecto.

---

## 6. Estrategia de Rollout Controlado

Dado que la evidencia es estadísticamente limitada ($N=2$) y los efectos perceptuales de la pausa permanecen sin verificar, la activación canónica universal presentaría un riesgo innecesario.

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

1. **Tamaño del Conjunto de Prueba ($N=2$):** La evidencia descansa exclusivamente sobre 1 caso sintético de prueba y 1 fragmento temporal de un VOD real de 5 horas.
2. **Ausencia de Generalización Demostrada:** Al haber registrado 0 fusiones en el caso real, no se puede inferir generalización a otros estilos de stream, géneros de videojuegos o dinámicas de creadores.
3. **No Significancia Estadística:** Los resultados no poseen significancia estadística formal ni permiten asegurar superioridad global.
4. **Trade-offs Reales y Medibles:** La pérdida geométrica en precisión estricta ($-0.0208$) es un hecho medido incontrovertible. Si el valor narrativo supera esa pérdida es una decisión cualitativa humana que requiere corroboración editorial.

---

## 8. Verificación de Quality Gates del Repositorio

Todos los controles de calidad canónicos del repositorio fueron ejecutados satisfactoriamente:

- **Pytest:** 86/86 pruebas pasadas (`uv run pytest tests/`, 7.41s).
  - Incluye `tests/unit/benchmark/test_exp_002_causal_controls.py` con 8/8 controles negativos validados.
- **Mypy:** Tipado estricto completado con éxito (`uv run mypy packages/ apps/`, 0 errores en 155 archivos).
- **Frontend Lint:** ESLint ejecutado sin errores (`npm run lint` en `apps/web`).
- **Frontend Type-Check:** Verificación TypeScript sin errores (`tsc --noEmit` en `apps/web`).
- **Frontend Production Build:** Compilación de producción exitosa (`npm run build` en `apps/web`, 7 rutas estáticas y dinámicas generadas).
- **Consistencia de Bóveda Obsidian:** 16/16 documentos canónicos requeridos presentes y válidos (`python scripts/check_vault.py`).

---

## 9. Veredicto de Gobernanza

De conformidad con los criterios de gobernanza técnica y editorial:

- **Arquitectura y Código:** Aptos, probados y completamente deterministas.
- **Evidencia Editorial:** Parcial; mejora demostrada en 1 caso sintético, pero valor de la pausa en estado `UNKNOWN` y panel humano no ejecutado.
- **Compatibilidad de Producción:** Validada en SQLite; pendiente en staging PostgreSQL.

Por consiguiente, se emite la resolución formal:

```
EXP-002 PROMOTION CONDITIONAL — EDITORIAL VALIDATION REQUIRED
```

### Condiciones Obligatorias para Promoción Definitiva:
1. **Validación Perceptual:** Evaluar audiovisual mente al menos 3 casos reales donde se fusionen eventos para confirmar si la pausa retenida aporta valor de timing o introduce silencio indeseado.
2. **Panel de Revisión Editorial Ciega:** Ejecutar una comparativa A/B con al menos 2 editores humanos sobre montajes reales para evaluar preferencia de ritmo.
3. **Endurecimiento de Claves de Caché:** Integrar la firma de artefactos M2 en la derivación de candidatos para garantizar una invalidación estricta ante cambios upstream.
4. **Validación Staging PostgreSQL:** Probar la idempotencia y retención de enlaces de evidencia en el clúster PostgreSQL de staging.
