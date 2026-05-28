from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import mne
import numpy as np
import pandas as pd

from backend.utils.paths import BDF_DIR, DATASET_DIR, PARTICIPANT_RATINGS_FILE


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

ORIGINAL_SFREQ: float = 512.0
TARGET_SFREQ: float = 128.0
DURING_DURATION_SECONDS: float = 60.0
SPECIAL_RECONSTRUCTED_SUBJECTS: set[int] = {28}

PROCESSED_DIR: Path = DATASET_DIR / "processed"
REPRESENTATION_INPUTS_DIR: Path = PROCESSED_DIR / "representation_inputs"


# ============================================================
# CANALES
# ============================================================

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

EOG_CHANNELS: list[str] = ["EXG1", "EXG2", "EXG3", "EXG4"]
EMG_CHANNELS: list[str] = ["EXG5", "EXG6", "EXG7", "EXG8"]
AUTONOMIC_CHANNELS: list[str] = ["GSR1", "Resp", "Plet", "Temp"]

ALL_SELECTED_CHANNELS: list[str] = (
    EEG_CHANNELS_GENEVA_ORDER
    + EOG_CHANNELS
    + EMG_CHANNELS
    + AUTONOMIC_CHANNELS
)


# ============================================================
# ARGUMENTOS
# ============================================================

