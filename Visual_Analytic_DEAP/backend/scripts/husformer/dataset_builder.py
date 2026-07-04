from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.utils.paths import DATASET_DIR

from . import config
from .channel_modalities import split_window_into_modalities
from .labeling import valence_to_label
from .participant_split import get_participant_split
from .windowing import generate_trial_windows


def load_global_metadata() -> pd.DataFrame:
    """
    Carga el CSV global de metadata generado por preprocess_representation_inputs.py.

    Este CSV ya contiene, por cada uno de los 1280 trials (32 participantes x
    40 trials), la ruta al .npz correspondiente y las etiquetas afectivas
    (valencia, activación, dominancia, liking), evitando tener que releer
    participant_ratings.xls.
    """
    if not config.REPRESENTATION_METADATA_FILE.exists():
        raise FileNotFoundError(
            "No existe el CSV de metadata global: "
            f"{config.REPRESENTATION_METADATA_FILE}. Corre primero: "
            "python -m backend.scripts.preprocess_representation_inputs --participants all"
        )

    return pd.read_csv(config.REPRESENTATION_METADATA_FILE)


def load_trial_signal(metadata_row: pd.Series) -> tuple[np.ndarray, list[str], float]:
    """
    Carga las señales, nombres de canal y frecuencia de muestreo de un trial.

    Usa la ruta relativa guardada en la columna 'representation_input_npz' del
    CSV global, resuelta contra DATASET_DIR.
    """
    npz_path: Path = DATASET_DIR / metadata_row["representation_input_npz"]

    if not npz_path.exists():
        raise FileNotFoundError(f"No existe el .npz esperado: {npz_path}")

    npz_data: Any = np.load(npz_path, allow_pickle=True)

    signals: np.ndarray = np.asarray(npz_data["signals"])
    channel_names: list[str] = [str(name) for name in npz_data["channels"].tolist()]
    sfreq: float = float(npz_data["sfreq"][0])

    return signals, channel_names, sfreq


def process_trial(
    metadata_row: pd.Series,
    split_containers: dict[str, dict[str, list[np.ndarray]]],
    manifest_rows: list[dict[str, Any]],
    global_window_counter: list[int],
) -> None:
    """
    Procesa un trial completo: ventanea, separa en modalidades, etiqueta y
    acumula el resultado en las estructuras compartidas del pipeline.

    Modifica en el lugar (in-place), no retorna nada:
    - split_containers: agrega las ventanas de este trial a las listas del
      split correspondiente (train/valid/test) — una lista por modalidad más
      'label'.
    - manifest_rows: agrega una fila de trazabilidad por cada ventana generada.
    - global_window_counter: contador mutable de un solo elemento (lista de 1
      entero), usado para asignar 'global_window_id' consecutivos entre
      trials distintos.
    """
    participant_id: int = int(metadata_row["participant_id"])
    trial: int = int(metadata_row["trial"])
    valence: float = float(metadata_row["valence"])
    arousal: float = float(metadata_row["arousal"])
    dominance: float = float(metadata_row["dominance"])
    liking: float = float(metadata_row["liking"])

    split_name: str = get_participant_split(participant_id)
    label: int = valence_to_label(valence)

    signals, channel_names, sfreq = load_trial_signal(metadata_row)

    windows, window_start_seconds = generate_trial_windows(
        signals=signals,
        sfreq=sfreq,
        window_seconds=config.WINDOW_SECONDS,
    )

    split_container: dict[str, list[np.ndarray]] = split_containers[split_name]

    for window_index in range(windows.shape[0]):
        window: np.ndarray = windows[window_index]

        modalities: dict[str, np.ndarray] = split_window_into_modalities(
            window=window,
            channel_names=channel_names,
            channel_groups=config.MODALITY_CHANNEL_GROUPS,
        )

        local_id: int = len(split_container["label"])

        for modality_name, modality_data in modalities.items():
            split_container[modality_name].append(modality_data)

        split_container["label"].append(np.array(label, dtype=np.float32))

        manifest_rows.append(
            {
                "global_window_id": global_window_counter[0],
                "local_id": local_id,
                "split": split_name,
                "participant_id": participant_id,
                "trial": trial,
                "window_index": window_index,
                "window_start_sec": float(window_start_seconds[window_index]),
                "valence": valence,
                "arousal": arousal,
                "dominance": dominance,
                "liking": liking,
            }
        )

        global_window_counter[0] += 1


