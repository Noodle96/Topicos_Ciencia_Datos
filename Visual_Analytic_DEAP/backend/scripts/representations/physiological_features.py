from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

from backend.scripts.representations.feature_utils import (
    compute_band_log_power,
    get_channel_signal,
    validate_feature_vector,
)


EOG_CHANNELS: list[str] = ["EXG1", "EXG2", "EXG3", "EXG4"]
EMG_CHANNELS: list[str] = ["EXG5", "EXG6", "EXG7", "EXG8"]

GSR_CHANNEL: str = "GSR1"
RESP_CHANNEL: str = "Resp"
PLET_CHANNEL: str = "Plet"
TEMP_CHANNEL: str = "Temp"


def compute_basic_signal_features(
    signal: np.ndarray,
    prefix: str,
) -> tuple[list[float], list[str]]:
    """
    Calcula estadísticas básicas de una señal fisiológica.

    Estas estadísticas no sustituyen a las features específicas de DEAP,
    pero son usadas como parte de la descripción general de la dinámica
    temporal de señales periféricas.
    """
    derivative: np.ndarray = np.diff(signal)

    feature_values: list[float] = [
        float(np.mean(signal)),
        float(np.std(signal)),
        float(np.min(signal)),
        float(np.max(signal)),
        float(np.sqrt(np.mean(signal ** 2))),
        float(np.mean(np.abs(derivative))) if derivative.size > 0 else 0.0,
    ]

    feature_names: list[str] = [
        f"{prefix}__mean",
        f"{prefix}__std",
        f"{prefix}__min",
        f"{prefix}__max",
        f"{prefix}__rms",
        f"{prefix}__mean_abs_derivative",
    ]

    return feature_values, feature_names


def extract_gsr_features(
    signals: np.ndarray,
    channels: list[str],
    sfreq: float,
) -> tuple[list[float], list[str]]:
    """
    Extrae características de GSR.

    Basado en la descripción de DEAP/Table 5:
    - valor medio de GSR;
    - dinámica de derivada;
    - componentes relacionadas con cambios rápidos;
    - conteo de eventos/peaks.

    En DEAP, GSR se asocia con activación/arousal porque la resistencia
    de la piel cambia con la sudoración.
    """
    signal: np.ndarray = get_channel_signal(
        signals=signals,
        channels=channels,
        channel_name=GSR_CHANNEL,
    )

    derivative: np.ndarray = np.diff(signal)
    negative_derivative: np.ndarray = derivative[derivative < 0]

    peaks, _ = find_peaks(signal)
    minima, _ = find_peaks(-signal)

    values, names = compute_basic_signal_features(
        signal=signal,
        prefix="GSR",
    )

    values.extend(
        [
            float(np.mean(derivative)) if derivative.size > 0 else 0.0,
            float(np.mean(negative_derivative)) if negative_derivative.size > 0 else 0.0,
            float(negative_derivative.size / derivative.size) if derivative.size > 0 else 0.0,
            float(len(peaks)),
            float(len(minima)),
            compute_band_log_power(signal, sfreq, 0.0, 2.4),
        ]
    )

    names.extend(
        [
            "GSR__mean_derivative",
            "GSR__mean_negative_derivative",
            "GSR__proportion_negative_derivative",
            "GSR__num_peaks",
            "GSR__num_local_minima",
            "GSR__log_power_0_2_4Hz",
        ]
    )

    validate_feature_vector(values, names)
    return values, names


