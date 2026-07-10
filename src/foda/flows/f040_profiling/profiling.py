"""Flujo 040: Profiling (feature profiling).

Banda tracer_bullet: contrato de clase + execute()/write_outputs() que arman
y persisten el reporte minimo (esquema {schema_version, client, flow, success})
de forma deterministica, sin sobreescribir run() (template method heredado de
Flow), calcado del patron de Ingestion.

Banda stab_1 (bucle TDD en curso, red/green/refactor caso a caso):
- Caso 1 (CA-18, CA-19): bump aditivo de schema_version a "0.2" (DS-PRF-7);
  identidad client/flow/success sin cambios de tipo ni valor.
- Caso 2 (CA-20, CA-17): execute() arma el bloque health con las 6 claves
  fijas (global_score, files_declared, files_healthy, files_with_problems,
  problems_by_type, pareto). Implementacion MINIMA (NC-2, TDD estricto): para
  el fixture "todos sanos" del caso 2 basta con las 6 claves presentes,
  global_score==1.0 y pareto==[]; los valores de conteos, problems_by_type y
  la formula ponderada de global_score son placeholders (0 / {} / 1.0) que los
  casos 3-22 iran forzando a su forma real, uno a uno (fake-it-till-you-make-it).
  No se lee bronze/ ni client_register.yaml (fuera de alcance, DS-PRF-1).
- Caso 3 (CA-06, DS-PRF-3): health.files_declared ya no es un placeholder
  fijo; se lee de self._ingestion_report["summary"]["files_declared"]
  (cargado en load_inputs). files_healthy, files_with_problems,
  problems_by_type, global_score y pareto siguen como placeholders minimos
  (0 / {} / 1.0 / []) hasta sus propios casos (4-22).
- Caso 4 (CA-07, DS-PRF-3): health.files_healthy ya no es un placeholder
  fijo; se cuenta iterando datasets[].files[] de self._ingestion_report y
  sumando los archivos sanos (status=="ingested" e inconsistencies==[]).
  files_with_problems, problems_by_type, global_score y pareto siguen como
  placeholders minimos (0 / {} / 1.0 / []) hasta sus propios casos (5-22).
- Caso 5 (CA-08, DS-PRF-3): health.files_with_problems ya no es un
  placeholder fijo; se cuenta iterando datasets[].files[] de
  self._ingestion_report y sumando los archivos con problemas
  (status!="ingested" o inconsistencies!=[]). problems_by_type, global_score
  y pareto siguen como placeholders minimos ({} / 1.0 / []) hasta sus propios
  casos (7-22). Refactor: _contar_archivos_sanos (caso 4) y
  _contar_archivos_con_problemas (caso 5) son predicados complementarios
  (De Morgan) sobre la misma iteracion de datasets[].files[]; se extrajeron
  _archivos() (aplana la estructura anidada) y _es_archivo_sano() (predicado
  unico) para eliminar la duplicacion, sin cambiar el resultado de ninguno
  de los dos contadores.
- Caso 7 (CA-11, DS-PRF-4): health.problems_by_type ya no es un placeholder
  fijo; se cuenta, sobre la lista top-level self._ingestion_report
  ["inconsistencies"], el numero de ocurrencias de cada uno de los 4 tipos
  fijos del vocabulario cerrado (missing_file, unexpected_file,
  missing_column, unexpected_column). global_score y pareto siguen como
  placeholders minimos (1.0 / []) hasta sus propios casos (9-19).
- Caso 10 (CA-02, DS-PRF-2): health.global_score ya no es un placeholder
  fijo; se calcula con la formula ponderada real (pesos missing_file=1.0,
  missing_column=0.5, unexpected_file=0.3, unexpected_column=0.1) sobre
  problems_by_type, redondeada a 4 decimales, con el borde
  files_declared==0 -> 1.0 (sin division por cero, ratificado en spec.md).
  pareto sigue como placeholder minimo ([]) hasta sus propios casos
  (15-19).
- Caso 16 (CA-15, DS-PRF-5): health.pareto ya no es un placeholder fijo;
  se construye con el helper _pareto(problems_by_type), que incluye solo
  los tipos con count>=1 (sin entradas para los tipos en 0), preservando
  la suma total de counts respecto a problems_by_type. pct (CA-16) y el
  ordenamiento por count desc/type asc (CA-13/CA-14) siguen pendientes de
  sus propios casos (17-19).

Nota (NC-6): una version previa del caso 2 adelanto de una vez toda la logica
de health (DS-PRF-2..5). Por decision del humano se restauro el TDD estricto:
esa logica se revirtio a este minimo para reconstruirla caso a caso con
rojo->verde genuino.
"""

import json

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowResult

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

_TIPOS_INCONSISTENCIA = (
    "missing_file",
    "unexpected_file",
    "missing_column",
    "unexpected_column",
)
"""Vocabulario cerrado de tipos de inconsistencia (DS-PRF-4): las 4 claves
fijas que siempre debe tener health.problems_by_type (CA-11, CA-12)."""

_PESOS_GLOBAL_SCORE = {
    "missing_file": 1.0,
    "unexpected_file": 0.3,
    "missing_column": 0.5,
    "unexpected_column": 0.1,
}
"""Pesos ratificados de la formula ponderada de global_score (DS-PRF-2),
con las mismas 4 claves y el mismo orden que _TIPOS_INCONSISTENCIA."""


