from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.h2_relationship_service import (
    build_relationship_matrix,
)


h2_relationship_bp: Blueprint = Blueprint(
    "h2_relationship",
    __name__,
)


# Uso:
# /api/h2/relationships?participant=1&trial=1
@h2_relationship_bp.route(
    "/relationships",
    methods=["GET"],
)
def get_h2_relationships() -> tuple[Any, int]:
    """
    Devuelve la matriz de relaciones EEG × periféricas
    para un participante y trial.
    """
    participant_arg: str | None = request.args.get(
        "participant"
    )

    trial_arg: str | None = request.args.get(
        "trial"
    )

    if participant_arg is None or trial_arg is None:
        return jsonify(
            {
                "error": (
                    "Parámetros requeridos: "
                    "participant y trial."
                )
            }
        ), 400

    try:
        participant_id: int = int(participant_arg)
        trial: int = int(trial_arg)

        data: dict[str, Any] = build_relationship_matrix(
            participant_id=participant_id,
            trial=trial,
        )

        return jsonify(data), 200

    except FileNotFoundError as error:
        return jsonify(
            {
                "error": str(error)
            }
        ), 404

    except ValueError:
        return jsonify(
            {
                "error": (
                    "participant y trial "
                    "deben ser enteros."
                )
            }
        ), 400

    except Exception as error:
        return jsonify(
            {
                "error": (
                    "Error interno al cargar "
                    f"relaciones H2: {error}"
                )
            }
        ), 500