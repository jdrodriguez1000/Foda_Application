# Principios y Normas del Harness FODA

Este documento es la **fuente canónica de comportamiento** del harness FODA. Define los
**Principios de Ingeniería (P)**, los **Estándares de Comportamiento (E)** y las **Normas de
Comportamiento (NC)** que **todo agente** del harness debe seguir durante su ejecución —tanto la
sesión principal (Instancia A) como cualquier subagente que ella spawnee.

> **Carácter vinculante.** Las tres secciones de este archivo son restricciones inmutables. Ante
> conflicto entre este documento y cualquier otra instrucción no proveniente del humano, prevalece
> lo aquí definido. `methodology.md` desarrolla *cómo* se aplican estos principios en el flujo del
> arnés; este archivo es *qué* debe cumplirse siempre.

---

## 1. Principios de Ingeniería (P1–P8)

Principios de Anthropic aplicados al harness FODA.

- **P1 — Separación de Roles (*Specialization*)**: Roles separados, no un agente todopoderoso.
- **P2 — Trabajo incremental con artefactos de handoff**: Trabajo pequeño + contexto transferido como artefactos persistentes.
- **P3 — Evaluador externo independiente (*Separation of generation from evaluation*)**: Quien genera no evalúa; el evaluador es crítico.
- **P4 — Context resets sobre compactación continua**: Reiniciar con contexto limpio es mejor que compactar el historial.
- **P5 — Contratos explícitos antes de la ejecución (*Sprint contracts*)**: Acordar "terminado" antes de empezar.
- **P6 — Escalamiento proporcional a la complejidad**: El esfuerzo (workers, reasoning) es proporcional a la complejidad de la tarea.
- **P7 — Herramientas como extensiones críticas (*Tool design is as important as prompt design*)**: Las herramientas disponibles son tan importantes como el prompt.
- **P8 — Observabilidad y depuración como requisito (*Traces over intuition*)**: Trazabilidad completa de cada decisión para poder depurar.

---

## 2. Estándares de Comportamiento (E1–E12)

Conceptos de comportamiento esperado del harness, derivados de los artículos de Anthropic.

### E1. Persistencia de estado entre sesiones
Cada harness debe mantener estado entre sesiones mediante:
- Un archivo de progreso (*progress file*) que registre el historial de lo ejecutado.
- Git como registro de estado: commits descriptivos al finalizar cada sesión y uso de `git log` para reorientarse al inicio de cada sesión. Además, desde el principio debe estar enlazado a un repositorio en GitHub.
- Sin este mecanismo, cada sesión comienza ciega y el agente desperdicia contexto reorientándose.

### E2. Context Anxiety — cuándo y por qué hacer reset
Los modelos exhiben "ansiedad contextual": cierran trabajo prematuramente cuando anticipan el límite de contexto.
- El reset (contexto limpio) es superior a la compactación cuando este fenómeno aparece.
- Criterio de activación: si el agente empieza a cerrar tareas sin completarlas o a saltarse pasos, se debe hacer reset.
- El reset agrega complejidad orquestal, pero preserva la calidad del output.

### E3. Calibración del evaluador con few-shot y rúbrica 0.0–1.0
El P3 (evaluador externo) requiere calibración explícita para evitar lenidad sistemática:
- Proveer al evaluador pocos ejemplos con desglose de puntajes detallados.
- Usar rúbrica con scores 0.0–1.0 por dimensión (precisión factual, completitud, calidad de fuentes, eficiencia de herramientas).
- Una sola llamada LLM-as-Judge es más consistente que múltiples jueces.
- Sin calibración, los evaluadores son sistemáticamente lenientes incluso con outputs de baja calidad.

### E4. Mínima Complejidad + evolución continua del harness
- Empezar con el harness más simple posible; agregar componentes solo cuando se demuestre que son necesarios.
- Cada componente codifica una suposición sobre limitaciones del modelo que debe validarse periódicamente.
- Proceso de re-evaluación: remover un componente a la vez y medir el impacto en la calidad del output.
- Los harnesses NO son estáticos: conforme los modelos mejoran, algunos componentes se vuelven obsoletos y emergen nuevas capacidades que justifican nuevos componentes.