def build_full_dataset(
    participants_to_process: list[int] | None = None,
) -> tuple[dict[str, dict[str, np.ndarray]], list[dict[str, Any]]]:
    """
    Construye la estructura completa de Husformer.pkl y las filas del manifest.

    Recorre los trials listados en el CSV global de metadata (1280 en total
    si participants_to_process es None), generando ventanas de 1 segundo
    repartidas en los splits train/valid/test según el participante (ver
    config.PARTICIPANT_SPLIT).

    Parámetros:
    - participants_to_process: si se da, solo se procesan los trials de estos
      participantes (útil para una corrida de prueba rápida). Si es None, se
      procesan los 32 participantes.

    Retorna una tupla (dataset_dict, manifest_rows):
    - dataset_dict: {'train': {...}, 'valid': {...}, 'test': {...}}, cada uno
      con claves 'modality_1'..'modality_5' (shape (N, muestras, canales)),
      'label' (shape (N,1,1)) e 'id' (shape (N,1,1)).
    - manifest_rows: lista de diccionarios, una fila por ventana generada.
    """
    global_metadata: pd.DataFrame = load_global_metadata()

    if participants_to_process is not None:
        global_metadata = global_metadata[
            global_metadata["participant_id"].isin(participants_to_process)
        ].reset_index(drop=True)

        if global_metadata.empty:
            raise ValueError(
                "Ningún trial coincide con los participantes solicitados: "
                f"{participants_to_process}."
            )

    modality_names: list[str] = list(config.MODALITY_CHANNEL_GROUPS.keys())

    split_containers: dict[str, dict[str, list[np.ndarray]]] = {}

    for split_name in ("train", "valid", "test"):
        container: dict[str, list[np.ndarray]] = {
            modality_name: [] for modality_name in modality_names
        }
        container["label"] = []
        split_containers[split_name] = container

    manifest_rows: list[dict[str, Any]] = []
    global_window_counter: list[int] = [0]

    total_trials: int = len(global_metadata)

    for row_position, (_, metadata_row) in enumerate(global_metadata.iterrows(), start=1):
        print(
            f"[INFO] Procesando trial {row_position}/{total_trials} "
            f"(S{int(metadata_row['participant_id']):02d}, "
            f"trial {int(metadata_row['trial']):02d})"
        )

        process_trial(
            metadata_row=metadata_row,
            split_containers=split_containers,
            manifest_rows=manifest_rows,
            global_window_counter=global_window_counter,
        )

    dataset_dict: dict[str, dict[str, np.ndarray]] = {}

    for split_name, container in split_containers.items():
        n_windows_in_split: int = len(container["label"])

        if n_windows_in_split == 0:
            raise ValueError(
                f"El split '{split_name}' quedó sin ventanas. Si estás probando "
                "con un subconjunto de participantes (--participants), asegúrate "
                "de incluir al menos uno de cada split "
                "(ver config.PARTICIPANT_SPLIT)."
            )

        split_data: dict[str, np.ndarray] = {}

        for modality_name in modality_names:
            split_data[modality_name] = np.stack(
                container[modality_name], axis=0
            ).astype(np.float32)

        split_data["label"] = np.array(
            container["label"], dtype=np.float32
        ).reshape(n_windows_in_split, 1, 1)

        split_data["id"] = np.arange(n_windows_in_split).reshape(
            n_windows_in_split, 1, 1
        )

        dataset_dict[split_name] = split_data

        print(f"[OK] Split '{split_name}': {n_windows_in_split} ventanas")

    return dataset_dict, manifest_rows


def save_pkl(dataset_dict: dict[str, dict[str, np.ndarray]], output_path: Path) -> None:
    """Guarda la estructura final como Husformer.pkl (formato que espera dataset.py)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("wb") as pkl_file:
        pickle.dump(dataset_dict, pkl_file)

    print(f"[OK] Husformer.pkl guardado en: {output_path}")
