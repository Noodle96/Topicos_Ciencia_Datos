from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.preprocessing import StandardScaler

from backend.utils.paths import DATASET_DIR


FEATURE_DIR: Path = (
    DATASET_DIR
    / "processed"
    / "representations"
    / "manual_deap_features"
)

X_FEATURES_PATH: Path = FEATURE_DIR / "X_features.npy"
X_STANDARDIZED_PATH: Path = FEATURE_DIR / "X_features_standardized.npy"
NORMALIZATION_METADATA_PATH: Path = FEATURE_DIR / "normalization_metadata.json"


def parse_arguments() -> argparse.Namespace:
    """Define argumentos de línea de comandos."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Normaliza X_features usando StandardScaler."
    )

    return parser.parse_args()


def load_features() -> np.ndarray:
    """Carga la matriz original de características."""
    if not X_FEATURES_PATH.exists():
        raise FileNotFoundError(f"No existe: {X_FEATURES_PATH}")

    X_features: np.ndarray = np.load(X_FEATURES_PATH)

    if X_features.ndim != 2:
        raise ValueError(
            f"X_features debe ser 2D, pero tiene shape {X_features.shape}"
        )

    return X_features


def validate_features(X_features: np.ndarray) -> None:
    """
    Verifica que la matriz no tenga NaN ni Inf.

    PCA, UMAP y t-SNE no deben recibir valores inválidos.
    """
    num_nan: int = int(np.isnan(X_features).sum())
    num_inf: int = int(np.isinf(X_features).sum())

    if num_nan > 0 or num_inf > 0:
        raise ValueError(
            "X_features contiene valores inválidos: "
            f"NaN={num_nan}, Inf={num_inf}"
        )


def standardize_features(X_features: np.ndarray) -> tuple[np.ndarray, StandardScaler]:
    """
    Aplica StandardScaler.

    Para cada feature:
    z = (x - mean) / std

    Esto evita que features con escalas grandes dominen PCA/UMAP/t-SNE.
    """
    scaler: StandardScaler = StandardScaler()

    X_standardized: np.ndarray = scaler.fit_transform(X_features)

    return X_standardized, scaler


def save_outputs(
    X_features: np.ndarray,
    X_standardized: np.ndarray,
    scaler: StandardScaler,
) -> None:
    """Guarda matriz normalizada y metadata de normalización."""
    np.save(X_STANDARDIZED_PATH, X_standardized)

    metadata: dict[str, Any] = {
        "normalization_method": "StandardScaler",
        "description": "z = (x - mean) / std applied feature-wise.",
        "input_file": str(X_FEATURES_PATH.relative_to(DATASET_DIR)),
        "output_file": str(X_STANDARDIZED_PATH.relative_to(DATASET_DIR)),
        "input_shape": list(X_features.shape),
        "output_shape": list(X_standardized.shape),
        "input_dtype": str(X_features.dtype),
        "output_dtype": str(X_standardized.dtype),
        "mean_shape": list(scaler.mean_.shape),
        "scale_shape": list(scaler.scale_.shape),
        "global_mean_after_standardization": float(np.mean(X_standardized)),
        "global_std_after_standardization": float(np.std(X_standardized)),
    }

    with NORMALIZATION_METADATA_PATH.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, ensure_ascii=False)

    print("[OK] Guardado:", X_STANDARDIZED_PATH)
    print("[OK] Metadata:", NORMALIZATION_METADATA_PATH)
    print("[OK] X_standardized shape:", X_standardized.shape)


def main() -> None:
    """Ejecuta la normalización completa."""
    parse_arguments()

    X_features: np.ndarray = load_features()

    validate_features(X_features=X_features)

    X_standardized, scaler = standardize_features(X_features=X_features)

    save_outputs(
        X_features=X_features,
        X_standardized=X_standardized,
        scaler=scaler,
    )


if __name__ == "__main__":
    main()


# USO:
# python -m backend.scripts.representations.normalize_manual_deap_features