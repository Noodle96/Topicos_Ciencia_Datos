from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import numpy as np

from backend.utils.paths import DATASET_DIR


PROCESSED_DIR: Path = DATASET_DIR / "processed"
PROCESSED_TRIALS_DIR: Path = PROCESSED_DIR / "trials"
PROCESSED_EVENTS_DIR: Path = PROCESSED_DIR / "events"
PROCESSED_METRICS_DIR: Path = PROCESSED_DIR / "metrics"

DEFAULT_CHANNELS: list[str] = [
    "Fp1",
    "Fp2",
    "F3",
    "F4",
    "GSR1",
    "Resp",
]

UNUSED_CHANNELS: set[str] = {
    "GSR2",
    "Erg1",
    "Erg2",
}


def _build_trial_npz_path(
    participant: int,
    trial: int,
) -> Path:
    """
    Construye la ruta del archivo .npz preprocesado de un trial.
    """
    return (
        PROCESSED_TRIALS_DIR
        / f"s{participant:02d}"
        / f"trial_{trial:02d}.npz"
    )


def _build_metrics_json_path(
    participant: int,
    trial: int,
) -> Path:
    """
    Construye la ruta del archivo de métricas preprocesadas.
    """
    return (
        PROCESSED_METRICS_DIR
        / f"s{participant:02d}"
        / f"trial_{trial:02d}_metrics.json"
    )


def _build_events_json_path(participant: int) -> Path:
    """
    Construye la ruta del archivo de eventos preprocesados.
    """
    return (
        PROCESSED_EVENTS_DIR
        / f"s{participant:02d}_events.json"
    )


def _load_json(path: Path) -> Dict[str, Any]:
    """
    Carga un archivo JSON.
    """
    if not path.exists():
        raise FileNotFoundError(f"No existe el archivo: {path}")

    with path.open("r", encoding="utf-8") as file:
        data: Dict[str, Any] = json.load(file)

    return data


def _get_trial_event_metadata(
    participant: int,
    trial: int,
) -> Dict[str, Any]:
    """
    Obtiene metadata/eventos reales de un trial.
    """
    events_path: Path = _build_events_json_path(participant)
    events_data: Dict[str, Any] = _load_json(events_path)

    for trial_info in events_data["trials"]:
        if int(trial_info["trial"]) == trial:
            return trial_info

    raise ValueError(
        f"No se encontró metadata para S{participant:02d}, trial {trial}"
    )


def _downsample_signal(
    times: np.ndarray,
    values: np.ndarray,
    max_points: int = 1200,
) -> List[Dict[str, float | None]]:
    """
    Reduce puntos solo para visualización.

    Las métricas NO se calculan aquí; ya están precalculadas
    usando todas las muestras del trial.
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

    samples: List[Dict[str, float | None]] = []

    for index in indices:
        value: float = float(values[index])

        samples.append(
            {
                "time": float(times[index]),
                "value": None if np.isnan(value) else value,
            }
        )

    return samples


def _load_trial_npz(
    participant: int,
    trial: int,
) -> Dict[str, Any]:
    """
    Carga señales preprocesadas de un trial.
    """
    trial_path: Path = _build_trial_npz_path(
        participant=participant,
        trial=trial,
    )

    if not trial_path.exists():
        raise FileNotFoundError(
            f"No existe el trial preprocesado: {trial_path}. "
            "Ejecuta primero preprocess_trials.py."
        )

    npz_data: np.lib.npyio.NpzFile = np.load(
        trial_path,
        allow_pickle=True,
    )

    return {
        "signals": npz_data["signals"],
        "times": npz_data["times"],
        "channels": npz_data["channels"].astype(str).tolist(),
        "sfreq": float(npz_data["sfreq"][0]),
    }


def _filter_requested_channels(
    requested_channels: list[str],
    available_channels: list[str],
) -> list[str]:
    """
    Filtra canales solicitados para mantener solo los existentes
    y excluir canales no usados.
    """
    return [
        channel
        for channel in requested_channels
        if channel in available_channels
        and channel not in UNUSED_CHANNELS
    ]


def load_trial_signals(
    participant: int,
    trial: int,
    channels: list[str] | None = None,
) -> Dict[str, Any]:
    """
    Carga señales preprocesadas de un trial.

    Este servicio ya NO abre archivos .bdf en tiempo real.
    Lee archivos .npz/.json generados previamente por:

    python -m backend.scripts.preprocess_trials --participants all --clean
    """

    requested_channels: list[str] = channels or DEFAULT_CHANNELS

    trial_data: Dict[str, Any] = _load_trial_npz(
        participant=participant,
        trial=trial,
    )

    event_metadata: Dict[str, Any] = _get_trial_event_metadata(
        participant=participant,
        trial=trial,
    )

    metrics_path: Path = _build_metrics_json_path(
        participant=participant,
        trial=trial,
    )

    metrics_data: Dict[str, Any] = _load_json(metrics_path)

    all_signals: np.ndarray = trial_data["signals"]
    times: np.ndarray = trial_data["times"]
    available_channels: list[str] = trial_data["channels"]

    valid_channels: list[str] = _filter_requested_channels(
        requested_channels=requested_channels,
        available_channels=available_channels,
    )

    if not valid_channels:
        raise ValueError(
            "Ninguno de los canales solicitados existe en el trial procesado. "
            f"Canales solicitados: {requested_channels}. "
            f"Canales disponibles: {available_channels}"
        )

    signals: Dict[str, List[Dict[str, float | None]]] = {}

    channel_to_index: dict[str, int] = {
        channel_name: index
        for index, channel_name in enumerate(available_channels)
    }

    for channel_name in valid_channels:
        channel_index: int = channel_to_index[channel_name]

        signals[channel_name] = _downsample_signal(
            times=times,
            values=all_signals[channel_index],
        )

    selected_metrics: Dict[str, Any] = {
        channel_name: metrics_data["metrics"][channel_name]
        for channel_name in valid_channels
        if channel_name in metrics_data["metrics"]
    }

    phases: list[dict[str, Any]] = [
        {
            "name": "Before",
            "status": 3,
            "start": event_metadata["phases"]["Before"]["start"],
            "end": event_metadata["phases"]["Before"]["end"],
        },
        {
            "name": "During",
            "status": 4,
            "start": event_metadata["phases"]["During"]["start"],
            "end": event_metadata["phases"]["During"]["end"],
        },
        {
            "name": "After",
            "status": 5,
            "start": event_metadata["phases"]["After"]["start"],
            "end": event_metadata["phases"]["After"]["end"],
        },
    ]

    return {
        "participant": participant,
        "trial": trial,
        "experiment_id": event_metadata["experiment_id"],
        "sfreq": trial_data["sfreq"],
        "channels": valid_channels,
        "phases": phases,
        "signals": signals,
        "metrics": selected_metrics,
        "metadata": {
            "valence": event_metadata["valence"],
            "arousal": event_metadata["arousal"],
            "dominance": event_metadata["dominance"],
            "liking": event_metadata["liking"],
            "familiarity": event_metadata["familiarity"],
            "trial_duration_sec": event_metadata["trial_duration_sec"],
            "before_duration_sec": event_metadata["before_duration_sec"],
            "during_duration_sec": event_metadata["during_duration_sec"],
            "after_duration_sec": event_metadata["after_duration_sec"],
        },
    }