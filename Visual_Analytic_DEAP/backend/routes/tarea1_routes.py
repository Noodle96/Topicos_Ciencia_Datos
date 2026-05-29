from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.tarea1_service import (
    load_tarea1_projection,
    load_tarea1_trial_signals,
)


tarea1_bp: Blueprint = Blueprint(
    "tarea1",
    __name__,
)


@tarea1_bp.route("/projection", methods=["GET"])
def get_tarea1_projection() -> Any:
    """
    Uso:
    /api/tarea1/projection?method=pca

    Retorna los puntos 2D de la proyección seleccionada:
    - pca
    - umap
    - tsne
    """
    method: str = request.args.get("method", "pca")

    try:
        data: dict[str, Any] = load_tarea1_projection(
            method=method,
        )

        return jsonify(data)

    except Exception as error:
        return jsonify({"error": str(error)}), 400


@tarea1_bp.route("/trial-signals", methods=["GET"])
def get_tarea1_trial_signals() -> Any:
    """
    Uso:
    /api/tarea1/trial-signals?participant=1&trial=2&channels=Fp1,F3,GSR1

    Retorna señales During-only del trial seleccionado.
    """
    try:
        participant: int = int(request.args.get("participant", "1"))
        trial: int = int(request.args.get("trial", "1"))

        channels_text: str = request.args.get("channels", "")

        channels: list[str] | None = (
            [
                channel.strip()
                for channel in channels_text.split(",")
                if channel.strip()
            ]
            if channels_text
            else None
        )

        data: dict[str, Any] = load_tarea1_trial_signals(
            participant=participant,
            trial=trial,
            channels=channels,
        )

        return jsonify(data)

    except Exception as error:
        return jsonify({"error": str(error)}), 400