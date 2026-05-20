from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.emotion_service import load_emotion_space_points

emotion_blueprint: Blueprint = Blueprint("emotion", __name__)


# Uso: GET http://127.0.0.1:5000/api/emotion-space?x=Valence&y=Arousal&participant=all&trial=all
@emotion_blueprint.route("/api/emotion-space", methods=["GET"])
def emotion_space() -> Any:
    """
    Devuelve los puntos del espacio emocional para construir
    el scatter plot interactivo del frontend.
    """

    x_variable: str = request.args.get("x", "Valence")
    y_variable: str = request.args.get("y", "Arousal")
    participant: str = request.args.get("participant", "all")
    experiment: str = request.args.get("experiment", "all")

    try:
        points = load_emotion_space_points(
            x_variable=x_variable,
            y_variable=y_variable,
            participant=participant,
            experiment=experiment,
        )

        return jsonify(
            {
                "x_variable": x_variable,
                "y_variable": y_variable,
                "participant": participant,
                "points": points,
                "experiment": experiment,
            }
        )

    except ValueError as error:
        return jsonify({"error": str(error)}), 400
