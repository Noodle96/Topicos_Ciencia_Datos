from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from backend.services.h2_relationship_service import (
    load_trial_relationships,
)
from backend.utils.paths import DATASET_DIR


PROCESSED_TRIALS_DIR: Path = DATASET_DIR / "processed" / "trials"


def load_trial_npz(
    participant_id: int,
    trial: int,
) -> tuple[np.ndarray, np.ndarray, list[str], float]:
    """
    Carga el archivo .npz procesado correspondiente a un trial.

    Retorna:
    - signals
    - times
    - channels
    - sfreq
    """
    participant_code: str = f"s{participant_id:02d}"

    trial_file: Path = (
        PROCESSED_TRIALS_DIR
        / participant_code
        / f"trial_{trial:02d}.npz"
    )

    if not trial_file.exists():
        raise FileNotFoundError(
            f"No existe archivo trial: {trial_file}"
        )

    npz_data: Any = np.load(
        trial_file,
        allow_pickle=True,
    )

    signals: np.ndarray = np.asarray(npz_data["signals"])
    times: np.ndarray = np.asarray(npz_data["times"])
    channels: list[str] = [
        str(channel)
        for channel in npz_data["channels"].tolist()
    ]
    sfreq: float = float(npz_data["sfreq"])

    return signals, times, channels, sfreq


def get_channel_index(
    channels: list[str],
    channel_name: str,
) -> int:
    """
    Obtiene el índice de un canal.

    Lanza excepción si el canal no existe.
    """
    if channel_name not in channels:
        raise ValueError(
            f"Canal no encontrado: {channel_name}"
        )

    return channels.index(channel_name)


def extract_during_indices(
    relationship_data: dict[str, Any],
    times: np.ndarray,
) -> tuple[int, int]:
    """
    Obtiene índices temporales de la fase During.
    """
    during_start_sec: float = float(
        relationship_data["during_start_sec"]
    )

    during_end_sec: float = float(
        relationship_data["during_end_sec"]
    )

    start_index: int = int(
        np.searchsorted(
            times,
            during_start_sec,
            side="left",
        )
    )

    end_index: int = int(
        np.searchsorted(
            times,
            during_end_sec,
            side="right",
        )
    )

    return start_index, end_index


def get_pair_correlation(
    relationship_data: dict[str, Any],
    channel_a: str,
    channel_b: str,
) -> float | None:
    """
    Busca la correlación entre dos canales.

    Revisa ambas direcciones porque el preprocessing puede guardar
    el par como source→target o como target→source según los grupos.
    """
    relationships: list[dict[str, Any]] = relationship_data.get(
        "relationships",
        [],
    )

    for item in relationships:
        source_channel: str = str(item.get("source_channel"))
        target_channel: str = str(item.get("target_channel"))

        is_direct_match: bool = (
            source_channel == channel_a
            and target_channel == channel_b
        )

        is_reverse_match: bool = (
            source_channel == channel_b
            and target_channel == channel_a
        )

        if is_direct_match or is_reverse_match:
            correlation: Any = item.get("correlation")

            if correlation is None:
                return None

            return float(correlation)

    return None


def build_timeseries_pair(
    participant_id: int,
    trial: int,
    channel_a: str,
    channel_b: str,
) -> dict[str, Any]:
    """
    Construye un par sincronizado canal A ↔ canal B durante During.

    Esta versión es general y permite combinaciones como:
    - EEG ↔ PERIPHERAL
    - EEG ↔ EEG
    - EEG ↔ EXG
    - EXG ↔ PERIPHERAL
    - PERIPHERAL ↔ PERIPHERAL
    """
    relationship_data: dict[str, Any] = load_trial_relationships(
        participant_id=participant_id,
        trial=trial,
    )

    signals, times, channels, sfreq = load_trial_npz(
        participant_id=participant_id,
        trial=trial,
    )

    during_start_index, during_end_index = extract_during_indices(
        relationship_data=relationship_data,
        times=times,
    )

    channel_a_index: int = get_channel_index(
        channels=channels,
        channel_name=channel_a,
    )

    channel_b_index: int = get_channel_index(
        channels=channels,
        channel_name=channel_b,
    )

    during_times: np.ndarray = times[
        during_start_index:during_end_index
    ]

    channel_a_values: np.ndarray = signals[
        channel_a_index,
        during_start_index:during_end_index,
    ]

    channel_b_values: np.ndarray = signals[
        channel_b_index,
        during_start_index:during_end_index,
    ]

    correlation: float | None = get_pair_correlation(
        relationship_data=relationship_data,
        channel_a=channel_a,
        channel_b=channel_b,
    )

    result: dict[str, Any] = {
        "participant_id": participant_id,
        "trial": trial,
        "experiment_id": relationship_data.get("experiment_id"),
        "phase": "during",
        "sfreq": sfreq,
        "channel_a": channel_a,
        "channel_b": channel_b,
        "correlation": correlation,
        "times": during_times.tolist(),
        "channel_a_values": channel_a_values.tolist(),
        "channel_b_values": channel_b_values.tolist(),
    }

    return result