def parse_arguments() -> argparse.Namespace:
    """Define los argumentos de línea de comandos del script."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Preprocessing independiente para inputs de representaciones DEAP."
    )

    parser.add_argument(
        "--participants",
        type=str,
        default="all",
        help="Participantes a procesar. Ejemplo: all, 1, 1,2,3",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Elimina solo dataset/processed/representation_inputs antes de procesar.",
    )

    return parser.parse_args()


def parse_participants(value: str) -> list[int]:
    """Convierte el argumento de participantes a una lista de IDs enteros."""
    if value == "all":
        return list(range(1, 33))

    return [int(item.strip()) for item in value.split(",") if item.strip()]


def prepare_output_directory(clean: bool) -> None:
    """Prepara la carpeta de salida sin borrar otros resultados de H1/H2."""
    if clean and REPRESENTATION_INPUTS_DIR.exists():
        shutil.rmtree(REPRESENTATION_INPUTS_DIR)

    REPRESENTATION_INPUTS_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# METADATA
# ============================================================

def load_participant_ratings() -> pd.DataFrame:
    """Carga participant_ratings.xls, usado para metadata y S28."""
    return pd.read_excel(PARTICIPANT_RATINGS_FILE)


def get_subject_ratings(
    ratings_df: pd.DataFrame,
    participant_id: int,
) -> pd.DataFrame:
    """Obtiene los ratings de un participante ordenados por Trial."""
    subject_df: pd.DataFrame = ratings_df[
        ratings_df["Participant_id"] == participant_id
    ].copy()

    subject_df = subject_df.sort_values("Trial").reset_index(drop=True)
    subject_df["start_sec"] = subject_df["Start_time"] / 10000

    return subject_df


def get_trial_metadata(
    ratings_df: pd.DataFrame,
    participant_id: int,
    trial: int,
) -> dict[str, Any]:
    """Obtiene metadata emocional de un trial específico."""
    row_df: pd.DataFrame = ratings_df[
        (ratings_df["Participant_id"] == participant_id)
        & (ratings_df["Trial"] == trial)
    ]

    if row_df.empty:
        raise ValueError(f"No existe metadata para S{participant_id:02d}, trial {trial}")

    row: pd.Series = row_df.iloc[0]

    return {
        "participant_id": int(row["Participant_id"]),
        "trial": int(row["Trial"]),
        "experiment_id": int(row["Experiment_id"]),
        "valence": float(row["Valence"]),
        "arousal": float(row["Arousal"]),
        "dominance": float(row["Dominance"]),
        "liking": float(row["Liking"]),
        "familiarity": None if pd.isna(row["Familiarity"]) else int(row["Familiarity"]),
    }


# ============================================================
# EVENTOS STATUS
# ============================================================

def normalize_event_codes(event_codes: np.ndarray) -> np.ndarray:
    """Normaliza códigos grandes del canal Status a códigos 3, 4, 5, etc."""
    normalized_codes: np.ndarray = event_codes.copy().astype(int)
    mask: np.ndarray = normalized_codes >= 1638144
    normalized_codes[mask] = normalized_codes[mask] - 1638144
    return normalized_codes


def find_status_channel(raw: mne.io.BaseRaw) -> str:
    """Busca automáticamente el canal Status entre los últimos canales."""
    candidate_channels: list[str] = raw.ch_names[-5:]

    for channel_name in candidate_channels:
        try:
            events: np.ndarray = mne.find_events(
                raw,
                stim_channel=channel_name,
                shortest_event=1,
                verbose=False,
            )

            if events.size == 0:
                continue

            normalized_codes: np.ndarray = normalize_event_codes(events[:, 2])
            unique_codes: set[int] = set(normalized_codes.astype(int).tolist())

            if {3, 4, 5}.issubset(unique_codes):
                return channel_name

        except Exception:
            continue

    raise ValueError("No se pudo identificar el canal Status.")


def get_normalized_events(raw: mne.io.BaseRaw) -> np.ndarray:
    """Extrae eventos Status y normaliza sus códigos."""
    status_channel: str = find_status_channel(raw)

    events: np.ndarray = mne.find_events(
        raw,
        stim_channel=status_channel,
        shortest_event=1,
        verbose=False,
    )

    events[:, 2] = normalize_event_codes(events[:, 2])
    return events


def find_trial_events_from_status(raw: mne.io.BaseRaw) -> np.ndarray:
    """Reconstruye los 40 patrones 3→4→5 desde Status."""
    events: np.ndarray = get_normalized_events(raw)
    relevant_events: np.ndarray = events[np.isin(events[:, 2], [3, 4, 5])]

    cleaned_trials: list[np.ndarray] = []
    index: int = 0

    while index <= len(relevant_events) - 3:
        codes: list[int] = [
            int(relevant_events[index][2]),
            int(relevant_events[index + 1][2]),
            int(relevant_events[index + 2][2]),
        ]

        if codes == [3, 4, 5]:
            cleaned_trials.extend(
                [
                    relevant_events[index],
                    relevant_events[index + 1],
                    relevant_events[index + 2],
                ]
            )
            index += 3
        else:
            index += 1

    if len(cleaned_trials) != 120:
        raise ValueError(
            "No se pudieron reconstruir 40 trials desde Status. "
            f"Eventos limpios: {len(cleaned_trials)}."
        )

    return np.array(cleaned_trials)


def estimate_start_time_offset_for_s28(
    raw: mne.io.BaseRaw,
    ratings_df: pd.DataFrame,
) -> float:
    """Estima offset entre Start_time y evento 4 real para S28."""
    events: np.ndarray = get_normalized_events(raw)
    event4_times_sec: np.ndarray = events[events[:, 2] == 4][:, 0] / ORIGINAL_SFREQ

    subject_df: pd.DataFrame = get_subject_ratings(
        ratings_df=ratings_df,
        participant_id=28,
    )

    differences: list[float] = []

    for index in range(min(len(subject_df), len(event4_times_sec))):
        rating_start_sec: float = float(subject_df.iloc[index]["start_sec"])
        event4_sec: float = float(event4_times_sec[index])
        difference_sec: float = event4_sec - rating_start_sec

        if 20.0 <= difference_sec <= 40.0:
            differences.append(difference_sec)

    if not differences:
        raise ValueError("No se pudo estimar offset confiable para S28.")

    return float(np.median(np.array(differences)))


def build_trial_events_from_ratings_for_s28(
    raw: mne.io.BaseRaw,
    ratings_df: pd.DataFrame,
) -> np.ndarray:
    """Reconstruye eventos 3→4→5 para S28 usando participant_ratings."""
    offset_sec: float = estimate_start_time_offset_for_s28(
        raw=raw,
        ratings_df=ratings_df,
    )

    subject_df: pd.DataFrame = get_subject_ratings(
        ratings_df=ratings_df,
        participant_id=28,
    )

    reconstructed_events: list[list[int]] = []

    for _, row in subject_df.iterrows():
        during_start_sec: float = float(row["start_sec"] + offset_sec)
        before_start_sec: float = during_start_sec - 5.0
        after_start_sec: float = during_start_sec + DURING_DURATION_SECONDS

        reconstructed_events.append([int(round(before_start_sec * ORIGINAL_SFREQ)), 0, 3])
        reconstructed_events.append([int(round(during_start_sec * ORIGINAL_SFREQ)), 0, 4])
        reconstructed_events.append([int(round(after_start_sec * ORIGINAL_SFREQ)), 0, 5])

    return np.array(reconstructed_events, dtype=int)


# ============================================================
# CANALES Y TIPOS
# ============================================================

def select_existing_channels(raw: mne.io.BaseRaw) -> list[str]:
    """Selecciona canales existentes manteniendo el orden definido."""
    available_channels: set[str] = set(raw.ch_names)

    return [
        channel
        for channel in ALL_SELECTED_CHANNELS
        if channel in available_channels
    ]


def get_channel_types(channels: list[str]) -> list[str]:
    """Asigna tipos MNE a cada canal seleccionado."""
    channel_types: list[str] = []

    for channel in channels:
        if channel in EEG_CHANNELS_GENEVA_ORDER:
            channel_types.append("eeg")
        elif channel in EOG_CHANNELS:
            channel_types.append("eog")
        elif channel in EMG_CHANNELS:
            channel_types.append("emg")
        else:
            channel_types.append("misc")

    return channel_types


# ============================================================
# PREPROCESSING DE UN TRIAL
# ============================================================
def remove_eog_artifacts_from_eeg(
    trial_raw: mne.io.RawArray,
) -> mne.io.RawArray:
    """
    Elimina artefactos oculares de los canales EEG usando ICA.

    Importante:
    - Solo limpia la actividad EEG contaminada por EOG.
    - No elimina los canales EOG del archivo.
    - Los canales EOG se conservan para extraer características propias
      como blink rate en etapas posteriores.
    """
    eeg_channels: list[str] = [
        channel
        for channel in EEG_CHANNELS_GENEVA_ORDER
        if channel in trial_raw.ch_names
    ]

    eog_channels: list[str] = [
        channel
        for channel in EOG_CHANNELS
        if channel in trial_raw.ch_names
    ]

    if not eeg_channels or not eog_channels:
        return trial_raw

    ica_raw: mne.io.RawArray = trial_raw.copy()

    # ICA necesita una señal razonablemente filtrada para estimar componentes.
    ica_raw.filter(
        l_freq=1.0,
        h_freq=None,
        picks=eeg_channels,
        verbose=False,
    )

    n_components: int = min(15, len(eeg_channels) - 1)

    if n_components < 2:
        return trial_raw

    ica: mne.preprocessing.ICA = mne.preprocessing.ICA(
        n_components=n_components,
        random_state=97,
        max_iter="auto",
        verbose=False,
    )

    ica.fit(
        ica_raw,
        picks=eeg_channels,
        verbose=False,
    )

    eog_indices: list[int] = []

    for eog_channel in eog_channels:
        detected_indices: list[int]
        scores: np.ndarray

        detected_indices, scores = ica.find_bads_eog(
            ica_raw,
            ch_name=eog_channel,
            verbose=False,
        )

        eog_indices.extend(detected_indices)

    unique_eog_indices: list[int] = sorted(set(eog_indices))

    if not unique_eog_indices:
        return trial_raw

    cleaned_raw: mne.io.RawArray = trial_raw.copy()
    ica.exclude = unique_eog_indices

    ica.apply(
        cleaned_raw,
        exclude=unique_eog_indices,
        verbose=False,
    )

    return cleaned_raw


def preprocess_during_trial(
    raw: mne.io.BaseRaw,
    selected_channels: list[str],
    during_start_sample_512: int,
    during_end_sample_512: int,
) -> tuple[np.ndarray, np.ndarray, list[str], float]:
    """
    Extrae y preprocesa únicamente la fase During.

    Flujo oficial para esta etapa:
    1. Extraer 60 segundos de During desde el archivo BDF original.
    2. Crear un RawArray temporal con los 44 canales seleccionados.
    3. Remover artefactos EOG de los canales EEG mediante ICA.
    4. Aplicar filtro bandpass 4–45 Hz solo a canales EEG.
    5. Remuestrear todas las señales a 128 Hz.
    6. Retornar señales listas para feature vectors o embeddings DL.

    Importante:
    - EOG no se elimina como modalidad.
    - EOG solo se usa como referencia para limpiar EEG.
    - EOG, EMG y periféricas no reciben el filtro EEG 4–45 Hz.
    """
    trial_data_512, _ = raw.get_data(
        picks=selected_channels,
        start=during_start_sample_512,
        stop=during_end_sample_512,
        return_times=True,
    )

    trial_info: mne.Info = mne.create_info(
        ch_names=selected_channels,
        sfreq=ORIGINAL_SFREQ,
        ch_types=get_channel_types(selected_channels),
    )

    trial_raw: mne.io.RawArray = mne.io.RawArray(
        data=trial_data_512,
        info=trial_info,
        verbose=False,
    )

    trial_raw = remove_eog_artifacts_from_eeg(trial_raw=trial_raw)

    eeg_existing_channels: list[str] = [
        channel
        for channel in EEG_CHANNELS_GENEVA_ORDER
        if channel in trial_raw.ch_names
    ]

    if eeg_existing_channels:
        trial_raw.filter(
            l_freq=4.0,
            h_freq=45.0,
            picks=eeg_existing_channels,
            verbose=False,
        )

    trial_raw.resample(
        sfreq=TARGET_SFREQ,
        npad="auto",
        verbose=False,
    )

    signals: np.ndarray
    times: np.ndarray
    signals, times = trial_raw.get_data(return_times=True)

    relative_times: np.ndarray = times - times[0]

    return signals, relative_times, list(trial_raw.ch_names), TARGET_SFREQ


# ============================================================
# PROCESAMIENTO POR PARTICIPANTE
# ============================================================

def preprocess_participant_representation_inputs(
    participant_id: int,
    ratings_df: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Procesa los 40 trials de un participante desde su archivo BDF."""
    print(f"[INFO] Procesando representation inputs para S{participant_id:02d}")

    bdf_path: Path = BDF_DIR / f"s{participant_id:02d}.bdf"

    if not bdf_path.exists():
        raise FileNotFoundError(f"No existe el archivo BDF: {bdf_path}")

    raw: mne.io.BaseRaw = mne.io.read_raw_bdf(
        bdf_path,
        preload=True,
        verbose=False,
    )

    if participant_id in SPECIAL_RECONSTRUCTED_SUBJECTS:
        trial_events: np.ndarray = build_trial_events_from_ratings_for_s28(
            raw=raw,
            ratings_df=ratings_df,
        )
        event_source: str = "participant_ratings_reconstructed"
    else:
        trial_events = find_trial_events_from_status(raw)
        event_source = "status"

    selected_channels: list[str] = select_existing_channels(raw)
    participant_output_dir: Path = REPRESENTATION_INPUTS_DIR / f"s{participant_id:02d}"
    participant_output_dir.mkdir(parents=True, exist_ok=True)

    metadata_rows: list[dict[str, Any]] = []

    for trial in range(1, 41):
        expected_index: int = (trial - 1) * 3

        during_event: np.ndarray = trial_events[expected_index + 1]

        during_start_sample_512: int = int(during_event[0])
        during_end_sample_512: int = (
            during_start_sample_512
            + int(DURING_DURATION_SECONDS * ORIGINAL_SFREQ)
        )

        signals, times, channels, sfreq = preprocess_during_trial(
            raw=raw,
            selected_channels=selected_channels,
            during_start_sample_512=during_start_sample_512,
            during_end_sample_512=during_end_sample_512,
        )

        metadata: dict[str, Any] = get_trial_metadata(
            ratings_df=ratings_df,
            participant_id=participant_id,
            trial=trial,
        )

        output_path: Path = participant_output_dir / f"trial_{trial:02d}_input.npz"

        np.savez_compressed(
            output_path,
            signals=signals,
            times=times,
            channels=np.array(channels),
            sfreq=np.array([sfreq]),
            participant_id=np.array([participant_id]),
            trial=np.array([trial]),
            experiment_id=np.array([metadata["experiment_id"]]),
        )

        expected_samples: int = int(round(DURING_DURATION_SECONDS * sfreq))
        actual_samples: int = int(signals.shape[1])
        duration_sec: float = float(actual_samples / sfreq)
        is_complete: bool = actual_samples == expected_samples

        metadata_rows.append(
            {
                **metadata,
                "event_source": event_source,
                "sfreq": sfreq,
                "num_channels": int(signals.shape[0]),
                "num_samples": actual_samples,
                "expected_samples": expected_samples,
                "duration_sec": duration_sec,
                "expected_duration_sec": DURING_DURATION_SECONDS,
                "is_complete": is_complete,
                "representation_input_npz": str(output_path.relative_to(DATASET_DIR)),
            }
        )

        print(f"[OK] Guardado: {output_path}")

    return metadata_rows


