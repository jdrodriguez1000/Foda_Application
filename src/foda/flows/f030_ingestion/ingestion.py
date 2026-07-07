"""Flujo 030: Ingestion (feature ingestion, banda tracer_bullet).

Fuente: 600_features/ingestion/tracer_bullet/spec.md (DS-ING-1..8) y plan.md
(TSK-01..TSK-36). Bucle TDD en curso: esqueleto minimo para el caso 1 (CA-14)
en fase ROJA (tdd_tester). Declara requires/produces (Artifact) segun el
contrato observable de la spec/plan; NO sobreescribe execute()/write_outputs()
todavia, por lo que run(ctx) falla con NotImplementedError (heredado de
Flow.execute, foda/core/flow.py) tras pasar validate(). La logica real
(lectura de archivos, deteccion de separador, validacion de columnas, copia a
bronze y escritura del reporte) la agrega tdd_coder en la fase VERDE.
"""

from foda.core.flow import Artifact, Flow

# DS-ING-8: requires/produces declarados; no se amplia ClientContext/Artifact (NC-3).
_REQUIRES = [
    Artifact(
        name="contract_data",
        base="outputs",
        relative="010_discovery/contract_data.json",
    ),
    Artifact(
        name="map_client_data",
        base="outputs",
        relative="020_onboarding/map_client_data.json",
    ),
]
_PRODUCES = [
    Artifact(
        name="ingestion_report",
        base="outputs",
        relative="030_ingestion/ingestion_report.json",
    ),
]


class Ingestion(Flow):
    """Flujo 030: carga y valida datos crudos, copia inmutable a bronze y
    emite reporte de carga (ingestion_report.json).

    Esqueleto minimo (fase ROJA, caso 1): hereda Flow, declara requires/
    produces y no sobreescribe run(). load_inputs/validate/execute/
    write_outputs quedan con el comportamiento base de Flow (execute() base
    lanza NotImplementedError) hasta que tdd_coder implemente el caso 1.
    """

    name = "ingestion"
    requires = _REQUIRES
    produces = _PRODUCES
