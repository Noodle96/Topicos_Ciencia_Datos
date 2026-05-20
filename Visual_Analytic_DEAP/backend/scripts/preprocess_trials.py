from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict

import mne
import numpy as np
import pandas as pd

from backend.utils.paths import BDF_DIR, DATASET_DIR, PARTICIPANT_RATINGS_FILE


ORIGINAL_SFREQ: float = 512.0
TARGET_SFREQ: float = 128.0
AFTER_DURATION_SECONDS: float = 3.0
SPECIAL_RECONSTRUCTED_SUBJECTS: set[int] = {28}

EEG_CHANNELS_GENEVA_ORDER: list[str] = [
    "Fp1", "AF3", "F3", "F7", "FC5", "FC1", "C3", "T7",
    "CP5", "CP1", "P3", "P7", "PO3", "O1", "Oz", "Pz",
    "O2", "PO4", "P4", "P8", "CP6", "CP2", "FC6", "FC2",
    "C4", "T8", "F4", "F8", "AF4", "Fp2", "Fz", "Cz",
]

PERIPHERAL_CHANNELS: list[str] = [
    "EXG1", "EXG2", "EXG3", "EXG4",
    "EXG5", "EXG6", "EXG7", "EXG8",
    "GSR1", "Resp", "Plet", "Temp",
]

ALL_SELECTED_CHANNELS: list[str] = EEG_CHANNELS_GENEVA_ORDER + PERIPHERAL_CHANNELS

PROCESSED_DIR: Path = DATASET_DIR / "processed"
TRIALS_DIR: Path = PROCESSED_DIR / "trials"
EVENTS_DIR: Path = PROCESSED_DIR / "events"
METRICS_DIR: Path = PROCESSED_DIR / "metrics"


def parse_arguments() -> argparse.Namespace:
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Offline preprocessing for DEAP trials."
    )
    parser.add_argument("--participants", type=str, default="all")
    parser.add_argument("--clean", action="store_true")
    return parser.parse_args()


def prepare_output_directories(clean: bool) -> None:
    if clean and PROCESSED_DIR.exists():
        shutil.rmtree(PROCESSED_DIR)

    TRIALS_DIR.mkdir(parents=True, exist_ok=True)
    EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)


def parse_participants(value: str) -> list[int]:
    if value == "all":
        return list(range(1, 33))

    return [int(item.strip()) for item in value.split(",") if item.strip()]


def build_bdf_path(participant_id: int) -> Path:
    return BDF_DIR / f"s{participant_id:02d}.bdf"


def normalize_event_codes(event_codes: np.ndarray) -> np.ndarray:
    normalized_codes: np.ndarray = event_codes.copy().astype(int)
    mask: np.ndarray = normalized_codes >= 1638144
    normalized_codes[mask] = normalized_codes[mask] - 1638144
    return normalized_codes


def find_status_channel(raw: mne.io.BaseRaw) -> str:
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
            f"Eventos limpios: {len(cleaned_trials)}. "
            f"Eventos relevantes: {len(relevant_events)}."
        )

    return np.array(cleaned_trials)


def load_participant_ratings() -> pd.DataFrame:
    return pd.read_excel(PARTICIPANT_RATINGS_FILE)


def get_subject_ratings(
    ratings_df: pd.DataFrame,
    participant_id: int,
) -> pd.DataFrame:
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
) -> Dict[str, Any]:
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


def estimate_start_time_offset_for_s28(
    raw: mne.io.BaseRaw,
    ratings_df: pd.DataFrame,
) -> float:
    """
    Estima offset entre participant_ratings.Start_time y evento 4 real.

    Para S28, los primeros eventos 4 son consistentes. Usamos diferencias
    razonables entre 20s y 40s y tomamos la mediana.
    """
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
    """
    Reconstruye 40 trials para S28 usando participant_ratings.Start_time.

    Start_time indica inicio de video playback. Por tanto:
    event 4 = Start_time + offset
    event 3 = event 4 - 5s
    event 5 = event 4 + 60s
    """
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
        after_start_sec: float = during_start_sec + 60.0

        reconstructed_events.append(
            [int(round(before_start_sec * ORIGINAL_SFREQ)), 0, 3]
        )
        reconstructed_events.append(
            [int(round(during_start_sec * ORIGINAL_SFREQ)), 0, 4]
        )
        reconstructed_events.append(
            [int(round(after_start_sec * ORIGINAL_SFREQ)), 0, 5]
        )

    if len(reconstructed_events) != 120:
        raise ValueError("S28 reconstruido no produjo 120 eventos.")

    return np.array(reconstructed_events, dtype=int)


