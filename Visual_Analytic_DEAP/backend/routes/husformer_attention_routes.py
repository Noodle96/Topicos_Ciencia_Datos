from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.husformer_attention_service import (
    load_husformer_trial_attention,
)


husformer_attention_bp: Blueprint = Blueprint(
    "husformer_attention",
    __name__,
)


@husformer_attention_bp.route("/trial-attention", methods=["GET"])
def get_husformer_trial_attention() -> Any:
    """
    Uso:
    /api/husformer/trial-attention?participant_id=1&trial=1

    Retorna la serie temporal de dominancia de modalidad (Vista B, B1/B2)
    para el trial dado: un vector de 5 pesos (uno por modalidad) por
    ventana de 1s, promediando attn_final_summary sobre el eje query (ver
    husformer_attention_service.py para la justificación de la reducción).
    """
    participant_id_raw: str | None = request.args.get("participant_id")
    trial_raw: str | None = request.args.get("trial")

    try:
        if participant_id_raw is None or trial_raw is None:
            raise ValueError("Faltan los parámetros 'participant_id' y/o 'trial'.")

        data: dict[str, Any] = load_husformer_trial_attention(
            participant_id=int(participant_id_raw),
            trial=int(trial_raw),
        )

        return jsonify(data)

    except Exception as error:
        return jsonify({"error": str(error)}), 400
