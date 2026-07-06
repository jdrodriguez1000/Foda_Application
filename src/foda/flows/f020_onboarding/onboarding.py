"""Flujo 020: Onboarding (feature onboarding, banda tracer_bullet).

Fuente: 600_features/onboarding/tracer_bullet/spec.md (DS-ONB-1..5) y plan.md
(TSK-01..TSK-09). Bucle TDD en curso: casos 1-10 cerrados (derivacion de
hierarchies.product y hierarchies.geography -levels/depth/unique_values/
unique_counts-, de datasets -kind/source_medium/periodicity/file_count/
files/fields, en el orden del contrato; maps_to se toma tal cual del
contrato- y de totals -dataset_count/file_count, derivados de una variable
local `datasets` compartida con la seccion "datasets", sin mutacion
posterior del mapa-); casos 11-15 cerrados como verde directo (profundidad
variable de niveles, determinismo de la serializacion -TSK-06- y ausencia
de artefactos parciales, ya cubiertos por el diseno existente); casos 16
(CA-14), 17 (CA-15, TSK-07), 18 (CA-16, TSK-07) y 19 (CA-17, TSK-07)
cerrados: validate() delega en el helper _validate_hierarchy(name, hierarchy)
-mismo patron que _hierarchy/_dataset en execute()- que exige levels no
vacios en product_hierarchy/geography y que las claves de cada miembro
coincidan exactamente con levels (ni falten ni sobren); ademas, validate()
acumula un dict {product_hierarchy, geography} con las jerarquias ya
validadas y lo pasa al helper _validate_maps_to(hierarchies, historical_data),
que exige que cada field.maps_to con dominio "product."/"geography."
referencie un <level> existente en la jerarquia correspondiente
(maps_to=None/"time"/"measure" siguen siendo validos), y a _validate_enums
(historical_data), que exige que field.type/kind/source_medium/periodicity
de cada dataset pertenezcan a su vocabulario cerrado (spec.md, Contratos de
Datos) delegando en el helper _check_enum(label, value, allowed) para las
4 comprobaciones identicas en forma (valor no en el set permitido -> mismo
mensaje de FlowContractError). El resto de reglas de contenido (CA-18,
CA-19: fechas, name duplicado) queda para casos posteriores del bucle.
"""

import json

from foda.core.context import ClientContext
from foda.core.flow import Artifact, Flow, FlowContractError, FlowResult

# DS-ONB-5: requires/produces declarados; no se amplia ClientContext.
_REQUIRES = [
    Artifact(
        name="contract_data",
        base="outputs",
        relative="010_discovery/contract_data.json",
    )
]
_PRODUCES = [
    Artifact(
        name="map_client_data",
        base="outputs",
        relative="020_onboarding/map_client_data.json",
    )
]


def _hierarchy(levels: list[str], members: list[dict[str, str]]) -> dict[str, object]:
    """DS-ONB-5/DS-ONB-3: construye el bloque {levels, depth, unique_values,
    unique_counts} comun a las jerarquias (product, geography); depth se
    deriva siempre de la cantidad de niveles. Por cada nivel, unique_values
    reporta los valores distintos observados en members en orden alfabetico
    ascendente y unique_counts su conteo."""
    unique_values = {
        level: sorted({member[level] for member in members}) for level in levels
    }
    unique_counts = {level: len(values) for level, values in unique_values.items()}
    return {
        "levels": levels,
        "depth": len(levels),
        "unique_values": unique_values,
        "unique_counts": unique_counts,
    }


def _validate_hierarchy(name: str, hierarchy: dict) -> None:
    """DS-ONB-1 (TSK-07): valida el contenido de una jerarquia
    (product_hierarchy o geography) ya cargada. Levels no vacios (CA-14) y
    claves de cada miembro coincidentes exactamente con levels -ni falten ni
    sobren- (CA-15). Lanza FlowContractError con el mismo mensaje que antes
    de este refactor; el resto de reglas de contenido (CA-16..CA-19) queda
    para casos posteriores del bucle."""
    levels = hierarchy.get("levels", [])
    if not levels:
        raise FlowContractError(f"{name}.levels no puede estar vacio.")
    for member in hierarchy.get("members", []):
        if set(member.keys()) != set(levels):
            raise FlowContractError(
                f"{name}: un miembro tiene claves {sorted(member.keys())} "
                f"que no coinciden con levels {sorted(levels)}."
            )


def _validate_maps_to(hierarchies: dict[str, dict], historical_data: dict) -> None:
    """DS-ONB-1 (TSK-07): valida que cada field.maps_to de historical_data.datasets
    sea uno de los valores permitidos por el contrato (null, "time", "measure",
    "product.<level>", "geography.<level>") y que, para "product."/"geography.",
    <level> exista en los levels de la jerarquia correspondiente (CA-16)."""
    domains = {"product": "product_hierarchy", "geography": "geography"}
    for dataset in historical_data.get("datasets", []):
        for field in dataset.get("fields", []):
            maps_to = field.get("maps_to")
            if maps_to in (None, "time", "measure"):
                continue
            domain, _, level = maps_to.partition(".")
            hierarchy_name = domains.get(domain)
            levels = hierarchies.get(hierarchy_name, {}).get("levels", []) if hierarchy_name else []
            if hierarchy_name is None or level not in levels:
                raise FlowContractError(
                    f"field.maps_to '{maps_to}' no es valido: el nivel no existe "
                    "en la jerarquia referenciada."
                )


_FIELD_TYPES = {"string", "integer", "number", "date", "boolean"}
_KINDS = {
    "ventas",
    "inventario",
    "ordenes_compra",
    "devoluciones",
    "promociones",
    "precios",
}
_SOURCE_MEDIUMS = {"csv", "xlsx", "database", "api"}
_PERIODICITIES = {
    "diaria",
    "semanal",
    "quincenal",
    "mensual",
    "trimestral",
    "semestral",
    "anual",
}


