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
# &eeg=Fp1
# &peripheral=GSR1
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
    - eeg
    - peripheral

    Internamente se resuelve el trial correspondiente.
    """
    participant_arg: str | None = request.args.get("participant")
    experiment_arg: str | None = request.args.get("experiment")
    eeg_channel: str | None = request.args.get("eeg")
    peripheral_channel: str | None = request.args.get("peripheral")

    if (
        participant_arg is None
        or experiment_arg is None
        or eeg_channel is None
        or peripheral_channel is None
    ):
        return jsonify(
            {
                "error": (
                    "Parámetros requeridos: "
                    "participant, experiment, eeg, peripheral."
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
            eeg_channel=eeg_channel,
            peripheral_channel=peripheral_channel,
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