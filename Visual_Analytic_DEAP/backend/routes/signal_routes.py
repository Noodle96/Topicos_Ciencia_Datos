from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.signal_service import load_trial_signals

signal_blueprint: Blueprint = Blueprint("signals", __name__)


# Uso: GET http://127.0.0.1:5000/api/trial-signals?participant=1&trial=5&channels=Fp1,Fp2,F3,F4,GSR1,Resp
@signal_blueprint.route("/api/trial-signals", methods=["GET"])
def trial_signals() -> Any:
    """
    Devuelve señales reales del .bdf para un trial específico.
    """

    participant: int = int(request.args.get("participant", "1"))
    trial: int = int(request.args.get("trial", "1"))

    channels_arg: str = request.args.get(
        "channels",
        "Fp1,Fp2,F3,F4,GSR1,Resp",
    )

    channels: list[str] = [
        channel.strip() for channel in channels_arg.split(",") if channel.strip()
    ]

    try:
        result = load_trial_signals(
            participant=participant,
            trial=trial,
            channels=channels,
        )

        return jsonify(result)

    except Exception as error:
        print(
            f"[ERROR /api/trial-signals] "
            f"{type(error).__name__}: {error}"
        )

        return (
            jsonify(
                {
                    "error_type": type(error).__name__,
                    "error": str(error),
                }
            ),
            400,
        )