def _check_enum(label: str, value: object, allowed: set[str]) -> None:
    """Lanza FlowContractError si value no pertenece al vocabulario cerrado
    allowed, con un mensaje uniforme que identifica el campo (label) y el
    valor recibido."""
    if value not in allowed:
        raise FlowContractError(f"{label} '{value}' no pertenece al vocabulario cerrado.")


def _validate_enums(historical_data: dict) -> None:
    """DS-ONB-1 (TSK-07, CA-17): valida que field.type, kind, source_medium y
    periodicity de cada dataset pertenezcan a su vocabulario cerrado (spec.md,
    Contratos de Datos -> Vocabularios cerrados)."""
    for dataset in historical_data.get("datasets", []):
        _check_enum("kind", dataset.get("kind"), _KINDS)
        _check_enum("source_medium", dataset.get("source_medium"), _SOURCE_MEDIUMS)
        _check_enum("periodicity", dataset.get("periodicity"), _PERIODICITIES)
        for field in dataset.get("fields", []):
            _check_enum("field.type", field.get("type"), _FIELD_TYPES)


def _dataset(dataset: dict) -> dict[str, object]:
    """DS-ONB-5: construye el bloque {kind, source_medium, periodicity,
    file_count, files, fields} de un dataset. file_count es la cantidad de
    archivos y cada files[*] refleja name/period_start/period_end del archivo
    fuente; cada fields[*] refleja name/type/required/maps_to de la columna,
    en el orden del contrato (maps_to se toma tal cual del contrato, incl.
    null para columnas no mapeadas como precio_unitario)."""
    files = dataset.get("files", [])
    fields = dataset.get("fields", [])
    files_out = [
        {
            "name": file_.get("name"),
            "period_start": file_.get("period_start"),
            "period_end": file_.get("period_end"),
        }
        for file_ in files
    ]
    fields_out = [
        {
            "name": field.get("name"),
            "type": field.get("type"),
            "required": field.get("required"),
            "maps_to": field.get("maps_to"),
        }
        for field in fields
    ]
    return {
        "kind": dataset.get("kind"),
        "source_medium": dataset.get("source_medium"),
        "periodicity": dataset.get("periodicity"),
        "file_count": len(files),
        "files": files_out,
        "fields": fields_out,
    }


class Onboarding(Flow):
    """Flujo 020: deriva map_client_data.json desde contract_data.json
    (determinista). Caso 1 (CA-01): happy path minimo end-to-end; el mapa
    completo (jerarquias/datasets/totals) se agrega en casos posteriores."""

    name = "onboarding"
    requires = _REQUIRES
    produces = _PRODUCES

    def __init__(self) -> None:
        self._contract: dict | None = None
        self._mapa: dict | None = None

    def load_inputs(self, ctx: ClientContext) -> None:
        """DS-ONB-5: lee y parsea contract_data.json a estado de instancia solo
        si el archivo existe; si no existe, deja el estado sin cargar para que
        validate() (base) lo detecte."""
        path = self.requires[0].path(ctx)
        if path.exists():
            self._contract = json.loads(path.read_text(encoding="utf-8"))

    def validate(self, ctx: ClientContext) -> None:
        """Fase 2a (DS-ONB-5): existencia base del require. Fase 2b (DS-ONB-1,
        TSK-07, en curso): coherencia de contenido del contrato ya cargado;
        por ahora levels no vacios (CA-14), claves de miembro coincidentes
        con levels (CA-15), field.maps_to a nivel existente (CA-16) y enums
        de field.type/kind/source_medium/periodicity dentro de su vocabulario
        cerrado (CA-17). Resto de reglas de contenido (CA-18..CA-19) quedan
        para casos posteriores del bucle."""
        super().validate(ctx)
        contract = self._contract or {}
        hierarchies: dict[str, dict] = {}
        for hierarchy_name in ("product_hierarchy", "geography"):
            hierarchy = contract.get(hierarchy_name, {})
            _validate_hierarchy(hierarchy_name, hierarchy)
            hierarchies[hierarchy_name] = hierarchy
        historical_data = contract.get("historical_data", {})
        _validate_maps_to(hierarchies, historical_data)
        _validate_enums(historical_data)

    def execute(self, ctx: ClientContext) -> FlowResult:
        """Deriva en memoria el mapa canonico (identidad del cliente +
        jerarquia de producto) y devuelve FlowResult(success=True,
        outputs=[ruta de produces[0]])."""
        contract = self._contract or {}
        product = contract.get("product_hierarchy", {})
        geography = contract.get("geography", {})
        historical_data = contract.get("historical_data", {})
        datasets = [
            _dataset(dataset) for dataset in historical_data.get("datasets", [])
        ]
        self._mapa = {
            "schema_version": contract.get("schema_version"),
            "client": contract.get("client"),
            "hierarchies": {
                "product": _hierarchy(
                    product.get("levels", []), product.get("members", [])
                ),
                "geography": _hierarchy(
                    geography.get("levels", []), geography.get("members", [])
                ),
            },
            "datasets": datasets,
            "totals": {
                "dataset_count": len(datasets),
                "file_count": sum(dataset["file_count"] for dataset in datasets),
            },
        }
        return FlowResult(success=True, outputs=[self.produces[0].path(ctx)])

    def write_outputs(self, ctx: ClientContext, result: FlowResult) -> None:
        """DS-ONB-5: crea la carpeta destino y escribe map_client_data.json."""
        path = self.produces[0].path(ctx)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self._mapa, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
