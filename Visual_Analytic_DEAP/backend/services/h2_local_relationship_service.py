from __future__ import annotations

from typing import Any

import numpy as np

from backend.services.h2_timeseries_service import build_timeseries_pair


def safe_pearson_correlation(
    x: np.ndarray,
    y: np.ndarray,
) -> float | None:
    """
    Calcula correlación Pearson entre dos señales.

    Retorna None si las señales están vacías, tienen diferente
    longitud o alguna tiene desviación estándar cero.
    """
    if x.size == 0 or y.size == 0:
        return None

    if x.shape[0] != y.shape[0]:
        return None

    x_std: float = float(np.std(x))
    y_std: float = float(np.std(y))

    if x_std == 0.0 or y_std == 0.0:
        return None

    correlation_matrix: np.ndarray = np.corrcoef(x, y)
    correlation: float = float(correlation_matrix[0, 1])

    if np.isnan(correlation):
        return None

    return correlation


def build_local_relationship(
    participant_id: int,
    trial: int,
    eeg_channel: str,
    peripheral_channel: str,
    start_sec: float,
    end_sec: float,
) -> dict[str, Any]:
    """
    Calcula la correlación local EEG ↔ periférica dentro de una
    ventana temporal seleccionada por el usuario.

    La ventana start_sec/end_sec se interpreta dentro de la fase During.
    """
    if start_sec < 0:
        raise ValueError("start_sec no puede ser negativo.")

    if end_sec <= start_sec:
        raise ValueError("end_sec debe ser mayor que start_sec.")

    pair_data: dict[str, Any] = build_timeseries_pair(
        participant_id=participant_id,
        trial=trial,
        eeg_channel=eeg_channel,
        peripheral_channel=peripheral_channel,
    )

    times: np.ndarray = np.asarray(pair_data["times"], dtype=float)
    eeg_values: np.ndarray = np.asarray(pair_data["eeg_values"], dtype=float)
    peripheral_values: np.ndarray = np.asarray(
        pair_data["peripheral_values"],
        dtype=float,
    )

    relative_times: np.ndarray = times - float(times[0])

    start_index: int = int(
        np.searchsorted(
            relative_times,
            start_sec,
            side="left",
        )
    )

    end_index: int = int(
        np.searchsorted(
            relative_times,
            end_sec,
            side="right",
        )
    )

    if start_index >= end_index:
        raise ValueError(
            "La ventana seleccionada no contiene muestras suficientes."
        )

    local_eeg: np.ndarray = eeg_values[start_index:end_index]
    local_peripheral: np.ndarray = peripheral_values[start_index:end_index]
    local_times: np.ndarray = relative_times[start_index:end_index]

    local_correlation: float | None = safe_pearson_correlation(
        x=local_eeg,
        y=local_peripheral,
    )

    result: dict[str, Any] = {
        "participant_id": participant_id,
        "trial": trial,
        "experiment_id": pair_data.get("experiment_id"),
        "phase": "during",
        "eeg_channel": eeg_channel,
        "peripheral_channel": peripheral_channel,
        "global_correlation": pair_data.get("correlation"),
        "local_correlation": local_correlation,
        "start_sec": start_sec,
        "end_sec": end_sec,
        "sample_count": int(local_eeg.shape[0]),
        "local_time_start": (
            float(local_times[0])
            if local_times.size > 0
            else None
        ),
        "local_time_end": (
            float(local_times[-1])
            if local_times.size > 0
            else None
        ),
    }

    return result