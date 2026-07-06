"""Tests unitarios de Onboarding (feature onboarding, banda tracer_bullet).

Fuente: 600_features/onboarding/tracer_bullet/spec.md (CA-xx) y plan.md
(casos TDD, TSK-10.. TSK-32). Bucle TDD: un test por caso, ejecutado en orden
(state.json -> stages.tdd.cases).
"""

from pathlib import Path

from foda.core.context import ClientContext
from foda.core.flow import FlowResult
from foda.core.scaffold import create_client
from foda.flows.f020_onboarding.onboarding import Onboarding


def _contrato_valido() -> dict:
    """Fixture valido (TSK-10): ventas + inventario, 4+4 niveles, tal como
    figura en el Sec Contratos de Datos de la spec (entrada esperada)."""
    return {
        "schema_version": "0.1",
        "client": {"code": "ABC", "name": "Cliente ABC S.A.", "sector": "retail"},
        "product_hierarchy": {
            "levels": ["familia", "categoria", "subcategoria", "clase"],
            "members": [
                {
                    "familia": "Bebidas",
                    "categoria": "Aguas",
                    "subcategoria": "Sin gas",
                    "clase": "Agua 600ml",
                },
                {
                    "familia": "Bebidas",
                    "categoria": "Gaseosas",
                    "subcategoria": "Cola",
                    "clase": "Cola 1.5L",
                },
                {
                    "familia": "Snacks",
                    "categoria": "Papas",
                    "subcategoria": "Fritas",
                    "clase": "Papas 45g",
                },
            ],
        },
        "geography": {
            "levels": ["region", "pais", "ciudad", "sede"],
            "members": [
                {
                    "region": "Andina",
                    "pais": "Colombia",
                    "ciudad": "Bogota",
                    "sede": "Sede Centro",
                },
                {
                    "region": "Andina",
                    "pais": "Colombia",
                    "ciudad": "Medellin",
                    "sede": "Sede Norte",
                },
            ],
        },
        "historical_data": {
            "datasets": [
                {
                    "kind": "ventas",
                    "source_medium": "csv",
                    "periodicity": "mensual",
                    "fields": [
                        {
                            "name": "fecha",
                            "type": "date",
                            "required": True,
                            "maps_to": "time",
                        },
                        {
                            "name": "sede",
                            "type": "string",
                            "required": True,
                            "maps_to": "geography.sede",
                        },
                        {
                            "name": "clase",
                            "type": "string",
                            "required": True,
                            "maps_to": "product.clase",
                        },
                        {
                            "name": "cantidad",
                            "type": "integer",
                            "required": True,
                            "maps_to": "measure",
                        },
                        {
                            "name": "precio_unitario",
                            "type": "number",
                            "required": False,
                            "maps_to": None,
                        },
                    ],
                    "files": [
                        {
                            "name": "ventas_2023_2025.csv",
                            "period_start": "2023-01-01",
                            "period_end": "2025-12-31",
                        }
                    ],
                },
                {
                    "kind": "inventario",
                    "source_medium": "csv",
                    "periodicity": "mensual",
                    "fields": [
                        {
                            "name": "fecha",
                            "type": "date",
                            "required": True,
                            "maps_to": "time",
                        },
                        {
                            "name": "sede",
                            "type": "string",
                            "required": True,
                            "maps_to": "geography.sede",
                        },
                        {
                            "name": "clase",
                            "type": "string",
                            "required": True,
                            "maps_to": "product.clase",
                        },
                        {
                            "name": "stock",
                            "type": "integer",
                            "required": True,
                            "maps_to": "measure",
                        },
                    ],
                    "files": [
                        {
                            "name": "inventario_2024.csv",
                            "period_start": "2024-01-01",
                            "period_end": "2024-12-31",
                        },
                        {
                            "name": "inventario_2025.csv",
                            "period_start": "2025-01-01",
                            "period_end": "2025-12-31",
                        },
                    ],
                },
            ]
        },
    }


def test_run_sobre_fixture_valido_escribe_map_client_data_y_devuelve_flow_result(
    tmp_path: Path,
) -> None:
    """Caso 1 (CA-01): run(ctx) sobre el fixture valido escribe
    map_client_data.json en ctx.outputs_dir / "020_onboarding/map_client_data.json"
    y devuelve FlowResult(success=True, outputs=[esa ruta]); el archivo existe
    en disco."""
    clients_root = tmp_path / "clients"
    create_client("ABC", clients_root)
    ctx = ClientContext("ABC", clients_root)

    contrato_path = ctx.outputs_dir / "010_discovery/contract_data.json"
    contrato_path.parent.mkdir(parents=True)
    import json

    contrato_path.write_text(
        json.dumps(_contrato_valido(), ensure_ascii=False), encoding="utf-8"
    )

    flow = Onboarding()
    result = flow.run(ctx)

    ruta_esperada = ctx.outputs_dir / "020_onboarding/map_client_data.json"

    assert isinstance(result, FlowResult)
    assert result.success is True
    assert result.outputs == [ruta_esperada]
    assert ruta_esperada.exists()