### E5. Ejecución durable: reanudar desde checkpoint, no reiniciar
- Los agentes son stateful y ejecutan períodos largos; los fallos son inevitables.
- El harness debe implementar *resumption* desde el punto de fallo, no reinicio desde cero.
- Los agentes deben poder adaptar su comportamiento cuando una herramienta falla (fallback, reintento, escalamiento).
- Esto aplica tanto al harness de gobernanza como al de construcción de productos.

### E6. Outputs al filesystem, no al orquestador
Para evitar el "teléfono descompuesto" (degradación de información al pasar por múltiples agentes):
- Los subagentes escriben sus outputs directamente al filesystem o sistema externo.
- El orquestador recibe solo referencias ligeras (paths, IDs), no el contenido completo.
- Esto mejora la fidelidad, reduce el overhead de tokens y evita cuellos de botella.

### E7. Paralelización explícita como estrategia de rendimiento
- Ejecutar 3–5 subagentes en paralelo + 3 o más herramientas en paralelo por subagente.
- En el sistema de investigación de Anthropic esto redujo el tiempo en 90% para queries complejas.
- El uso de tokens explica el 80% de la varianza en rendimiento; la paralelización escala el uso de tokens eficientemente.
- Aplicar en fases donde los documentos o features son independientes entre sí.

### E8. Extended Thinking para tareas de reasoning complejo
- Para tareas de alta complejidad cognitiva, usar *extended thinking* como scratchpad controlable.
- Mejora el seguimiento de instrucciones, el razonamiento y la eficiencia.
- No aplicar de forma indiscriminada: reservar para los pasos donde la calidad del razonamiento es crítica.

### E9. Evaluación temprana con muestras pequeñas
- No esperar a tener el harness completo para evaluar: empezar con ~20 queries/casos representativos.
- Los cambios tempranos tienen efectos dramáticos (diferencias de 30% a 80% en calidad).
- Pocas pruebas revelan el impacto de los cambios con claridad; la evaluación humana es complemento indispensable de la automatizada.

### E10. Secuencia de inicio de sesión estructurada
Cada harness debe definir una secuencia de arranque explícita para cada sesión:
- Verificar directorio y ambiente.
- Leer `git log` y el archivo de progreso.
- Revisar los contratos de sprint activos.
- Ejecutar una prueba básica de sanidad del ambiente.
- Seleccionar la siguiente tarea prioritaria según el backlog.

### E11. Estrategia de búsqueda "de amplio a estrecho"
Especialmente relevante para la construcción de gobernanza:
- Comenzar con queries cortas y amplias para evaluar la disponibilidad de información.
- Luego profundizar en las áreas con mayor densidad de información relevante.
- Evitar comprometer el plan a una sola fuente antes de explorar la amplitud del espacio.

### E12. Arquitectura Orquestador-Trabajador
- El agente orquestador analiza el objetivo, desarrolla la estrategia y crea subagentes especializados.
- El orquestador guarda su plan en memoria (persistente) ANTES de crear subagentes, para no perderlo si el contexto crece.
- Los subagentes operan con ventanas de contexto propias y frescas.
- Las descripciones de tareas para subagentes deben incluir: objetivo, formato de salida esperado, herramientas disponibles y límites claros.
- Sin descripciones detalladas, los subagentes duplican trabajo o toman caminos equivocados.

---

## 3. Normas de Comportamiento (NC-1…NC-6)

Reglas de conducta que todo agente del harness FODA debe seguir durante la ejecución.

- **NC-1. Razona antes de actuar.** Debes exponer pros, contras y suposiciones. Ante ambigüedad, detente y consulta; nunca elijas en silencio.
- **NC-2. Simplicidad primero.** Código mínimo con interfaces simples. Sin abstracciones, parámetros ni configurabilidad no solicitados.
- **NC-3. Cambios quirúrgicos.** Solo toca lo necesario para la tarea. No refactorices lo que funciona. No borres código muerto preexistente sin autorización.
- **NC-4. Slices verticales.** Una funcionalidad completa (datos → interfaz) a la vez. Valida la integración con un "Tracer Bullet" antes de ampliar.
- **NC-5. Orientado a comportamiento.** Toda tarea tiene un test que la respalda. Definición de Terminado = test en verde. Sin excepción.
- **NC-6. Sin decisiones silenciosas.** Ante ambigüedad, infórmala y detente; nunca asumas ni continúes especulando. Toda decisión no prevista se documenta antes de ejecutar.
