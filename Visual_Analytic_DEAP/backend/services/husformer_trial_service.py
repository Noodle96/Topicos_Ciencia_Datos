"""
Service de la Vista A (Espacio de Representaciones Fusionadas, A1/A2/A3).

Lee las salidas de `backend/scripts/husformer/generate_trial_projections.py`
(trial_metadata.csv + projections/{method}_2d.csv) -- last_hs de Husformer
agregado por trial vía mean-pooling, proyectado en 2D. Pipeline
DELIBERADAMENTE separado del de Tarea1 (ver tarea1_service.py), aunque el
formato de salida al frontend es análogo a propósito, para poder reutilizar
el mismo patrón de render del chart D3 en ambos casos.

Clustering de A2 (agregado 2026-07-15): a diferencia de las proyecciones
PCA/UMAP/t-SNE (precomputadas offline por generate_trial_projections.py),
el clustering se calcula AL VUELO en cada request -- KMeans/HDBSCAN sobre
1280x40 floats es prácticamente instantáneo (muy por debajo del umbral de
responsividad de 50-100ms citado en el resumen del Cap. 5 de Aigner), y
calcularlo en vivo permite que el usuario explore distintos k/min_cluster_size
sin depender de un script offline. Decisión confirmada con Russell
(2026-07-15), ver estado_proyecto.md.

Clustering corre sobre `trial_last_hs_standardized.npy` (el vector de 40-dim
YA estandarizado, el mismo insumo que se proyecta a 2D para A1), NUNCA sobre
las coordenadas 2D ya proyectadas -- razón: PCA/UMAP/t-SNE son transformaciones
lossy (UMAP/t-SNE en particular solo preservan vecindad local, no distancias
reales, ver Cap. 13 de Munzner), así que clusterizar sobre la proyección 2D
haría que el resultado cambiara según qué método esté activo en A1, aunque el
trial sea exactamente el mismo. Clusterizando sobre el vector de 40-dim, la
etiqueta de cluster de cada trial es estable sin importar qué proyección esté
mostrando A1/A2 -- solo cambia la posición del punto, no su color.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import HDBSCAN, KMeans

from backend.utils.paths import DATASET_DIR


REPRESENTATIONS_DIR: Path = (
    DATASET_DIR
    / "processed"
    / "representations"
    / "husformer"
)

PROJECTIONS_DIR: Path = REPRESENTATIONS_DIR / "projections"

TRIAL_LAST_HS_STANDARDIZED_PATH: Path = REPRESENTATIONS_DIR / "trial_last_hs_standardized.npy"
TRIAL_METADATA_PATH: Path = REPRESENTATIONS_DIR / "trial_metadata.csv"

VALID_PROJECTION_METHODS: set[str] = {
    "pca",
    "umap",
    "tsne",
}

VALID_CLUSTER_METHODS: set[str] = {
    "kmeans",
    "hdbscan",
}

# Presets fijos, no un slider libre -- decisión de diseño confirmada con
# Russell (2026-07-15): "specification by selection" (Cap. 5 de Aigner,
# Tominski 2011) en vez de exponer un parámetro crudo sin curar. Validados
# también acá en el backend, no solo restringidos en el frontend, para que
# el endpoint nunca quede en un estado inconsistente con el diseño acordado.
VALID_KMEANS_K: set[int] = {3, 4, 6, 12}
VALID_HDBSCAN_MIN_CLUSTER_SIZE: set[int] = {5, 10, 20, 50}

# Semilla fija solo para reproducibilidad de KMeans (init aleatoria) -- NO
# relacionada con la semilla 97 del split participante/train-valid-test.
KMEANS_RANDOM_STATE: int = 42


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


def _validate_cluster_method(method: str) -> str:
    """Valida el método de clustering solicitado (kmeans o hdbscan)."""
    normalized_method: str = method.strip().lower()

    if normalized_method not in VALID_CLUSTER_METHODS:
        raise ValueError(
            f"Método de clustering inválido: {method}. "
            f"Métodos válidos: {sorted(VALID_CLUSTER_METHODS)}"
        )

    return normalized_method


def _validate_cluster_param(method: str, param_value: int) -> int:
    """
    Valida que param_value sea uno de los presets fijos para el método dado.

    KMeans: param_value es k (número de clusters), uno de VALID_KMEANS_K.
    HDBSCAN: param_value es min_cluster_size, uno de VALID_HDBSCAN_MIN_CLUSTER_SIZE.
    """
    if method == "kmeans":
        if param_value not in VALID_KMEANS_K:
            raise ValueError(
                f"k inválido para KMeans: {param_value}. "
                f"Valores válidos: {sorted(VALID_KMEANS_K)}"
            )
    else:  # hdbscan
        if param_value not in VALID_HDBSCAN_MIN_CLUSTER_SIZE:
            raise ValueError(
                f"min_cluster_size inválido para HDBSCAN: {param_value}. "
                f"Valores válidos: {sorted(VALID_HDBSCAN_MIN_CLUSTER_SIZE)}"
            )

    return param_value


def _load_trial_last_hs_standardized() -> tuple[np.ndarray, pd.DataFrame]:
    """
    Carga el vector de 40-dim estandarizado por trial + su metadata de
    contexto (participant_id, trial), alineados fila a fila -- ambos son
    generados juntos, en el mismo orden, por generate_trial_projections.py
    (aggregate_by_trial), así que no hace falta un merge explícito, solo
    verificar que las longitudes coincidan (defensivo).
    """
    if not TRIAL_LAST_HS_STANDARDIZED_PATH.exists() or not TRIAL_METADATA_PATH.exists():
        raise FileNotFoundError(
            f"Faltan los insumos de clustering: {TRIAL_LAST_HS_STANDARDIZED_PATH} "
            f"y/o {TRIAL_METADATA_PATH}. "
            "Ejecuta backend/scripts/husformer/generate_trial_projections.py primero."
        )

    trial_last_hs_standardized: np.ndarray = np.load(TRIAL_LAST_HS_STANDARDIZED_PATH)
    trial_metadata: pd.DataFrame = pd.read_csv(TRIAL_METADATA_PATH)

    if len(trial_last_hs_standardized) != len(trial_metadata):
        raise ValueError(
            "Desajuste entre trial_last_hs_standardized.npy "
            f"({len(trial_last_hs_standardized)} filas) y trial_metadata.csv "
            f"({len(trial_metadata)} filas) -- probablemente vienen de corridas "
            "distintas de generate_trial_projections.py. Regenerar ambos juntos."
        )

    return trial_last_hs_standardized, trial_metadata


def _run_kmeans(features: np.ndarray, k: int) -> np.ndarray:
    """Corre KMeans sobre el vector de 40-dim estandarizado. Sin ruido: todo punto cae en 0..k-1."""
    model: KMeans = KMeans(n_clusters=k, random_state=KMEANS_RANDOM_STATE, n_init="auto")
    return model.fit_predict(features)


def _run_hdbscan(features: np.ndarray, min_cluster_size: int) -> np.ndarray:
    """Corre HDBSCAN sobre el vector de 40-dim estandarizado. Ruido: label -1."""
    model: HDBSCAN = HDBSCAN(min_cluster_size=min_cluster_size)
    return model.fit_predict(features)


def load_husformer_trial_clusters(method: str, param_value: int) -> dict[str, Any]:
    """
    Calcula clustering AL VUELO (no precomputado) sobre el vector de 40-dim
    estandarizado por trial (Vista A, A2), y devuelve una etiqueta de cluster
    por trial.

    method: "kmeans" (param_value = k) o "hdbscan" (param_value = min_cluster_size).
    Ambos parámetros están restringidos a los presets fijos definidos en
    VALID_KMEANS_K / VALID_HDBSCAN_MIN_CLUSTER_SIZE (ver docstring del módulo).
    """
    valid_method: str = _validate_cluster_method(method)
    valid_param: int = _validate_cluster_param(valid_method, param_value)

    features, trial_metadata = _load_trial_last_hs_standardized()

    if valid_method == "kmeans":
        labels: np.ndarray = _run_kmeans(features, k=valid_param)
        param_name: str = "k"
        has_noise: bool = False
    else:
        labels = _run_hdbscan(features, min_cluster_size=valid_param)
        param_name = "min_cluster_size"
        has_noise = True

    non_noise_labels: set[int] = {int(label) for label in labels if label != -1}
    num_clusters: int = len(non_noise_labels)

    points: list[dict[str, Any]] = [
        {
            "Participant_id": int(row["participant_id"]),
            "Trial": int(row["trial"]),
            "cluster": int(label),
        }
        for (_, row), label in zip(trial_metadata.iterrows(), labels)
    ]

    return {
        "method": valid_method,
        "param_name": param_name,
        "param_value": valid_param,
        "num_clusters": num_clusters,
        "has_noise": has_noise,
        "num_points": len(points),
        "points": points,
    }
