from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.h2_relationship_service import (
    find_trial_by_experiment,
)
from backend.services.h2_local_relationship_service import (
    build_local_relationship,
)


h2_local_relationship_bp: Blueprint = Blueprint(
    "h2_local_relationship",
    __name__,
)


# Uso:
# /api/h2/local-relationship
# ?participant=1
# &experiment=5
# &eeg=Fp1
# &peripheral=GSR1
# &start_sec=10
# &end_sec=25
@h2_local_relationship_bp.route(
    "/local-relationship",
    methods=["GET"],
)
def get_h2_local_relationship() -> tuple[Any, int]:
    """
    Devuelve la correlación local EEG ↔ periférica dentro de una
    ventana temporal seleccionada durante During.

    La consulta usa participant + experiment.
    Internamente se resuelve el trial correspondiente.
    """
    participant_arg: str | None = request.args.get("participant")
    experiment_arg: str | None = request.args.get("experiment")
    eeg_channel: str | None = request.args.get("eeg")
    peripheral_channel: str | None = request.args.get("peripheral")
    start_sec_arg: str | None = request.args.get("start_sec")
    end_sec_arg: str | None = request.args.get("end_sec")

    if (
        participant_arg is None
        or experiment_arg is None
        or eeg_channel is None
        or peripheral_channel is None
        or start_sec_arg is None
        or end_sec_arg is None
    ):
        return jsonify(
            {
                "error": (
                    "Parámetros requeridos: participant, experiment, eeg, "
                    "peripheral, start_sec y end_sec."
                )
            }
        ), 400

    try:
        participant_id: int = int(participant_arg)
        experiment_id: int = int(experiment_arg)
        start_sec: float = float(start_sec_arg)
        end_sec: float = float(end_sec_arg)

        trial: int = find_trial_by_experiment(
            participant_id=participant_id,
            experiment_id=experiment_id,
        )

        data: dict[str, Any] = build_local_relationship(
            participant_id=participant_id,
            trial=trial,
            eeg_channel=eeg_channel,
            peripheral_channel=peripheral_channel,
            start_sec=start_sec,
            end_sec=end_sec,
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
                    "Error interno al calcular relación local H2: "
                    f"{error}"
                )
            }
        ), 500