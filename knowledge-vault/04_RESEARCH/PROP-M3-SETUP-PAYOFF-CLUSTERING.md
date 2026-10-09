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

## 4. Estado de la Pausa Retenida $[4.0, 5.0]$

En el caso sintético `case-test-005`, la referencia humana activa comprende $[1.0, 4.0]$ y $[5.0, 9.0]$. EXP-002 selecciona $[1.0, 9.0]$, absorbiendo el segundo $[4.0, 5.0]$.
- **Inspección Audiovisual:** El archivo físico `case-test-005_src.mp4` no existe en disco (es una entidad sintética definida en metadatos y fixtures).
- **Veredicto Editorial de la Pausa:** Al no ser posible escuchar la cadencia del streamer ni observar la expresión facial durante ese segundo, su valor editorial se clasifica estrictamente como **`UNKNOWN`**.
- No se puede aseverar ausencia de dead air sin evaluación perceptual directa.

---

## 5. Comparativa Editorial Humana

- **Estado de Evaluación:** No se ha realizado un panel de ciego con revisores humanos para comparar los montajes resultantes de M13-P1 frente a EXP-002.
- **Veredicto:** **`PENDING HUMAN EDITORIAL EVALUATION`**. No se aduce preferencia humana sin pruebas perceptuales documentadas.

---

## 6. Correctitud de Configuración, Caché y PostgreSQL

### 6.1 Audit de Firmas de Derivación (`derivation_signature`)
- `CandidateRun.derivation_signature` incluye la configuración de clustering y del generador, pero **no incluye el hash de entrada de los artefactos M2** (transcripciones o eventos de línea temporal).
- `CandidateSegment.derivation_signature` incluye timestamps y la versión del generador/clustering (`exp002_variant_b`), pero no serializa el hash completo de parámetros ni la firma M2.
- **Requisito de Promoción:** Para activación canónica general, se debe garantizar que cualquier cambio en parámetros de clustering o en M2 invalide selectivamente los artefactos M3/M4/M5 sin afectar M1/M2.

### 6.2 Verificación PostgreSQL
- La persistencia ha sido validada en SQLite (`test.db`).
- El entorno de staging con PostgreSQL no se encuentra actualmente disponible en este host.
- **Requisito de Promoción:** Validar la idempotencia de transacciones, retries y ausencia de duplicados en el esquema de producción PostgreSQL antes de la activación canónica total.

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

**Decisión:** **`CONDITIONAL`**

### Condiciones Resolutorias Requeridas:
1. **Validación Perceptual de la Pausa:** Evaluar en al menos 3 casos reales renderizados si las pausas conversacionales retenidas aportan timing cómico o introducen dead air injustificado.
2. **Blind Review Editorial:** Registrar una prueba A/B ciega con revisores humanos sobre montajes reales comparables.
3. **Endurecimiento de Firmas de Derivación:** Incorporar el hash de entrada M2 y el hash de configuración completo en la firma de invalidación de caché de candidatos.
4. **Validación Staging PostgreSQL:** Ejecutar pruebas de idempotencia e inserción masiva en una instancia PostgreSQL de staging.
