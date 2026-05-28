from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.h2_relationship_service import (
    build_cross_participant_relationship_matrix,
)


h2_relationship_bp: Blueprint = Blueprint(
    "h2_relationship",
    __name__,
)


# Uso:
# /api/h2/relationships
# ?experiment=5
# &row_group=EEG
# &reference_group=PERIPHERAL
# &reference_channel=GSR1
@h2_relationship_bp.route(
    "/relationships",
    methods=["GET"],
)
def get_h2_relationships() -> tuple[Any, int]:
    """
    Devuelve la matriz H2 de relaciones por participantes.

    Filas:
    - canales del grupo Y seleccionado.

    Columnas:
    - participantes S01...S32.

    Celda:
    - correlación entre el canal de la fila y el canal de referencia
      durante el experimento seleccionado.
    """
    experiment_arg: str | None = request.args.get("experiment")
    row_group: str | None = request.args.get("row_group")
    reference_group: str | None = request.args.get("reference_group")
    reference_channel: str | None = request.args.get("reference_channel")

    if (
        experiment_arg is None
        or row_group is None
        or reference_group is None
        or reference_channel is None
    ):
        return jsonify(
            {
                "error": (
                    "Parámetros requeridos: experiment, row_group, "
                    "reference_group y reference_channel."
                )
            }
        ), 400

    try:
        experiment_id: int = int(experiment_arg)

        data: dict[str, Any] = build_cross_participant_relationship_matrix(
            experiment_id=experiment_id,
            row_group=row_group,
            reference_group=reference_group,
            reference_channel=reference_channel,
        )

        return jsonify(data), 200

    except FileNotFoundError as error:
        return jsonify({"error": str(error)}), 404

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    except Exception as error:
        return jsonify(
            {
                "error": (
                    "Error interno al cargar matriz H2 por participantes: "
                    f"{error}"
                )
            }
        ), 500