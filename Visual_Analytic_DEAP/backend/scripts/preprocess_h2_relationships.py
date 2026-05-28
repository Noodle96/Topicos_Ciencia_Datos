from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from backend.utils.paths import DATASET_DIR


PROCESSED_TRIALS_DIR: Path = DATASET_DIR / "processed" / "trials"
PROCESSED_EVENTS_DIR: Path = DATASET_DIR / "processed" / "events"
OUTPUT_RELATIONSHIPS_DIR: Path = DATASET_DIR / "processed" / "relationships"


CHANNEL_GROUPS: dict[str, list[str]] = {
    "EEG": [
        "Fp1", "AF3", "F7", "F3", "FC1", "FC5", "T7", "C3",
        "CP1", "CP5", "P7", "P3", "Pz", "PO3", "O1", "Oz",
        "O2", "PO4", "P4", "P8", "CP6", "CP2", "C4", "T8",
        "FC6", "FC2", "F4", "F8", "AF4", "Fp2", "Fz", "Cz",
    ],
    "EXG": [
        "EXG1", "EXG2", "EXG3", "EXG4",
        "EXG5", "EXG6", "EXG7", "EXG8",
    ],
    "PERIPHERAL": [
        "GSR1", "Resp", "Plet", "Temp",
    ],
}


RELATIONSHIP_GROUP_PAIRS: list[tuple[str, str]] = [
    ("EEG", "EEG"),
    ("EEG", "EXG"),
    ("EEG", "PERIPHERAL"),
    ("EXG", "EXG"),
    ("EXG", "PERIPHERAL"),
    ("PERIPHERAL", "PERIPHERAL"),
]


def clean_output_directory() -> None:
    """
    Elimina completamente la carpeta de relaciones H2.

    Esto permite regenerar los archivos desde cero y evita mezclar
    resultados antiguos con una nueva configuración del preprocessing.
    """
    if OUTPUT_RELATIONSHIPS_DIR.exists():
        shutil.rmtree(OUTPUT_RELATIONSHIPS_DIR)
        print(f"[INFO] Carpeta eliminada: {OUTPUT_RELATIONSHIPS_DIR}")


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


def safe_pearson_correlation(
    x: np.ndarray,
    y: np.ndarray,
) -> float | None:
    """
    Calcula correlación Pearson entre dos señales.

    Retorna None si alguna señal está vacía, si tienen longitud distinta
    o si alguna de ellas tiene desviación estándar cero.
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


def get_channel_index(
    channels: list[str],
    channel_name: str,
) -> int | None:
    """Devuelve el índice de un canal dentro de la lista de canales."""
    try:
        return channels.index(channel_name)
    except ValueError:
        return None


def extract_during_indices(
    event_info: dict[str, Any],
    times: np.ndarray,
) -> tuple[int, int]:
    """
    Obtiene los índices temporales correspondientes a la fase During.

    Usa:
    - processed_during_start_sec
    - processed_after_start_sec

    Ambos tiempos están expresados en segundos dentro del trial procesado.
    """
    during_start_sec: float = float(event_info["processed_during_start_sec"])
    during_end_sec: float = float(event_info["processed_after_start_sec"])

    start_index: int = int(
        np.searchsorted(times, during_start_sec, side="left")
    )

    end_index: int = int(
        np.searchsorted(times, during_end_sec, side="right")
    )

    return start_index, end_index


def load_trial_npz(
    trial_file: Path,
) -> tuple[np.ndarray, np.ndarray, list[str], float]:
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
    channels: list[str] = [
        str(channel)
        for channel in npz_data["channels"].tolist()
    ]
    sfreq: float = float(npz_data["sfreq"])

    return signals, times, channels, sfreq


def build_channel_signal_map(
    signals: np.ndarray,
    channels: list[str],
    start_index: int,
    end_index: int,
) -> dict[str, np.ndarray]:
    """
    Construye un diccionario canal → señal recortada en During.

    Solo incluye canales presentes en el archivo procesado.
    """
    channel_signal_map: dict[str, np.ndarray] = {}

    for group_channels in CHANNEL_GROUPS.values():
        for channel_name in group_channels:
            channel_index: int | None = get_channel_index(
                channels=channels,
                channel_name=channel_name,
            )

            if channel_index is None:
                continue

            channel_signal_map[channel_name] = signals[
                channel_index,
                start_index:end_index,
            ]

    return channel_signal_map


def build_trial_relationships(
    participant_id: int,
    trial: int,
    trial_file: Path,
    event_info: dict[str, Any],
) -> dict[str, Any]:
    """
    Construye relaciones entre grupos de canales para un trial.

    En esta versión se calculan relaciones durante During para:
    - EEG ↔ PERIPHERAL
    - EXG ↔ PERIPHERAL
    - EEG ↔ EXG

    Cada relación guarda grupo, canal y correlación.
    """
    signals, times, channels, sfreq = load_trial_npz(trial_file)

    during_start_index, during_end_index = extract_during_indices(
        event_info=event_info,
        times=times,
    )

    channel_signal_map: dict[str, np.ndarray] = build_channel_signal_map(
        signals=signals,
        channels=channels,
        start_index=during_start_index,
        end_index=during_end_index,
    )

    relationships: list[dict[str, Any]] = []

    for source_group, target_group in RELATIONSHIP_GROUP_PAIRS:
        source_channels: list[str] = CHANNEL_GROUPS[source_group]
        target_channels: list[str] = CHANNEL_GROUPS[target_group]

        for source_channel in source_channels:
            source_signal: np.ndarray | None = channel_signal_map.get(
                source_channel
            )

            if source_signal is None:
                continue

            for target_channel in target_channels:
                target_signal: np.ndarray | None = channel_signal_map.get(
                    target_channel
                )

                if target_signal is None:
                    continue

                correlation: float | None = safe_pearson_correlation(
                    x=source_signal,
                    y=target_signal,
                )

                relationships.append(
                    {
                        "source_group": source_group,
                        "source_channel": source_channel,
                        "target_group": target_group,
                        "target_channel": target_channel,
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
        "channel_groups": CHANNEL_GROUPS,
        "relationship_group_pairs": RELATIONSHIP_GROUP_PAIRS,
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
        output_file: Path = (
            participant_output_dir
            / f"trial_{trial:02d}_relationships.json"
        )

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


def parse_arguments() -> argparse.Namespace:
    """Define y procesa argumentos de línea de comandos."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Preprocessing H2: relaciones multimodales por grupos."
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Elimina archivos previos antes de regenerar relaciones.",
    )

    return parser.parse_args()


if __name__ == "__main__":
    args: argparse.Namespace = parse_arguments()

    if args.clean:
        clean_output_directory()

    preprocess_all_relationships()

# python -m backend.scripts.preprocess_h2_relationships --clean