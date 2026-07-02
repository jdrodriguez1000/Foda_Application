# 600_features — Features de Desarrollo (SDD/TDD)

Esta carpeta contiene los **artefactos de desarrollo** de cada feature construida con la cadena de 8 agentes SDD/TDD. Una carpeta por feature, nombrada en `snake_case`.

> El detalle de cómo funciona la cadena (orquestación, gates, `state.json`) vive en [`700_architecture/sdd_tdd_workflow.md`](../700_architecture/sdd_tdd_workflow.md), que es la **fuente única de verdad**. Este README solo explica cómo usar esta carpeta.

## Qué vive aquí (y qué no)

En `600_features/<feature>/` viven **solo** los artefactos SDD y la máquina de estado:

```
600_features/<feature>/
├── definition.md      # feature_definer — qué y por qué
├── spec.md            # spec_writer — comportamiento, contratos, criterios de aceptación
├── plan.md            # plan_builder — cómo + lista de casos de test
├── verification.md    # spec_verifier — veredicto y trazabilidad
└── state.json         # máquina de estado de la cadena
```

El **código y los tests NO viven aquí**:
- Código de producción → `src/foda/…`
- Tests (unit e integración) → `tests/…`

## Cómo arrancar una feature nueva

1. Copia `_template/` a `600_features/<nombre_feature>/`.
2. La sesión principal invoca `feature_definer` con el nombre y la necesidad; el agente rellena `definition.md` e inicializa `state.json`.
3. La cadena continúa: `spec_writer` → 🚧gate → `plan_builder` → 🚧gate → bucle TDD (`tdd_tester` → `tdd_coder` → `tdd_refactor`) → `integration_tester` → `spec_verifier`.

Los archivos de `_template/` son **esqueletos**: contienen los encabezados de sección que cada agente debe rellenar. No los edites como si fueran una feature; son el molde a copiar.

## Estado de una feature

Se lee de un vistazo en su `state.json` (`status`, `current_stage`, `stages`). Ver el esquema y los valores válidos en [`sdd_tdd_workflow.md` §6](../700_architecture/sdd_tdd_workflow.md#6-convención-de-statejson).
