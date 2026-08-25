from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.husformer_attention_service import (
    load_husformer_trial_attention,
    load_husformer_window_cross_attention,
    compute_trial_pattern_network,
    compute_selected_trials_cross_attention,
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


@husformer_attention_bp.route("/window-cross-attention", methods=["GET"])
def get_husformer_window_cross_attention() -> Any:
    """
    Uso:
    /api/husformer/window-cross-attention?participant_id=1&trial=1&window_index=10

    Retorna la matriz 5x5 cruda de atención cross-modal (attn_cross_summary)
    de UNA ventana puntual (Vista C, C1) -- ver husformer_attention_service.py
    para la diferencia con attn_final_summary (B1/B2).
    """
    participant_id_raw: str | None = request.args.get("participant_id")
    trial_raw: str | None = request.args.get("trial")
    window_index_raw: str | None = request.args.get("window_index")

    try:
        if participant_id_raw is None or trial_raw is None or window_index_raw is None:
            raise ValueError(
                "Faltan los parámetros 'participant_id', 'trial' y/o 'window_index'."
            )

        data: dict[str, Any] = load_husformer_window_cross_attention(
            participant_id=int(participant_id_raw),
            trial=int(trial_raw),
            window_index=int(window_index_raw),
        )

        return jsonify(data)

    except Exception as error:
        return jsonify({"error": str(error)}), 400


@husformer_attention_bp.route("/trial-pattern-network", methods=["GET"])
def get_husformer_trial_pattern_network() -> Any:
    """
    Uso:
    /api/husformer/trial-pattern-network

    Retorna el mapa de patrones de fusión cross-modal entre los 1280 trials
    (Vista A, A3 rediseñada -- reemplaza el panel de perfil de
    cuestionario): un nodo por trial (con su valencia y distancia al punto
    neutro) + aristas hacia sus vecinos más parecidos en firma de atención
    cross-modal. Sin parámetros -- es un mapa del dataset completo, no de un
    trial puntual. Ver husformer_attention_service.py (compute_trial_
    pattern_network) para la justificación completa.
    """
    try:
        data: dict[str, Any] = compute_trial_pattern_network()
        return jsonify(data)

    except Exception as error:
        return jsonify({"error": str(error)}), 400


@husformer_attention_bp.route("/selected-trials-cross-attention", methods=["GET"])
def get_husformer_selected_trials_cross_attention() -> Any:
    """
    Uso:
    /api/husformer/selected-trials-cross-attention?trials=1_5,2_10,7_3

    Cada elemento de 'trials' es "participant_id_trial" (separados por
    guión bajo), la lista completa separada por comas.

    Retorna la matriz 5x5 promedio de atención cross-modal de cada trial en
    la lista (Vista C, C1 rediseñada -- Small Multiples, uno por trial
    seleccionado en A1/A2). Sin parámetro 'trials' o vacío, retorna la lista
    vacía (mismo estado que "nada seleccionado todavía"). Ver
    husformer_attention_service.py (compute_selected_trials_cross_attention)
    para la justificación completa.
    """
    trials_raw: str | None = request.args.get("trials")

    try:
        trial_keys: list[tuple[int, int]] = []

        if trials_raw:
            for pair_str in trials_raw.split(","):
                participant_str, trial_str = pair_str.split("_")
                trial_keys.append((int(participant_str), int(trial_str)))

        data: dict[str, Any] = compute_selected_trials_cross_attention(trial_keys)
        return jsonify(data)

    except Exception as error:
        return jsonify({"error": str(error)}), 400