def select_existing_channels(raw: mne.io.BaseRaw) -> list[str]:
    available_channels: set[str] = set(raw.ch_names)

    return [
        channel
        for channel in ALL_SELECTED_CHANNELS
        if channel in available_channels
    ]


def get_channel_types(channels: list[str]) -> list[str]:
    channel_types: list[str] = []

    for channel in channels:
        if channel in EEG_CHANNELS_GENEVA_ORDER:
            channel_types.append("eeg")
        elif channel in {"EXG1", "EXG2", "EXG3", "EXG4"}:
            channel_types.append("eog")
        elif channel in {"EXG5", "EXG6", "EXG7", "EXG8"}:
            channel_types.append("emg")
        else:
            channel_types.append("misc")

    return channel_types


def compute_phase_metrics(values: np.ndarray) -> Dict[str, float | None]:
    if values.size == 0 or np.all(np.isnan(values)):
        return {
            "mean": None,
            "std": None,
            "rms": None,
            "min": None,
            "max": None,
        }

    return {
        "mean": float(np.nanmean(values)),
        "std": float(np.nanstd(values)),
        "rms": float(np.sqrt(np.nanmean(values ** 2))),
        "min": float(np.nanmin(values)),
        "max": float(np.nanmax(values)),
    }


def compute_metrics_by_phase(
    channel_values: np.ndarray,
    sfreq: float,
    phases: dict[str, dict[str, float]],
) -> Dict[str, Dict[str, float | None]]:
    metrics_by_phase: Dict[str, Dict[str, float | None]] = {}

    for phase_name, phase_info in phases.items():
        start_index: int = int(round(phase_info["start"] * sfreq))
        end_index: int = int(round(phase_info["end"] * sfreq))

        phase_values: np.ndarray = channel_values[start_index:end_index]

        metrics_by_phase[phase_name] = compute_phase_metrics(phase_values)

    return metrics_by_phase


