from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from backend.utils.paths import DATASET_DIR


# ---------------------------------------------------------------------
# H2 configuration
# ---------------------------------------------------------------------

PROCESSED_TRIALS_DIR: Path = DATASET_DIR / "processed" / "trials"
PROCESSED_EVENTS_DIR: Path = DATASET_DIR / "processed" / "events"
OUTPUT_RELATIONSHIPS_DIR: Path = DATASET_DIR / "processed" / "relationships"
def clean_output_directory() -> None:
    """
    Elimina completamente la carpeta de relaciones procesadas.

    Esto permite regenerar todos los archivos desde cero
    y mantener reproducibilidad del preprocessing.
    """
    if OUTPUT_RELATIONSHIPS_DIR.exists():
        shutil.rmtree(OUTPUT_RELATIONSHIPS_DIR)
        print(f"[INFO] Carpeta eliminada: {OUTPUT_RELATIONSHIPS_DIR}")

EEG_CHANNELS_H2: list[str] = [
    "Fp1", "Fp2",
    "F3", "F4", "Fz",
    "C3", "C4", "Cz",
    "O1", "O2",
]

PERIPHERAL_CHANNELS_H2: list[str] = [
    "GSR1",
    "Resp",
    "Plet",
    "Temp",
]


def load_json(file_path: Path) -> dict[str, Any]:
    """Carga un archivo JSON y devuelve su contenido como diccionario."""
    with file_path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = json.load(file)

    return data


def save_json(data: dict[str, Any], file_path: Path) -> None:
    """Guarda un diccionario como archivo JSON con indentación legible."""
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def safe_pearson_correlation(x: np.ndarray, y: np.ndarray) -> float | None:
    """
    Calcula correlación Pearson entre dos señales.

    Retorna None si alguna señal está vacía, tiene longitud distinta
    o tiene desviación estándar cero.
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


def get_channel_index(channels: list[str], channel_name: str) -> int | None:
    """Devuelve el índice de un canal dentro de la lista de canales."""
    try:
        return channels.index(channel_name)
    except ValueError:
        return None


def extract_during_indices(event_info: dict[str, Any], times: np.ndarray) -> tuple[int, int]:
    """
    Obtiene los índices temporales correspondientes a la fase During.

    Usa los tiempos procesados:
    - processed_during_start_sec
    - processed_after_start_sec

    Estos tiempos están expresados en segundos dentro del trial procesado.
    """
    during_start_sec: float = float(event_info["processed_during_start_sec"])
    during_end_sec: float = float(event_info["processed_after_start_sec"])

    start_index: int = int(np.searchsorted(times, during_start_sec, side="left"))
    end_index: int = int(np.searchsorted(times, during_end_sec, side="right"))

    return start_index, end_index


def load_trial_npz(trial_file: Path) -> tuple[np.ndarray, np.ndarray, list[str], float]:
    """
    Carga un archivo trial_XX.npz generado por H1.

    Retorna:
    - signals: matriz de señales
    - times: vector temporal
    - channels: nombres de canales
    - sfreq: frecuencia de muestreo procesada
    """
    npz_data: Any = np.load(trial_file, allow_pickle=True)

    signals: np.ndarray = np.asarray(npz_data["signals"])
    times: np.ndarray = np.asarray(npz_data["times"])
    channels: list[str] = [str(channel) for channel in npz_data["channels"].tolist()]
    sfreq: float = float(npz_data["sfreq"])

    return signals, times, channels, sfreq


def build_trial_relationships(
    participant_id: int,
    trial: int,
    trial_file: Path,
    event_info: dict[str, Any],
) -> dict[str, Any]:
    """
    Construye las relaciones EEG ↔ periféricas para un trial.

    Solo utiliza la fase During y calcula correlación Pearson entre
    cada canal EEG seleccionado y cada señal periférica seleccionada.
    """
    signals, times, channels, sfreq = load_trial_npz(trial_file)

    during_start_index, during_end_index = extract_during_indices(
        event_info=event_info,
        times=times,
    )

    relationships: list[dict[str, Any]] = []

    for eeg_channel in EEG_CHANNELS_H2:
        eeg_index: int | None = get_channel_index(channels, eeg_channel)

        if eeg_index is None:
            continue

        eeg_signal: np.ndarray = signals[eeg_index, during_start_index:during_end_index]

        for peripheral_channel in PERIPHERAL_CHANNELS_H2:
            peripheral_index: int | None = get_channel_index(channels, peripheral_channel)

            if peripheral_index is None:
                continue

            peripheral_signal: np.ndarray = signals[
                peripheral_index,
                during_start_index:during_end_index,
            ]

            correlation: float | None = safe_pearson_correlation(
                x=eeg_signal,
                y=peripheral_signal,
            )

            relationships.append(
                {
                    "eeg_channel": eeg_channel,
                    "peripheral_channel": peripheral_channel,
                    "correlation": correlation,
                }
            )

    result: dict[str, Any] = {
        "participant_id": participant_id,
        "trial": trial,
        "experiment_id": event_info.get("experiment_id"),
        "phase": "during",
        "method": "pearson",
        "sfreq": sfreq,
        "during_start_sec": event_info.get("processed_during_start_sec"),
        "during_end_sec": event_info.get("processed_after_start_sec"),
        "relationships": relationships,
    }

    return result


def preprocess_participant_relationships(participant_id: int) -> None:
    """
    Procesa todos los trials disponibles de un participante.

    Lee:
    - dataset/processed/trials/sXX/trial_YY.npz
    - dataset/processed/events/sXX_events.json

    Guarda:
    - dataset/processed/relationships/sXX/trial_YY_relationships.json
    """
    participant_code: str = f"s{participant_id:02d}"

    participant_trials_dir: Path = PROCESSED_TRIALS_DIR / participant_code
    participant_output_dir: Path = OUTPUT_RELATIONSHIPS_DIR / participant_code
    events_file: Path = PROCESSED_EVENTS_DIR / f"{participant_code}_events.json"

    if not participant_trials_dir.exists():
        print(f"[WARN] No existe carpeta de trials: {participant_trials_dir}")
        return

    if not events_file.exists():
        print(f"[WARN] No existe archivo de eventos: {events_file}")
        return

    events_data: dict[str, Any] = load_json(events_file)
    trials_events: list[dict[str, Any]] = events_data.get("trials", [])

    for event_info in trials_events:
        trial: int = int(event_info["trial"])

        trial_file: Path = participant_trials_dir / f"trial_{trial:02d}.npz"
        output_file: Path = participant_output_dir / f"trial_{trial:02d}_relationships.json"

        if not trial_file.exists():
            print(f"[WARN] No existe trial procesado: {trial_file}")
            continue

        relationships_data: dict[str, Any] = build_trial_relationships(
            participant_id=participant_id,
            trial=trial,
            trial_file=trial_file,
            event_info=event_info,
        )

        save_json(data=relationships_data, file_path=output_file)

        print(f"[OK] Guardado: {output_file}")


def preprocess_all_relationships() -> None:
    """Procesa las relaciones H2 para los 32 participantes del dataset DEAP."""
    for participant_id in range(1, 33):
        print(f"\n[INFO] Procesando participante S{participant_id:02d}")
        preprocess_participant_relationships(participant_id=participant_id)


if __name__ == "__main__":
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Preprocessing H2: relaciones EEG ↔ periféricas"
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Elimina archivos previos antes de regenerar relaciones.",
    )

    args: argparse.Namespace = parser.parse_args()

    if args.clean:
        clean_output_directory()

    preprocess_all_relationships()

# python -m backend.scripts.preprocess_h2_relationships --clean