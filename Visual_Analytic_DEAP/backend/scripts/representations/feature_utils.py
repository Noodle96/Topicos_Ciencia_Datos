from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
from scipy.signal import welch


def load_representation_input_npz(
    npz_path: Path,
) -> tuple[np.ndarray, np.ndarray, list[str], float, int, int, int]:
    """
    Carga un archivo .npz generado por preprocess_representation_inputs.py.

    Retorna:
    - signals: matriz de señales con shape (n_channels, n_samples)
    - times: vector temporal con shape (n_samples,)
    - channels: nombres de canales
    - sfreq: frecuencia de muestreo procesada
    - participant_id: ID del participante
    - trial: número de trial
    - experiment_id: ID del estímulo real
    """
    npz_data: Any = np.load(npz_path, allow_pickle=True)

    signals: np.ndarray = np.asarray(npz_data["signals"])
    times: np.ndarray = np.asarray(npz_data["times"])
    channels: list[str] = [str(channel) for channel in npz_data["channels"].tolist()]
    sfreq: float = float(npz_data["sfreq"][0])
    participant_id: int = int(npz_data["participant_id"][0])
    trial: int = int(npz_data["trial"][0])
    experiment_id: int = int(npz_data["experiment_id"][0])

    return signals, times, channels, sfreq, participant_id, trial, experiment_id


def get_channel_signal(
    signals: np.ndarray,
    channels: list[str],
    channel_name: str,
) -> np.ndarray:
    """
    Obtiene la señal de un canal específico.

    Lanza error si el canal no existe, porque para esta etapa queremos
    detectar inconsistencias de forma explícita.
    """
    if channel_name not in channels:
        raise ValueError(f"Canal no encontrado: {channel_name}")

    channel_index: int = channels.index(channel_name)
    return signals[channel_index]


def compute_band_log_power(
    signal: np.ndarray,
    sfreq: float,
    low_freq: float,
    high_freq: float,
) -> float:
    """
    Calcula log(power) en una banda de frecuencia usando Welch.

    Este cálculo sigue la idea del paper DEAP:
    usar logaritmo de potencia espectral por banda.

    Nota:
    - high_freq debe estar dentro del límite de Nyquist.
    - Se agrega un epsilon pequeño para evitar log(0).
    """
    freqs: np.ndarray
    psd: np.ndarray

    freqs, psd = welch(
        signal,
        fs=sfreq,
        nperseg=min(int(sfreq * 2), signal.shape[0]),
    )

    band_mask: np.ndarray = (freqs >= low_freq) & (freqs < high_freq)

    if not np.any(band_mask):
        return float("nan")

    band_power: float = float(np.trapz(psd[band_mask], freqs[band_mask]))
    epsilon: float = 1e-12

    return float(np.log(band_power + epsilon))


def validate_feature_vector(
    feature_values: list[float],
    feature_names: list[str],
) -> None:
    """
    Valida que el vector de valores y nombres tenga la misma longitud.
    """
    if len(feature_values) != len(feature_names):
        raise ValueError(
            "Inconsistencia en features: "
            f"{len(feature_values)} valores vs {len(feature_names)} nombres."
        )