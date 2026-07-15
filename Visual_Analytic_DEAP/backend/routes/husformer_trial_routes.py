from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.husformer_trial_service import (
    load_husformer_trial_clusters,
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


@husformer_trial_bp.route("/trial-clusters", methods=["GET"])
def get_husformer_trial_clusters() -> Any:
    """
    Uso:
    /api/husformer/trial-clusters?method=kmeans&param_value=6
    /api/husformer/trial-clusters?method=hdbscan&param_value=10

    Retorna la etiqueta de cluster por trial (Vista A, sub-panel A2),
    calculada AL VUELO (no precomputada) sobre el vector de 40-dim
    estandarizado de last_hs -- no sobre las coordenadas 2D proyectadas.

    method=kmeans -> param_value es k, uno de {3, 4, 6, 12}.
    method=hdbscan -> param_value es min_cluster_size, uno de {5, 10, 20, 50}.
    Ambos son presets fijos (no un valor libre), validados también en el
    service.
    """
    method: str = request.args.get("method", "kmeans")
    param_value_raw: str | None = request.args.get("param_value")

    try:
        if param_value_raw is None:
            raise ValueError("Falta el parámetro 'param_value' (k para kmeans, min_cluster_size para hdbscan).")

        param_value: int = int(param_value_raw)

        data: dict[str, Any] = load_husformer_trial_clusters(
            method=method,
            param_value=param_value,
        )

        return jsonify(data)

    except Exception as error:
        return jsonify({"error": str(error)}), 400