class Profiling(Flow):
    """Flujo 040: analiza el ingreso ingerido y emite reporte de profiling
    (profiling_report.json)."""

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
        "0.2", client, flow, success) + bloque health con las 6 claves fijas.

        files_declared (caso 3, DS-PRF-3), files_healthy/files_with_problems
        (casos 4-5, DS-PRF-3), problems_by_type (caso 7, DS-PRF-4),
        global_score (caso 10, DS-PRF-2) y pareto (caso 16, DS-PRF-5) ya se
        derivan del ingestion_report real. pct (CA-16) y el ordenamiento de
        pareto (CA-13/CA-14) siguen pendientes de sus propios casos
        (17-19), TDD estricto (NC-2)."""
        files_declared = self._ingestion_report.get("summary", {}).get(
            "files_declared", 0
        )
        files_healthy = self._contar_archivos_sanos(self._ingestion_report)
        files_with_problems = self._contar_archivos_con_problemas(
            self._ingestion_report
        )
        problems_by_type = self._problems_by_type(self._ingestion_report)
        global_score = self._global_score(files_declared, problems_by_type)
        pareto = self._pareto(problems_by_type)
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

    @staticmethod
    def _archivos(ingestion_report: dict):
        """Aplana datasets[].files[] del ingestion_report en un unico
        iterable de archivos, evitando repetir el doble for en cada
        contador (DS-PRF-3)."""
        return (
            archivo
            for dataset in ingestion_report.get("datasets", [])
            for archivo in dataset.get("files", [])
        )

    @staticmethod
    def _es_archivo_sano(archivo: dict) -> bool:
        """Un archivo esta sano si fue ingerido (status=="ingested") y no
        tiene inconsistencias. "Con problemas" (CA-08) es exactamente la
        negacion de "sano" (CA-07): status!="ingested" o inconsistencies!=[]
        equivale, por De Morgan, a not(status=="ingested" e
        inconsistencies==[])."""
        return archivo.get("status") == "ingested" and not archivo.get(
            "inconsistencies"
        )

    @classmethod
    def _contar_archivos_sanos(cls, ingestion_report: dict) -> int:
        """Caso 4 (CA-07, DS-PRF-3): cuenta, en datasets[].files[] del
        ingestion_report, los archivos sanos."""
        return sum(
            1 for archivo in cls._archivos(ingestion_report)
            if cls._es_archivo_sano(archivo)
        )

    @classmethod
    def _contar_archivos_con_problemas(cls, ingestion_report: dict) -> int:
        """Caso 5 (CA-08, DS-PRF-3): cuenta, en datasets[].files[] del
        ingestion_report, los archivos con problemas (complemento exacto de
        _es_archivo_sano)."""
        return sum(
            1 for archivo in cls._archivos(ingestion_report)
            if not cls._es_archivo_sano(archivo)
        )

    @staticmethod
    def _problems_by_type(ingestion_report: dict) -> dict:
        """Caso 7 (CA-11, DS-PRF-4): cuenta, sobre la lista top-level
        ingestion_report["inconsistencies"], las ocurrencias de cada uno de
        los 4 tipos fijos del vocabulario cerrado. Siempre devuelve las 4
        claves, incluso en 0 (CA-12)."""
        conteos = {tipo: 0 for tipo in _TIPOS_INCONSISTENCIA}
        for inconsistencia in ingestion_report.get("inconsistencies", []):
            tipo = inconsistencia.get("type")
            if tipo in conteos:
                conteos[tipo] += 1
        return conteos

    @staticmethod
    def _global_score(files_declared: int, problems_by_type: dict) -> float:
        """Caso 10 (CA-02, DS-PRF-2): formula ponderada de global_score.

        penalizacion_total = Sum(peso[tipo] * problems_by_type[tipo]);
        global_score = max(0.0, 1.0 - penalizacion_total/files_declared),
        redondeado a 4 decimales. Borde files_declared==0 -> 1.0 (sin
        division por cero), ratificado en spec.md DS-PRF-2."""
        if files_declared == 0:
            return 1.0
        penalizacion_total = sum(
            peso * problems_by_type.get(tipo, 0)
            for tipo, peso in _PESOS_GLOBAL_SCORE.items()
        )
        return round(max(0.0, 1.0 - penalizacion_total / files_declared), 4)

    @staticmethod
    def _pareto(problems_by_type: dict) -> list:
        """Caso 16 (CA-15, DS-PRF-5): construye pareto a partir de
        problems_by_type incluyendo solo los tipos con count>=1 (sin
        entradas para los tipos en 0), sin perder informacion: la suma de
        los counts de pareto siempre coincide con la suma de
        problems_by_type.values(). Caso 17 (CA-16, DS-PRF-5): cada entrada
        incluye ademas pct=round(count/total,4), con total=Σ(
        problems_by_type.values()); no hay division por cero porque solo se
        entra a este calculo cuando existe al menos un tipo con count>=1
        (total>=1 en ese caso). Orden queda para sus propios casos
        (18-19)."""
        total = sum(problems_by_type.values())
        return [
            {"type": tipo, "count": count, "pct": round(count / total, 4)}
            for tipo, count in problems_by_type.items()
            if count >= 1
        ]

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
