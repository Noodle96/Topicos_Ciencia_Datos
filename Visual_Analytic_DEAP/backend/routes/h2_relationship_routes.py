from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.h2_relationship_service import (
    build_relationship_matrix,
    find_trial_by_experiment,
)


h2_relationship_bp: Blueprint = Blueprint(
    "h2_relationship",
    __name__,
)


# Uso:
# /api/h2/relationships?participant=1&experiment=5
@h2_relationship_bp.route(
    "/relationships",
    methods=["GET"],
)
def get_h2_relationships() -> tuple[Any, int]:
    """
    Devuelve la matriz de relaciones EEG × periféricas para H2.

    La consulta principal usa:
    - participant
    - experiment

    Internamente se resuelve el trial correspondiente.
    """
    participant_arg: str | None = request.args.get("participant")
    experiment_arg: str | None = request.args.get("experiment")

    if participant_arg is None or experiment_arg is None:
        return jsonify(
            {
                "error": (
                    "Parámetros requeridos: "
                    "participant y experiment."
                )
            }
        ), 400

    try:
        participant_id: int = int(participant_arg)
        experiment_id: int = int(experiment_arg)

        trial: int = find_trial_by_experiment(
            participant_id=participant_id,
            experiment_id=experiment_id,
        )

        data: dict[str, Any] = build_relationship_matrix(
            participant_id=participant_id,
            trial=trial,
        )

        return jsonify(data), 200

    except FileNotFoundError as error:
        return jsonify({"error": str(error)}), 404

    except ValueError:
        return jsonify(
            {
                "error": (
                    "participant y experiment "
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