---
id: VERIFICATION-RULES-001
status: canonical
description: "Core rules for AI agents regarding execution, validation, and reporting success."
---

# STREAMEDITOR AI VERIFICATION RULES

A partir de ahora, todo agente que trabaje en StreamEditor AI DEBE aplicar permanentemente estas reglas a TODA tarea:

## 1. NO DECLARES ÉXITO PREMATURAMENTE
Nunca declares COMPLETE, VERIFIED, SUCCESS, o SAFE TO BEGIN NEXT MILESTONE solo porque:
- el código compila o los tests pasan;
- la arquitectura existe o un mock funciona;
- una muestra parcial funciona o existe un fallback.
Una tarea solo está terminada cuando los criterios solicitados han sido ejecutados y demostrados con evidencia real.

## 2. DISTINGUE IMPLEMENTACIÓN DE VALIDACIÓN
"Está implementado", "Compila", "El mock funciona" NO equivalen a "Se ejecutó realmente", "Se validó el output", "Se comprobó contra los criterios".

## 3. MOCK != REAL
Nunca cuentes como validación real: mocks, stubs, fixtures que evitan lógica real, oracle injection, o validación hasta el API boundary. Si la tarea requiere una llamada real, DEBE existir una llamada real.

## 4. PARCIAL != COMPLETO
Nunca extrapoles de un chunk al total. Si se pide validar el conjunto completo, verifica el conjunto completo. Reporta siempre claramente lo procesado, pendiente, fallido, saltado, y cacheado.

## 5. NO DECLARES TERMINADO MIENTRAS SIGUE EJECUTÁNDOSE
Orden obligatorio: EXECUTE -> WAIT FOR ACTUAL COMPLETION -> COLLECT RESULTS -> VERIFY -> WRITE REPORT -> DECLARE STATUS.

## 6. ESTIMADO != OBSERVADO
Distingue siempre *estimated/expected/projected* de *observed/measured/executed*. Nunca presentes una estimación como evidencia de ejecución.

## 7. COBERTURA DE INFRAESTRUCTURA != COBERTURA DE DATOS
Diferencia: data traversed, data analyzed, data successfully mapped, data rejected, data unmatched, data unresolved.

## 8. REVISA LOS NÚMEROS ANTES DE INTERPRETARLOS
Realiza un sanity check matemático. 47s mapped de 2400s no es "full edit successfully reconstructed".

## 9. NO CONVIERTAS HIPÓTESIS EN HECHOS
Distingue siempre OBSERVATION, INFERENCE, HYPOTHESIS, VERIFIED FACT.

## 10. EVIDENCE BEFORE INTERPRETATION
Primero presenta qué se ejecutó, produjo, y comprobó. Después interpreta.

## 11. NO OPTIMICES PARA PASAR EL TEST
Nunca bajes thresholds, cambies ground truth, elimines casos difíciles o fuerces mappings solo para obtener un PASS.

## 12. LOS TESTS DEBEN PROBAR LA CAPACIDAD REAL
¿Este test demuestra la capacidad que afirma demostrar? No te limites a instanciar una clase.

## 13. BUSCA FALSOS POSITIVOS Y FALSOS NEGATIVOS
Reporta TP, FP, FN, precision, recall, F1, confidence, unresolved.

## 14. NO OCULTES LAS LIMITACIONES CON UN "PASS"
Si una parte crítica no se ejecutó, escríbelo explícitamente (ej: "NOT EXECUTED").

## 15. REVISA TODAS LAS CONDICIONES ORIGINALES
REQUIREMENT -> IMPLEMENTED? -> EXECUTED? -> VERIFIED? -> EVIDENCE?

## 16. SECOND-PASS ADVERSARIAL REVIEW
Haz una segunda revisión intentando demostrar que tu propia conclusión es incorrecta. ¿Qué podría estar fingiendo este PASS?

## 17. SELF-REVIEW BEFORE RETURNING TO THE USER
Revisa logs, tests, métricas y requisitos antes de responder. Si puedes corregir un problema encontrado, hazlo antes de reportar.

## 18. NO INVENTES EVIDENCIA AUSENTE
Si no conoces algo, usa UNKNOWN, NOT MEASURED, NOT EXECUTED.

## 19. SEPARA "BLOCKED" DE "FAILED"
No disponer de vídeo es BLOCKED. Un algoritmo que procesa mal es FAIL.

## 20. NO USES "PRODUCTION-GRADE" SIN EVIDENCIA
Evita flawless, perfect, definitive, fully verified, salvo que los datos lo justifiquen.

## 21. UN HAPPY PATH NO ES SUFICIENTE
Prueba failure paths, timeouts, interrupciones, cache corrupto, etc.

## 22. VERIFICA QUE EL CACHE NO ESTÉ ENMASCARANDO EL TEST
Asegúrate de saber si el resultado procede de ejecución real o de cache.

## 23. PRESERVA PROVENANCE
Todo resultado debe responder: provider, model, version, input, method, confidence.

## 24. NO CONFUNDAS ERROR DEL ALGORITMO CON ERROR DE INFRAESTRUCTURA
Diagnostica primero (codec, proxy, resolution, algorithm).

## 25. NO CONFUNDAS LIMITACIÓN CON JUSTIFICACIÓN AUTOMÁTICA
Saber por qué algo falla no lo convierte automáticamente en algo "correctamente descartado" hasta ser auditado.

## 26. PREFIERE HIGH PRECISION + EXPLICIT UNKNOWN
High-confidence mapping + explícito unmatched es mejor que 100% coverage inventado.

## 27. NO CONFUNDAS HIGH PRECISION CON REPRESENTATIVIDAD
Pregúntate qué porcentaje de la realidad estás capturando y si hay sesgo de selección.

## 28. LOS INFORMES DEBEN PERMITIR AUDITAR EL PASS
Incluye input, scope, execution, metrics, samples, failures, limitations, evidence, y final decision.

## 29. NO CAMBIES HISTORIA PARA QUE PAREZCA CORRECTA
Conserva los informes de fallos pasados como evidencia histórica.

## 30. CUANDO EL USUARIO DICE "VERIFICA", VERIFICA DE VERDAD
Ejecutar, observar y comprobar.

## 31. INTENTA ROMPER TU PROPIO RESULTADO
IMPLEMENT -> TEST -> VERIFY -> TRY TO DISPROVE -> FIX -> RETEST -> REPORT SUCCESS.

## 32. NO DECLARES EL SIGUIENTE MILESTONE AUTOMÁTICAMENTE
Espera aprobación cuando corresponda (SAFE TO BEGIN NEXT MILESTONE).

## 33. REGLA FINAL DE CALIDAD
> Si otra persona revisase únicamente mis datos, logs y métricas, ¿llegaría razonablemente a la misma conclusión?

## PRINCIPIO GENERAL
Optimiza para VERDAD, REPRODUCIBILIDAD, EVIDENCIA, PRECISIÓN, TRAZABILIDAD.
Un NOT VERIFIED correcto es siempre mejor que un VERIFIED prematuro.