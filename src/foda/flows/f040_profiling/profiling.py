"""Flujo 040: Profiling (feature profiling, banda tracer_bullet).

Fuente: 600_features/profiling/tracer_bullet/spec.md y plan.md. Bucle TDD en
curso: caso 1 (CA-01) en VERDE (tdd_coder). Implementacion minima (NC-2):
solo se declara el contrato de la clase (name/requires/produces), calcado
del patron de Ingestion (ver f030_ingestion/ingestion.py). Los hooks
load_inputs/execute/write_outputs (comportamiento real de ejecucion) llegan
en casos posteriores del bucle TDD (no se adelantan).

Caso 2 (CA-02) en VERDE (tdd_coder, TSK-05): Profiling no sobreescribe run()
(usa el template method heredado de Flow); execute(ctx) arma en memoria el
reporte minimo (esquema {schema_version, client, flow, success}, sin leer
bronze todavia -esta banda no calcula salud de datos, NC-2) y
write_outputs(ctx, result) lo persiste de forma deterministica, calcado del
patron de Ingestion.write_outputs (sort_keys + indent=2 + newline final, sin
la parte de copia a bronze que no aplica a este flujo).

Banda stab_1, caso 1 (CA-18, CA-19, TSK-02) en VERDE (tdd_coder): bump
aditivo de schema_version a "0.2" (DS-PRF-7); identidad client/flow/success
sin cambios de tipo ni valor.

Banda stab_1, caso 2 (CA-20, CA-17, TSK-03/TSK-04) en VERDE (tdd_coder):
execute() lee ingestion_report.json (ya cargado por load_inputs, DS-PRF-1..5
de 600_features/profiling/stab_1/spec.md) y arma el bloque health con las
6 claves fijas (global_score, files_declared, files_healthy,
files_with_problems, problems_by_type, pareto), aplicando la formula
completa de DS-PRF-2 (pesos por tipo, redondeo a 4 decimales, borde
files_declared==0), los conteos de DS-PRF-3, el agregado por tipo de
DS-PRF-4 y el ranking pareto de DS-PRF-5. Se implementa de una vez porque
es la unica lectura del reporte y evita retrabajo innecesario en los casos
3-22 (que solo anaden aserciones sobre fixtures adicionales, no logica
nueva); no se leen bronze/ ni client_register.yaml (fuera de alcance,
DS-PRF-1).

Banda stab_1, caso 2 (tdd_refactor, TSK-35 parcial): sin cambio de
comportamiento, se extrae el cuerpo de execute() en helpers privados puros
del modulo (_conteos_de_archivos, _problems_by_type, _global_score,
_pareto), uno por responsabilidad de DS-PRF-3/4/2/5, para legibilidad y
para que los casos 3-22 (solo fixtures nuevas, sin logica nueva) no deban
tocar un execute() monolitico.
"""

import json

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowResult

_PESOS_POR_TIPO = {
    "missing_file": 1.0,
    "missing_column": 0.5,
    "unexpected_file": 0.3,
    "unexpected_column": 0.1,
}

_REQUIRES = [
    Artifact(
        name="ingestion_report",
        base="outputs",
        relative="030_ingestion/ingestion_report.json",
    ),
]
_PRODUCES = [
    Artifact(
        name="profiling_report",
        base="outputs",
        relative="040_profiling/profiling_report.json",
    ),
]


def _conteos_de_archivos(ingestion_report: dict) -> tuple[int, int, int]:
    """DS-PRF-3: deriva (files_declared, files_healthy, files_with_problems)
    de ingestion_report. files_declared viene de summary.files_declared; el
    resto de iterar datasets[].files[], donde un archivo declarado es sano
    si status=="ingested" y su lista inconsistencies esta vacia (en caso
    contrario, con problemas)."""
    files_declared = int(ingestion_report.get("summary", {}).get("files_declared", 0))

    files_healthy = 0
    files_with_problems = 0
    for dataset in ingestion_report.get("datasets", []):
        for file_entry in dataset.get("files", []):
            sano = (
                file_entry.get("status") == "ingested"
                and not file_entry.get("inconsistencies")
            )
            if sano:
                files_healthy += 1
            else:
                files_with_problems += 1

    return files_declared, files_healthy, files_with_problems


