from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.h2_relationship_service import (
    find_trial_by_experiment,
)
from backend.services.h2_timeseries_service import (
    build_timeseries_pair,
)


h2_timeseries_bp: Blueprint = Blueprint(
    "h2_timeseries",
    __name__,
)


# Uso:
# /api/h2/timeseries-pair
# ?participant=1
# &experiment=5
# &channel_a=Fp1
# &channel_b=GSR1
@h2_timeseries_bp.route(
    "/timeseries-pair",
    methods=["GET"],
)
def get_h2_timeseries_pair() -> tuple[Any, int]:
    """
    Devuelve dos señales sincronizadas durante During.

    La consulta usa:
    - participant
    - experiment
    - channel_a
    - channel_b

    Internamente se resuelve el trial correspondiente.
    """
    participant_arg: str | None = request.args.get("participant")
    experiment_arg: str | None = request.args.get("experiment")
    channel_a: str | None = request.args.get("channel_a")
    channel_b: str | None = request.args.get("channel_b")

    if (
        participant_arg is None
        or experiment_arg is None
        or channel_a is None
        or channel_b is None
    ):
        return jsonify(
            {
                "error": (
                    "Parámetros requeridos: "
                    "participant, experiment, channel_a y channel_b."
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

        data: dict[str, Any] = build_timeseries_pair(
            participant_id=participant_id,
            trial=trial,
            channel_a=channel_a,
            channel_b=channel_b,
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
                    "Error interno al cargar "
                    f"timeseries pair H2: {error}"
                )
            }
        ), 500