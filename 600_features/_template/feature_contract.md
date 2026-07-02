# Feature Contract — <feature>

> Artefacto **a nivel feature** (por encima de las bandas), creado por `feature_definer` en el paso *Definir*.
> Es la **"estrella polar"**: la definición de **"terminado" total** de la feature. Materializa P5 (contratos
> explícitos antes de ejecutar) y es **obligatorio antes de iniciar la primera banda** (`D-030`).
> **Una feature tiene un solo `feature_contract`**, aunque recorra varias bandas (`tracer_bullet → stab_n`).

## Estrella Polar
<Una frase: el valor total que entrega la feature cuando está "terminada" de verdad.>

## Definición de "Terminado" (feature completa)
Condiciones que deben cumplirse para considerar la feature **terminada** (no una banda suelta, sino el total):
- <Comportamiento observable end-to-end que debe existir.>
- <Calidad / robustez esperada al cierre.>

## Alcance Total
**In scope (toda la feature, a través de sus bandas):**
- <...>

**Out of scope (nunca, o en otra feature):**
- <...>

## Bandas Previstas (eje vertical)
Qué endurece cada banda hacia la estrella polar (crear **solo** las que se necesiten; `D-029`):

| Banda | Qué aporta / endurece |
|---|---|
| `tracer_bullet` | <slice vertical mínimo end-to-end (NC-4).> |
| `stab_1` | <estabilización: qué se refuerza sin ampliar alcance.> |

## Criterios de Aceptación de la Feature
> Nivel feature (la ambición total). Los criterios **por celda** viven en el `spec.md` de cada banda.
1. <Qué debe ser cierto cuando la feature esté terminada; verificable.>

## Dependencias
- <Otras features / artefactos / flujos requeridos por la feature completa.>

## Relación con Hitos de Producto
- <Opcional: a qué hito emergente (MVP / Final) contribuye esta feature, si aplica (`D-029`).>