# ============================================================
# MAIN
# ============================================================

def save_global_metadata(metadata_rows: list[dict[str, Any]]) -> None:
    """Guarda un CSV global con metadata de todos los trials procesados."""
    metadata_df: pd.DataFrame = pd.DataFrame(metadata_rows)
    metadata_path: Path = REPRESENTATION_INPUTS_DIR / "representation_metadata.csv"
    metadata_df.to_csv(metadata_path, index=False)
    print(f"[OK] Metadata global guardada: {metadata_path}")


def main() -> None:
    """Ejecuta el preprocessing completo de inputs para representaciones."""
    args: argparse.Namespace = parse_arguments()

    prepare_output_directory(clean=args.clean)

    participants: list[int] = parse_participants(args.participants)
    ratings_df: pd.DataFrame = load_participant_ratings()

    all_metadata_rows: list[dict[str, Any]] = []

    for participant_id in participants:
        participant_rows: list[dict[str, Any]] = (
            preprocess_participant_representation_inputs(
                participant_id=participant_id,
                ratings_df=ratings_df,
            )
        )
        all_metadata_rows.extend(participant_rows)

    save_global_metadata(metadata_rows=all_metadata_rows)


if __name__ == "__main__":
    main()


# ============================================================
# USO
# ============================================================
# Procesar un participante:
# python -m backend.scripts.preprocess_representation_inputs --participants 1 --clean
#
# Procesar varios:
# python -m backend.scripts.preprocess_representation_inputs --participants 1,2,3 --clean
#
# Procesar todos:
# python -m backend.scripts.preprocess_representation_inputs --participants all --clean