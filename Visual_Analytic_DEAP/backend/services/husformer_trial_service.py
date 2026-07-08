"""
Service de la Vista A (Espacio de Representaciones Fusionadas, A1/A2/A3).

Lee las salidas de `backend/scripts/husformer/generate_trial_projections.py`
(trial_metadata.csv + projections/{method}_2d.csv) -- last_hs de Husformer
agregado por trial vía mean-pooling, proyectado en 2D. Pipeline
DELIBERADAMENTE separado del de Tarea1 (ver tarea1_service.py), aunque el
formato de salida al frontend es análogo a propósito, para poder reutilizar
el mismo patrón de render del chart D3 en ambos casos.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from backend.utils.paths import DATASET_DIR


REPRESENTATIONS_DIR: Path = (
    DATASET_DIR
    / "processed"
    / "representations"
    / "husformer"
)

PROJECTIONS_DIR: Path = REPRESENTATIONS_DIR / "projections"

VALID_PROJECTION_METHODS: set[str] = {
    "pca",
    "umap",
    "tsne",
}


def _validate_projection_method(method: str) -> str:
    """
    Valida el método de proyección solicitado.

    Métodos disponibles (mismo contrato que Tarea1):
    - pca
    - umap
    - tsne
    """
    normalized_method: str = method.strip().lower()

    if normalized_method not in VALID_PROJECTION_METHODS:
        raise ValueError(
            f"Método de proyección inválido: {method}. "
            f"Métodos válidos: {sorted(VALID_PROJECTION_METHODS)}"
        )

    return normalized_method


def _build_projection_path(method: str) -> Path:
    """Construye la ruta del CSV de proyección 2D trial-level de last_hs."""
    valid_method: str = _validate_projection_method(method)
    return PROJECTIONS_DIR / f"{valid_method}_2d.csv"


def _to_frontend_point(row: pd.Series) -> dict[str, Any]:
    """
    Convierte una fila de projections/{method}_2d.csv al formato esperado
    por el frontend para A1.

    Nombres análogos a los de Tarea1 (`_to_frontend_point` en
    tarea1_service.py) para reutilizar el mismo patrón de render en el
    chart D3, aunque el dato de origen es last_hs de Husformer (agregado
    por trial), no las features manuales.
    """
    return {
        "Participant_id": int(row["participant_id"]),
        "Participant_label": f"S{int(row['participant_id']):02d}",
        "Trial": int(row["trial"]),
        "Split": str(row["split"]),
        "Valence": None if pd.isna(row.get("valence")) else float(row["valence"]),
        "Arousal": None if pd.isna(row.get("arousal")) else float(row["arousal"]),
        "Dominance": None if pd.isna(row.get("dominance")) else float(row["dominance"]),
        "Liking": None if pd.isna(row.get("liking")) else float(row["liking"]),
        "NumWindowsAggregated": int(row["n_windows_aggregated"]),
        "projection_method": str(row["projection_method"]),
        "x": float(row["x"]),
        "y": float(row["y"]),
    }


def load_husformer_trial_projection(method: str) -> dict[str, Any]:
    """
    Carga los puntos 2D de la proyección trial-level de last_hs (Vista A, A1).

    Cada punto representa un trial completo (mean-pooling de las ~60
    ventanas de 1s de ese trial -- ver generate_trial_projections.py), no
    una ventana individual como en Vista B/C.
    """
    projection_path: Path = _build_projection_path(method)

    if not projection_path.exists():
        raise FileNotFoundError(
            f"No existe la proyección: {projection_path}. "
            "Ejecuta backend/scripts/husformer/generate_trial_projections.py primero."
        )

    projection_df: pd.DataFrame = pd.read_csv(projection_path)

    projection_df = projection_df.astype(object).where(
        pd.notnull(projection_df),
        None,
    )

    points: list[dict[str, Any]] = [
        _to_frontend_point(row)
        for _, row in projection_df.iterrows()
    ]

    return {
        "method": _validate_projection_method(method),
        "num_points": len(points),
        "points": points,
    }
