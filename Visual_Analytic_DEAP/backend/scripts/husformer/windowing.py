from __future__ import annotations

import numpy as np


def generate_trial_windows(
    signals: np.ndarray,
    sfreq: float,
    window_seconds: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Divide la señal completa de un trial en ventanas consecutivas no solapadas.

    Sigue el mismo esquema de ventaneo que usan los scripts de ejemplo de
    Husformer (make_data/Pre-DEAP.py): ventanas de duración fija, sin overlap.

    Parámetros:
    - signals: señal del trial completo, shape (n_canales, n_muestras).
    - sfreq: frecuencia de muestreo real de la señal (Hz).
    - window_seconds: duración deseada de cada ventana, en segundos.

    Retorna una tupla:
    - windows: shape (n_ventanas, n_canales, muestras_por_ventana).
    - window_start_seconds: shape (n_ventanas,), segundo de inicio de cada
      ventana relativo al inicio del trial (para el manifest de trazabilidad).

    Si el total de muestras no es múltiplo exacto de muestras_por_ventana, la
    última ventana incompleta se descarta (no se rellena con ceros), para no
    introducir señal artificial en el modelo.
    """
    samples_per_window: int = int(round(sfreq * window_seconds))

    if samples_per_window <= 0:
        raise ValueError(
            f"window_seconds={window_seconds} y sfreq={sfreq} producen "
            f"samples_per_window={samples_per_window}, debe ser positivo."
        )

    n_channels, n_total_samples = signals.shape
    n_windows: int = n_total_samples // samples_per_window

    if n_windows == 0:
        raise ValueError(
            f"La señal tiene {n_total_samples} muestras, insuficientes para "
            f"una sola ventana de {samples_per_window} muestras."
        )

    n_used_samples: int = n_windows * samples_per_window
    trimmed_signals: np.ndarray = signals[:, :n_used_samples]

    # reshape conserva el orden (row-major): cada canal se parte en n_windows
    # bloques contiguos de samples_per_window muestras cada uno.
    windows: np.ndarray = trimmed_signals.reshape(
        n_channels, n_windows, samples_per_window
    ).transpose(1, 0, 2)

    window_start_seconds: np.ndarray = (
        np.arange(n_windows) * samples_per_window / sfreq
    )

    return windows, window_start_seconds