def extract_respiration_features(
    signals: np.ndarray,
    channels: list[str],
    sfreq: float,
) -> tuple[list[float], list[str]]:
    """
    Extrae características de respiración.

    DEAP considera respiración porque:
    - respiración lenta se asocia con relajación;
    - ritmo irregular o rápido se asocia con mayor activación emocional.

    Aquí usamos:
    - estadísticas básicas;
    - conteo de ciclos respiratorios aproximado mediante peaks;
    - potencia espectral de baja frecuencia.
    """
    signal: np.ndarray = get_channel_signal(
        signals=signals,
        channels=channels,
        channel_name=RESP_CHANNEL,
    )

    values, names = compute_basic_signal_features(
        signal=signal,
        prefix="Resp",
    )

    min_distance_samples: int = int(max(sfreq * 1.0, 1))
    peaks, _ = find_peaks(signal, distance=min_distance_samples)

    duration_min: float = signal.shape[0] / sfreq / 60.0
    breathing_rate: float = float(len(peaks) / duration_min) if duration_min > 0 else 0.0

    values.extend(
        [
            float(len(peaks)),
            breathing_rate,
            compute_band_log_power(signal, sfreq, 0.0, 2.4),
        ]
    )

    names.extend(
        [
            "Resp__num_peaks",
            "Resp__breathing_rate_per_min",
            "Resp__log_power_0_2_4Hz",
        ]
    )

    validate_feature_vector(values, names)
    return values, names


def extract_temperature_features(
    signals: np.ndarray,
    channels: list[str],
    sfreq: float,
) -> tuple[list[float], list[str]]:
    """
    Extrae características de temperatura de piel.

    En DEAP, la temperatura se registra porque puede variar con estados
    emocionales. Es una señal lenta, por eso se priorizan estadísticas y
    tendencia temporal.
    """
    signal: np.ndarray = get_channel_signal(
        signals=signals,
        channels=channels,
        channel_name=TEMP_CHANNEL,
    )

    values, names = compute_basic_signal_features(
        signal=signal,
        prefix="Temp",
    )

    time_axis: np.ndarray = np.arange(signal.shape[0]) / sfreq

    if signal.shape[0] > 1:
        slope: float = float(np.polyfit(time_axis, signal, deg=1)[0])
    else:
        slope = 0.0

    values.append(slope)
    names.append("Temp__linear_slope")

    validate_feature_vector(values, names)
    return values, names


def extract_plet_features(
    signals: np.ndarray,
    channels: list[str],
    sfreq: float,
) -> tuple[list[float], list[str]]:
    """
    Extrae características de Plet/BVP.

    El paper DEAP menciona que la señal de plethysmograph permite estimar:
    - heart rate;
    - interbeat intervals;
    - HRV;
    - características espectrales derivadas de HRV.

    Aquí usamos detección aproximada de peaks sobre Plet.
    """
    signal: np.ndarray = get_channel_signal(
        signals=signals,
        channels=channels,
        channel_name=PLET_CHANNEL,
    )

    values, names = compute_basic_signal_features(
        signal=signal,
        prefix="Plet",
    )

    min_distance_samples: int = int(max(sfreq * 0.35, 1))
    peaks, _ = find_peaks(signal, distance=min_distance_samples)

    duration_min: float = signal.shape[0] / sfreq / 60.0
    heart_rate: float = float(len(peaks) / duration_min) if duration_min > 0 else 0.0

    if len(peaks) >= 2:
        ibi_seconds: np.ndarray = np.diff(peaks) / sfreq
        hrv_mean_ibi: float = float(np.mean(ibi_seconds))
        hrv_std_ibi: float = float(np.std(ibi_seconds))
        hrv_rmssd: float = float(np.sqrt(np.mean(np.diff(ibi_seconds) ** 2))) if len(ibi_seconds) > 1 else 0.0
    else:
        hrv_mean_ibi = 0.0
        hrv_std_ibi = 0.0
        hrv_rmssd = 0.0

    values.extend(
        [
            float(len(peaks)),
            heart_rate,
            hrv_mean_ibi,
            hrv_std_ibi,
            hrv_rmssd,
            compute_band_log_power(signal, sfreq, 0.0, 2.4),
        ]
    )

    names.extend(
        [
            "Plet__num_peaks",
            "Plet__heart_rate_per_min",
            "Plet__hrv_mean_ibi_sec",
            "Plet__hrv_std_ibi_sec",
            "Plet__hrv_rmssd_sec",
            "Plet__log_power_0_2_4Hz",
        ]
    )

    validate_feature_vector(values, names)
    return values, names