def _problems_by_type(ingestion_report: dict) -> dict[str, int]:
    """DS-PRF-4: cuenta ocurrencias por tipo sobre la lista top-level
    ingestion_report.inconsistencies[], devolviendo siempre las 4 claves
    fijas del vocabulario cerrado (0 si no hay ocurrencias)."""
    conteos = {tipo: 0 for tipo in _PESOS_POR_TIPO}
    for inconsistencia in ingestion_report.get("inconsistencies", []):
        tipo = inconsistencia.get("type")
        if tipo in conteos:
            conteos[tipo] += 1
    return conteos


def _global_score(files_declared: int, problems_by_type: dict[str, int]) -> float:
    """DS-PRF-2: penalizacion ponderada por tipo, normalizada sobre
    files_declared, con clamp inferior 0.0, redondeo a 4 decimales y borde
    files_declared==0 -> 1.0 (sin division por cero)."""
    if files_declared == 0:
        return 1.0

    penalizacion_total = sum(
        _PESOS_POR_TIPO[tipo] * conteo for tipo, conteo in problems_by_type.items()
    )
    return round(max(0.0, 1.0 - penalizacion_total / files_declared), 4)


def _pareto(problems_by_type: dict[str, int]) -> list[dict]:
    """DS-PRF-5: ranking por tipo (solo count>=1), orden count desc / type
    asc, cada entrada {type, count, pct} con pct sobre el total de
    ocurrencias. [] si no hay problemas."""
    total_problemas = sum(problems_by_type.values())
    if total_problemas == 0:
        return []

    tipos_con_problemas = sorted(
        (tipo for tipo, conteo in problems_by_type.items() if conteo >= 1),
        key=lambda tipo: (-problems_by_type[tipo], tipo),
    )
    return [
        {
            "type": tipo,
            "count": problems_by_type[tipo],
            "pct": round(problems_by_type[tipo] / total_problemas, 4),
        }
        for tipo in tipos_con_problemas
    ]


class Profiling(Flow):
    """Flujo 040: analiza el bronze ingerido y emite reporte de profiling
    (profiling_report.json).

    Caso 1 (CA-01): solo el contrato de clase (name, requires, produces).
    Caso 2 (CA-02): execute()/write_outputs() arman y persisten el reporte
    minimo (sin sobreescribir run(), heredado de Flow).
    """

    name = "profiling"
    requires = _REQUIRES
    produces = _PRODUCES

    def __init__(self) -> None:
        self._report: dict | None = None
        self._ingestion_report: dict | None = None

    def load_inputs(self, ctx: ClientContext) -> None:
        """Lee y parsea ingestion_report.json (unico require) a estado de
        instancia solo si existe; si no existe, deja el estado sin cargar
        para que validate() (base) lo detecte."""
        path = self.requires[0].path(ctx)
        if path.exists():
            self._ingestion_report = json.loads(path.read_text(encoding="utf-8"))

    def execute(self, ctx: ClientContext) -> FlowResult:
        """Arma en memoria el reporte de profiling: identidad (schema_version
        "0.2", client, flow, success) + bloque health (DS-PRF-2..5) derivado
        unicamente de ingestion_report.json (sin leer bronze/, DS-PRF-1).
        Orquesta los helpers privados puros que calculan cada parte del
        bloque health; no hace calculos propios."""
        ingestion_report = self._ingestion_report or {}

        files_declared, files_healthy, files_with_problems = _conteos_de_archivos(
            ingestion_report
        )
        problems_by_type = _problems_by_type(ingestion_report)
        global_score = _global_score(files_declared, problems_by_type)
        pareto = _pareto(problems_by_type)

        self._report = {
            "schema_version": "0.2",
            "client": ctx.name,
            "flow": "profiling",
            "success": True,
            "health": {
                "global_score": global_score,
                "files_declared": files_declared,
                "files_healthy": files_healthy,
                "files_with_problems": files_with_problems,
                "problems_by_type": problems_by_type,
                "pareto": pareto,
            },
        }
        return FlowResult(success=True, outputs=[self.produces[0].path(ctx)])

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        """Escribe profiling_report.json de forma deterministica (sort_keys
        + indent=2 + newline final), calcado de Ingestion.write_outputs."""
        path = self.produces[0].path(ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._report, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
