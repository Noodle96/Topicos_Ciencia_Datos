from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.utils.paths import DATASET_DIR


FEATURE_DIR: Path = (
    DATASET_DIR
    / "processed"
    / "representations"
    / "manual_deap_features"
)

PROJECTIONS_DIR: Path = FEATURE_DIR / "projections"

REPRESENTATION_INPUTS_DIR: Path = (
    DATASET_DIR
    / "processed"
    / "representation_inputs"
)

VALID_PROJECTION_METHODS: set[str] = {
    "pca",
    "umap",
    "tsne",
}


DEFAULT_CHANNELS: list[str] = [
    "Fp1",
    "F3",
    "C3",
    "P3",
    "O1",
    "F4",
    "C4",
    "P4",
    "O2",
    "GSR1",
    "Resp",
    "Plet",
    "Temp",
]


def _validate_projection_method(method: str) -> str:
    """
    Valida el método de proyección solicitado.

    Métodos disponibles:
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
    """Construye la ruta del CSV de proyección 2D."""
    valid_method: str = _validate_projection_method(method)
    return PROJECTIONS_DIR / f"{valid_method}_2d.csv"


def _to_frontend_point(row: pd.Series) -> dict[str, Any]:
    """
    Convierte una fila del CSV de proyección al formato esperado por frontend.

    Se mantienen nombres similares a H1 para facilitar reutilización visual:
    - Participant_id
    - Trial
    - Experiment_id
    - Valence
    - Arousal
    - Dominance
    - Liking
    - Familiarity
    """
    familiarity_value: Any = row.get("familiarity")

    return {
        "Participant_id": int(row["participant_id"]),
        "Participant_label": f"S{int(row['participant_id']):02d}",
        "Trial": int(row["trial"]),
        "Experiment_id": int(row["experiment_id"]),
        "Valence": None if pd.isna(row.get("valence")) else float(row["valence"]),
        "Arousal": None if pd.isna(row.get("arousal")) else float(row["arousal"]),
        "Dominance": None if pd.isna(row.get("dominance")) else float(row["dominance"]),
        "Liking": None if pd.isna(row.get("liking")) else float(row["liking"]),
        "Familiarity": None if pd.isna(familiarity_value) else float(familiarity_value),
        "projection_method": str(row["projection_method"]),
        "x": float(row["x"]),
        "y": float(row["y"]),
    }


def load_tarea1_projection(method: str) -> dict[str, Any]:
    """
    Carga los puntos 2D de una proyección latente.

    Cada punto representa:
    - un participante,
    - un trial,
    - un experimento,
    - coordenadas x,y generadas por PCA/UMAP/t-SNE.
    """
    projection_path: Path = _build_projection_path(method)

    if not projection_path.exists():
        raise FileNotFoundError(
            f"No existe la proyección: {projection_path}. "
            "Ejecuta generate_latent_projections.py primero."
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


def _build_representation_input_path(
    participant: int,
    trial: int,
) -> Path:
    """
    Construye la ruta del .npz During-only usado en tarea1.
    """
    return (
        REPRESENTATION_INPUTS_DIR
        / f"s{participant:02d}"
        / f"trial_{trial:02d}_input.npz"
    )


def _downsample_signal(
    times: np.ndarray,
    values: np.ndarray,
    max_points: int = 1200,
) -> list[dict[str, float | None]]:
    """
    Reduce muestras solo para visualización.

    Las estadísticas se calculan con todas las muestras originales.
    """
    total_points: int = len(times)

    if total_points <= max_points:
        indices: np.ndarray = np.arange(total_points)
    else:
        indices = np.linspace(
            0,
            total_points - 1,
            max_points,
            dtype=int,
        )

    samples: list[dict[str, float | None]] = []

    for index in indices:
        value: float = float(values[index])

        samples.append(
            {
                "time": float(times[index]),
                "value": None if np.isnan(value) else value,
            }
        )

    return samples


def _compute_channel_statistics(values: np.ndarray) -> dict[str, float | None]:
    """
    Calcula estadísticas descriptivas de un canal durante During.
    """
    if values.size == 0 or np.all(np.isnan(values)):
        return {
            "mean": None,
            "std": None,
            "min": None,
            "max": None,
            "rms": None,
            "peak_to_peak": None,
        }

    return {
        "mean": float(np.nanmean(values)),
        "std": float(np.nanstd(values)),
        "min": float(np.nanmin(values)),
        "max": float(np.nanmax(values)),
        "rms": float(np.sqrt(np.nanmean(values ** 2))),
        "peak_to_peak": float(np.nanmax(values) - np.nanmin(values)),
    }


def _get_channel_type(channel_name: str) -> str:
    """
    Clasifica el canal para mostrarlo en el frontend.
    """
    if channel_name.startswith("EXG"):
        exg_number: int = int(channel_name.replace("EXG", ""))

        if 1 <= exg_number <= 4:
            return "EOG"

        return "EMG"

    if channel_name in {"GSR1", "Resp", "Plet", "Temp"}:
        return "PERIPHERAL"

    return "EEG"


def load_tarea1_trial_signals(
    participant: int,
    trial: int,
    channels: list[str] | None = None,
) -> dict[str, Any]:
    """
    Carga señales During-only para un trial seleccionado en tarea1.

    Entrada:
    - participant
    - trial
    - channels

    Salida:
    - señales downsampleadas para renderizado,
    - estadísticas por canal,
    - metadata básica del trial.
    """
    input_path: Path = _build_representation_input_path(
        participant=participant,
        trial=trial,
    )

    if not input_path.exists():
        raise FileNotFoundError(
            f"No existe representation input: {input_path}"
        )

    npz_data: Any = np.load(input_path, allow_pickle=True)

    signals_array: np.ndarray = np.asarray(npz_data["signals"])
    times: np.ndarray = np.asarray(npz_data["times"])
    available_channels: list[str] = [
        str(channel)
        for channel in npz_data["channels"].tolist()
    ]
    sfreq: float = float(npz_data["sfreq"][0])
    experiment_id: int = int(npz_data["experiment_id"][0])

    requested_channels: list[str] = channels or DEFAULT_CHANNELS

    valid_channels: list[str] = [
        channel
        for channel in requested_channels
        if channel in available_channels
    ]

    if not valid_channels:
        raise ValueError(
            "Ninguno de los canales solicitados existe en el trial. "
            f"Solicitados: {requested_channels}"
        )

    channel_to_index: dict[str, int] = {
        channel_name: index
        for index, channel_name in enumerate(available_channels)
    }

    signals: dict[str, list[dict[str, float | None]]] = {}
    statistics: dict[str, dict[str, float | None]] = {}
    channel_types: dict[str, str] = {}

    for channel_name in valid_channels:
        channel_index: int = channel_to_index[channel_name]
        values: np.ndarray = signals_array[channel_index]

        signals[channel_name] = _downsample_signal(
            times=times,
            values=values,
        )

        statistics[channel_name] = _compute_channel_statistics(values)
        channel_types[channel_name] = _get_channel_type(channel_name)

    return {
        "participant": participant,
        "participant_label": f"S{participant:02d}",
        "trial": trial,
        "experiment_id": experiment_id,
        "phase": "During",
        "sfreq": sfreq,
        "duration_sec": float(times[-1] - times[0]) if len(times) > 1 else 0.0,
        "channels": valid_channels,
        "channel_types": channel_types,
        "signals": signals,
        "statistics": statistics,
    }