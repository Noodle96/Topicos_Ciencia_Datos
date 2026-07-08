from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.husformer_trial_service import (
    load_husformer_trial_projection,
)


husformer_trial_bp: Blueprint = Blueprint(
    "husformer_trial",
    __name__,
)


@husformer_trial_bp.route("/trial-projection", methods=["GET"])
def get_husformer_trial_projection() -> Any:
    """
    Uso:
    /api/husformer/trial-projection?method=pca

    Retorna los puntos 2D de la Vista A (sub-panel A1) -- uno por trial,
    a partir de last_hs de Husformer agregado por mean-pooling y proyectado
    con:
    - pca
    - umap
    - tsne
    """
    method: str = request.args.get("method", "pca")

    try:
        data: dict[str, Any] = load_husformer_trial_projection(
            method=method,
        )

        return jsonify(data)

    except Exception as error:
        return jsonify({"error": str(error)}), 400
