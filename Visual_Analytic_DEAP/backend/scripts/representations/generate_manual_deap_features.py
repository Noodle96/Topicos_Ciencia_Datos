from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.utils.paths import DATASET_DIR
from backend.scripts.representations.eeg_features import extract_all_eeg_features
from backend.scripts.representations.feature_utils import (
    load_representation_input_npz,
    validate_feature_vector,
)
from backend.scripts.representations.physiological_features import (
    extract_all_physiological_features,
)


REPRESENTATION_INPUTS_DIR: Path = DATASET_DIR / "processed" / "representation_inputs"

OUTPUT_DIR: Path = (
    DATASET_DIR
    / "processed"
    / "representations"
    / "manual_deap_features"
)

METADATA_FILE: Path = REPRESENTATION_INPUTS_DIR / "representation_metadata.csv"


def parse_arguments() -> argparse.Namespace:
    """Define argumentos de línea de comandos."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Genera vectores de características manuales basados en DEAP."
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Elimina la carpeta de salida antes de generar features.",
    )

    parser.add_argument(
        "--include-incomplete",
        action="store_true",
        help="Incluye trials incompletos. Por defecto se excluyen.",
    )

    return parser.parse_args()


def prepare_output_directory(clean: bool) -> None:
    """Prepara carpeta de salida."""
    if clean and OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_representation_metadata() -> pd.DataFrame:
    """Carga metadata generada por preprocess_representation_inputs.py."""
    if not METADATA_FILE.exists():
        raise FileNotFoundError(f"No existe metadata: {METADATA_FILE}")

    metadata_df: pd.DataFrame = pd.read_csv(METADATA_FILE)
    return metadata_df


def build_trial_feature_vector(
    npz_path: Path,
) -> tuple[list[float], list[str], dict[str, Any]]:
    """
    Construye el vector de características de un trial.

    Flujo:
    1. Cargar .npz.
    2. Extraer EEG features.
    3. Extraer physiological features.
    4. Concatenar ambos bloques.
    """
    (
        signals,
        times,
        channels,
        sfreq,
        participant_id,
        trial,
        experiment_id,
    ) = load_representation_input_npz(npz_path=npz_path)

    eeg_values, eeg_names = extract_all_eeg_features(
        signals=signals,
        channels=channels,
        sfreq=sfreq,
    )

    physiological_values, physiological_names = extract_all_physiological_features(
        signals=signals,
        channels=channels,
        sfreq=sfreq,
    )

    feature_values: list[float] = eeg_values + physiological_values
    feature_names: list[str] = eeg_names + physiological_names

    validate_feature_vector(
        feature_values=feature_values,
        feature_names=feature_names,
    )

    trial_info: dict[str, Any] = {
        "participant_id": participant_id,
        "trial": trial,
        "experiment_id": experiment_id,
        "sfreq": sfreq,
        "num_channels": int(signals.shape[0]),
        "num_samples": int(signals.shape[1]),
        "duration_sec": float(signals.shape[1] / sfreq),
    }

    return feature_values, feature_names, trial_info


def generate_features(include_incomplete: bool) -> None:
    """
    Genera la matriz completa X_features.

    Cada fila representa un trial.
    Cada columna representa una característica fisiológica/EEG.
    """
    metadata_df: pd.DataFrame = load_representation_metadata()

    if not include_incomplete and "is_complete" in metadata_df.columns:
        metadata_df = metadata_df[metadata_df["is_complete"] == True].copy()

    all_feature_vectors: list[list[float]] = []
    output_metadata_rows: list[dict[str, Any]] = []
    reference_feature_names: list[str] | None = None

    for _, row in metadata_df.iterrows():
        relative_npz_path: str = str(row["representation_input_npz"])
        npz_path: Path = DATASET_DIR / relative_npz_path

        feature_values, feature_names, trial_info = build_trial_feature_vector(
            npz_path=npz_path,
        )

        if reference_feature_names is None:
            reference_feature_names = feature_names
        elif reference_feature_names != feature_names:
            raise ValueError(
                "Los nombres de features no coinciden entre trials. "
                f"Problema en: {npz_path}"
            )

        all_feature_vectors.append(feature_values)

        output_metadata_rows.append(
            {
                **row.to_dict(),
                **trial_info,
            }
        )

        print(
            "[OK] Features generadas:",
            f"S{int(trial_info['participant_id']):02d}",
            f"trial_{int(trial_info['trial']):02d}",
            f"features={len(feature_values)}",
        )

    if reference_feature_names is None:
        raise ValueError("No se generó ningún vector de características.")

    X_features: np.ndarray = np.asarray(all_feature_vectors, dtype=np.float64)

    np.save(OUTPUT_DIR / "X_features.npy", X_features)

    with (OUTPUT_DIR / "feature_names.json").open("w", encoding="utf-8") as file:
        json.dump(reference_feature_names, file, indent=2, ensure_ascii=False)

    output_metadata_df: pd.DataFrame = pd.DataFrame(output_metadata_rows)
    output_metadata_df.to_csv(OUTPUT_DIR / "trial_metadata.csv", index=False)

    feature_config: dict[str, Any] = {
        "representation_type": "manual_deap_features",
        "description": (
            "Feature vectors based on EEG spectral power/asymmetry and "
            "available physiological features inspired by DEAP Section 6.1/Table 5."
        ),
        "num_trials": int(X_features.shape[0]),
        "num_features": int(X_features.shape[1]),
        "eeg_features_expected": 216,
        "physiological_features": int(X_features.shape[1] - 216),
        "include_incomplete": include_incomplete,
        "dtype": str(X_features.dtype),
    }

    with (OUTPUT_DIR / "feature_config.json").open("w", encoding="utf-8") as file:
        json.dump(feature_config, file, indent=2, ensure_ascii=False)

    print("\n[OK] X_features:", X_features.shape)
    print("[OK] Guardado en:", OUTPUT_DIR)


def main() -> None:
    """Punto de entrada principal."""
    args: argparse.Namespace = parse_arguments()

    prepare_output_directory(clean=args.clean)

    generate_features(
        include_incomplete=args.include_incomplete,
    )


if __name__ == "__main__":
    main()


# USO:
# python -m backend.scripts.representations.generate_manual_deap_features --clean
#
# Si deseas incluir trials incompletos:
# python -m backend.scripts.representations.generate_manual_deap_features --clean --include-incomplete