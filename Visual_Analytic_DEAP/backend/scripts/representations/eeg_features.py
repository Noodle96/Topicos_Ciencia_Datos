from __future__ import annotations

import numpy as np

from backend.scripts.representations.feature_utils import (
    compute_band_log_power,
    get_channel_signal,
    validate_feature_vector,
)


EEG_CHANNELS_GENEVA_ORDER: list[str] = [
    "Fp1", "AF3", "F3", "F7",
    "FC5", "FC1", "C3", "T7",
    "CP5", "CP1", "P3", "P7",
    "PO3", "O1", "Oz", "Pz",
    "Fp2", "AF4", "Fz", "F4",
    "F8", "FC6", "FC2", "Cz",
    "C4", "T8", "CP6", "CP2",
    "P4", "P8", "PO4", "O2",
]


EEG_BANDS: dict[str, tuple[float, float]] = {
    "theta": (4.0, 8.0),
    "slow_alpha": (8.0, 10.0),
    "alpha": (8.0, 12.0),
    "beta": (12.0, 30.0),
    "gamma": (30.0, 45.0),
}


ASYMMETRY_BANDS: list[str] = [
    "theta",
    "alpha",
    "beta",
    "gamma",
]


SYMMETRIC_EEG_PAIRS: list[tuple[str, str]] = [
    ("Fp1", "Fp2"),
    ("AF3", "AF4"),
    ("F3", "F4"),
    ("F7", "F8"),
    ("FC5", "FC6"),
    ("FC1", "FC2"),
    ("C3", "C4"),
    ("T7", "T8"),
    ("CP5", "CP6"),
    ("CP1", "CP2"),
    ("P3", "P4"),
    ("P7", "P8"),
    ("PO3", "PO4"),
    ("O1", "O2"),
]


def extract_eeg_band_power_features(
    signals: np.ndarray,
    channels: list[str],
    sfreq: float,
) -> tuple[list[float], list[str]]:
    """
    Extrae features EEG de potencia espectral.

    Según DEAP:
    - Se calcula log(power) para cada canal EEG.
    - Bandas:
        theta       4–8 Hz
        slow alpha  8–10 Hz
        alpha       8–12 Hz
        beta        12–30 Hz
        gamma       30+ Hz

    En nuestro caso gamma se limita a 30–45 Hz porque el EEG fue filtrado
    previamente en 4–45 Hz.

    Total esperado:
    32 canales × 5 bandas = 160 features.
    """
    feature_values: list[float] = []
    feature_names: list[str] = []

    for channel_name in EEG_CHANNELS_GENEVA_ORDER:
        channel_signal: np.ndarray = get_channel_signal(
            signals=signals,
            channels=channels,
            channel_name=channel_name,
        )

        for band_name, (low_freq, high_freq) in EEG_BANDS.items():
            log_power: float = compute_band_log_power(
                signal=channel_signal,
                sfreq=sfreq,
                low_freq=low_freq,
                high_freq=high_freq,
            )

            feature_values.append(log_power)
            feature_names.append(f"EEG__{channel_name}__log_power__{band_name}")

    validate_feature_vector(
        feature_values=feature_values,
        feature_names=feature_names,
    )

    if len(feature_values) != 160:
        raise ValueError(f"EEG band power debe tener 160 features, obtuvo {len(feature_values)}")

    return feature_values, feature_names


def extract_eeg_asymmetry_features(
    signals: np.ndarray,
    channels: list[str],
    sfreq: float,
) -> tuple[list[float], list[str]]:
    """
    Extrae features EEG de asimetría hemisférica.

    Según DEAP:
    - Se calcula la diferencia de potencia espectral entre pares simétricos.
    - Se usan 14 pares izquierda/derecha.
    - Se calculan diferencias para theta, alpha, beta y gamma.

    Total esperado:
    14 pares × 4 bandas = 56 features.
    """
    feature_values: list[float] = []
    feature_names: list[str] = []

    for left_channel, right_channel in SYMMETRIC_EEG_PAIRS:
        left_signal: np.ndarray = get_channel_signal(
            signals=signals,
            channels=channels,
            channel_name=left_channel,
        )
        right_signal: np.ndarray = get_channel_signal(
            signals=signals,
            channels=channels,
            channel_name=right_channel,
        )

        for band_name in ASYMMETRY_BANDS:
            low_freq, high_freq = EEG_BANDS[band_name]

            left_log_power: float = compute_band_log_power(
                signal=left_signal,
                sfreq=sfreq,
                low_freq=low_freq,
                high_freq=high_freq,
            )

            right_log_power: float = compute_band_log_power(
                signal=right_signal,
                sfreq=sfreq,
                low_freq=low_freq,
                high_freq=high_freq,
            )

            asymmetry_value: float = left_log_power - right_log_power

            feature_values.append(asymmetry_value)
            feature_names.append(
                f"EEG__asymmetry__{left_channel}_minus_{right_channel}__{band_name}"
            )

    validate_feature_vector(
        feature_values=feature_values,
        feature_names=feature_names,
    )

    if len(feature_values) != 56:
        raise ValueError(f"EEG asymmetry debe tener 56 features, obtuvo {len(feature_values)}")

    return feature_values, feature_names


def extract_all_eeg_features(
    signals: np.ndarray,
    channels: list[str],
    sfreq: float,
) -> tuple[list[float], list[str]]:
    """
    Extrae todas las features EEG basadas en DEAP.

    Total esperado:
    - 160 band power features
    - 56 asymmetry features
    - 216 EEG features
    """
    band_values, band_names = extract_eeg_band_power_features(
        signals=signals,
        channels=channels,
        sfreq=sfreq,
    )

    asymmetry_values, asymmetry_names = extract_eeg_asymmetry_features(
        signals=signals,
        channels=channels,
        sfreq=sfreq,
    )

    feature_values: list[float] = band_values + asymmetry_values
    feature_names: list[str] = band_names + asymmetry_names

    validate_feature_vector(
        feature_values=feature_values,
        feature_names=feature_names,
    )

    if len(feature_values) != 216:
        raise ValueError(f"Total EEG debe ser 216 features, obtuvo {len(feature_values)}")

    return feature_values, feature_names