def extract_eog_features(
    signals: np.ndarray,
    channels: list[str],
    sfreq: float,
) -> tuple[list[float], list[str]]:
    """
    Extrae características de EOG.

    DEAP menciona blink rate como característica relacionada con ansiedad.
    Los canales EXG1–EXG4 se tratan como EOG en nuestro mapeo.
    """
    values: list[float] = []
    names: list[str] = []

    for channel_name in EOG_CHANNELS:
        signal: np.ndarray = get_channel_signal(
            signals=signals,
            channels=channels,
            channel_name=channel_name,
        )

        channel_values, channel_names = compute_basic_signal_features(
            signal=signal,
            prefix=f"EOG_{channel_name}",
        )

        threshold: float = float(np.mean(signal) + 2.0 * np.std(signal))
        min_distance_samples: int = int(max(sfreq * 0.2, 1))
        peaks, _ = find_peaks(signal, height=threshold, distance=min_distance_samples)

        duration_min: float = signal.shape[0] / sfreq / 60.0
        blink_rate: float = float(len(peaks) / duration_min) if duration_min > 0 else 0.0

        channel_values.extend(
            [
                float(len(peaks)),
                blink_rate,
            ]
        )

        channel_names.extend(
            [
                f"EOG_{channel_name}__num_blink_like_peaks",
                f"EOG_{channel_name}__blink_like_rate_per_min",
            ]
        )

        values.extend(channel_values)
        names.extend(channel_names)

    validate_feature_vector(values, names)
    return values, names


def extract_emg_features(
    signals: np.ndarray,
    channels: list[str],
    sfreq: float,
) -> tuple[list[float], list[str]]:
    """
    Extrae características de EMG.

    DEAP indica que la actividad muscular EMG se representa mediante energía
    en el rango 4–40 Hz, donde se concentra gran parte de la potencia durante
    contracción muscular.
    """
    values: list[float] = []
    names: list[str] = []

    for channel_name in EMG_CHANNELS:
        signal: np.ndarray = get_channel_signal(
            signals=signals,
            channels=channels,
            channel_name=channel_name,
        )

        channel_values, channel_names = compute_basic_signal_features(
            signal=signal,
            prefix=f"EMG_{channel_name}",
        )

        emg_log_energy_4_40: float = compute_band_log_power(
            signal=signal,
            sfreq=sfreq,
            low_freq=4.0,
            high_freq=40.0,
        )

        channel_values.append(emg_log_energy_4_40)
        channel_names.append(f"EMG_{channel_name}__log_power_4_40Hz")

        values.extend(channel_values)
        names.extend(channel_names)

    validate_feature_vector(values, names)
    return values, names


def extract_all_physiological_features(
    signals: np.ndarray,
    channels: list[str],
    sfreq: float,
) -> tuple[list[float], list[str]]:
    """
    Extrae todas las características fisiológicas no-EEG disponibles.

    Este bloque corresponde al grupo de señales fisiológicas periféricas
    descritas en DEAP:
    - GSR;
    - respiration;
    - skin temperature;
    - blood volume by plethysmograph;
    - EOG;
    - EMG.

    Nota metodológica:
    En nuestro RAW no se usa ECG explícito, por lo que las características
    de ritmo cardiaco se aproximan desde Plet/BVP.
    """
    feature_values: list[float] = []
    feature_names: list[str] = []

    extractors = [
        extract_gsr_features,
        extract_respiration_features,
        extract_temperature_features,
        extract_plet_features,
        extract_eog_features,
        extract_emg_features,
    ]

    for extractor in extractors:
        values, names = extractor(
            signals=signals,
            channels=channels,
            sfreq=sfreq,
        )
        feature_values.extend(values)
        feature_names.extend(names)

    validate_feature_vector(
        feature_values=feature_values,
        feature_names=feature_names,
    )

    return feature_values, feature_names