def preprocess_participant(
    participant_id: int,
    ratings_df: pd.DataFrame,
) -> None:
    print(f"[INFO] Procesando S{participant_id:02d}")

    bdf_path: Path = build_bdf_path(participant_id)

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

    participant_trials_dir: Path = TRIALS_DIR / f"s{participant_id:02d}"
    participant_metrics_dir: Path = METRICS_DIR / f"s{participant_id:02d}"

    participant_trials_dir.mkdir(parents=True, exist_ok=True)
    participant_metrics_dir.mkdir(parents=True, exist_ok=True)

    events_metadata: Dict[str, Any] = {
        "participant_id": participant_id,
        "sfreq_original": ORIGINAL_SFREQ,
        "sfreq_processed": TARGET_SFREQ,
        "channels": selected_channels,
        "event_source": event_source,
        "trials": [],
    }

    for trial in range(1, 41):
        expected_index: int = (trial - 1) * 3

        before_event: np.ndarray = trial_events[expected_index]
        during_event: np.ndarray = trial_events[expected_index + 1]
        after_event: np.ndarray = trial_events[expected_index + 2]

        before_start_sample_512: int = int(before_event[0])
        during_start_sample_512: int = int(during_event[0])
        after_start_sample_512: int = int(after_event[0])

        after_end_sample_512: int = (
            after_start_sample_512 + int(AFTER_DURATION_SECONDS * ORIGINAL_SFREQ)
        )

        before_duration_sec: float = (
            during_start_sample_512 - before_start_sample_512
        ) / ORIGINAL_SFREQ
        during_duration_sec: float = (
            after_start_sample_512 - during_start_sample_512
        ) / ORIGINAL_SFREQ
        after_duration_sec: float = AFTER_DURATION_SECONDS
        trial_duration_sec: float = (
            after_end_sample_512 - before_start_sample_512
        ) / ORIGINAL_SFREQ

        phases: dict[str, dict[str, float]] = {
            "Before": {"start": 0.0, "end": before_duration_sec},
            "During": {
                "start": before_duration_sec,
                "end": before_duration_sec + during_duration_sec,
            },
            "After": {
                "start": before_duration_sec + during_duration_sec,
                "end": trial_duration_sec,
            },
        }

        trial_data_512, _ = raw.get_data(
            picks=selected_channels,
            start=before_start_sample_512,
            stop=after_end_sample_512,
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

        trial_data, trial_times = trial_raw.get_data(return_times=True)
        relative_times: np.ndarray = trial_times - trial_times[0]

        trial_npz_path: Path = participant_trials_dir / f"trial_{trial:02d}.npz"

        np.savez_compressed(
            trial_npz_path,
            signals=trial_data,
            times=relative_times,
            channels=np.array(trial_raw.ch_names),
            sfreq=np.array([TARGET_SFREQ]),
        )

        metadata: Dict[str, Any] = get_trial_metadata(
            ratings_df=ratings_df,
            participant_id=participant_id,
            trial=trial,
        )

        metrics: Dict[str, Any] = {
            "participant_id": participant_id,
            "trial": trial,
            "experiment_id": metadata["experiment_id"],
            "metrics": {},
        }

        for channel_index, channel_name in enumerate(trial_raw.ch_names):
            metrics["metrics"][channel_name] = compute_metrics_by_phase(
                channel_values=trial_data[channel_index],
                sfreq=TARGET_SFREQ,
                phases=phases,
            )

        metrics_path: Path = (
            participant_metrics_dir / f"trial_{trial:02d}_metrics.json"
        )

        with metrics_path.open("w", encoding="utf-8") as file:
            json.dump(metrics, file, indent=2)

        events_metadata["trials"].append(
            {
                **metadata,
                "event_source": event_source,
                "before_start_sample_512": before_start_sample_512,
                "during_start_sample_512": during_start_sample_512,
                "after_start_sample_512": after_start_sample_512,
                "after_end_sample_512": after_end_sample_512,
                "before_duration_sec": before_duration_sec,
                "during_duration_sec": during_duration_sec,
                "after_duration_sec": after_duration_sec,
                "trial_duration_sec": trial_duration_sec,
                "processed_before_start_sec": phases["Before"]["start"],
                "processed_during_start_sec": phases["During"]["start"],
                "processed_after_start_sec": phases["After"]["start"],
                "processed_end_sec": phases["After"]["end"],
                "actual_samples": int(trial_data.shape[1]),
                "phases": phases,
                "trial_npz": str(trial_npz_path.relative_to(DATASET_DIR)),
                "metrics_json": str(metrics_path.relative_to(DATASET_DIR)),
            }
        )

    events_path: Path = EVENTS_DIR / f"s{participant_id:02d}_events.json"

    with events_path.open("w", encoding="utf-8") as file:
        json.dump(events_metadata, file, indent=2)

    print(f"[OK] S{participant_id:02d} procesado correctamente")


def main() -> None:
    args: argparse.Namespace = parse_arguments()

    prepare_output_directories(clean=args.clean)

    participants: list[int] = parse_participants(args.participants)
    ratings_df: pd.DataFrame = load_participant_ratings()

    for participant_id in participants:
        preprocess_participant(
            participant_id=participant_id,
            ratings_df=ratings_df,
        )


if __name__ == "__main__":
    main()
# python -m backend.scripts.preprocess_trials --participants 1 --clean
# python -m backend.scripts.preprocess_trials --participants 1,2,3 --clean
# python -m backend.scripts.preprocess_trials --participants all --clean
# --clean elimina:
# dataset/processed/




# hacer:
# python -m backend.scripts.preprocess_trials --participants all --clean