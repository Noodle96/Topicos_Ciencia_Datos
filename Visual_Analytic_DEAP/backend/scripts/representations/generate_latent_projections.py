from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

try:
    import umap
except ImportError:
    umap = None

from backend.utils.paths import DATASET_DIR


FEATURE_DIR: Path = (
    DATASET_DIR
    / "processed"
    / "representations"
    / "manual_deap_features"
)

X_STANDARDIZED_PATH: Path = FEATURE_DIR / "X_features_standardized.npy"
# X_STANDARDIZED_PATH: Path = FEATURE_DIR / "X_features.npy"
TRIAL_METADATA_PATH: Path = FEATURE_DIR / "trial_metadata.csv"

PROJECTIONS_DIR: Path = FEATURE_DIR / "projections"


def parse_arguments() -> argparse.Namespace:
    """Define argumentos de línea de comandos."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description="Genera proyecciones 2D PCA/UMAP/t-SNE desde X_features_standardized."
    )

    parser.add_argument(
        "--methods",
        type=str,
        default="pca,umap,tsne",
        help="Métodos separados por coma. Ejemplo: pca,umap,tsne",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Elimina la carpeta projections antes de generar nuevas proyecciones.",
    )

    return parser.parse_args()


def prepare_output_directory(clean: bool) -> None:
    """Prepara carpeta de salida para proyecciones."""
    if clean and PROJECTIONS_DIR.exists():
        shutil.rmtree(PROJECTIONS_DIR)

    PROJECTIONS_DIR.mkdir(parents=True, exist_ok=True)


def parse_methods(methods_text: str) -> list[str]:
    """Convierte texto de métodos a lista normalizada."""
    methods: list[str] = [
        method.strip().lower()
        for method in methods_text.split(",")
        if method.strip()
    ]

    allowed_methods: set[str] = {"pca", "umap", "tsne"}

    invalid_methods: list[str] = [
        method for method in methods
        if method not in allowed_methods
    ]

    if invalid_methods:
        raise ValueError(f"Métodos no soportados: {invalid_methods}")

    return methods


def load_inputs() -> tuple[np.ndarray, pd.DataFrame]:
    """Carga matriz normalizada y metadata de trials."""
    if not X_STANDARDIZED_PATH.exists():
        raise FileNotFoundError(f"No existe: {X_STANDARDIZED_PATH}")

    if not TRIAL_METADATA_PATH.exists():
        raise FileNotFoundError(f"No existe: {TRIAL_METADATA_PATH}")

    X_standardized: np.ndarray = np.load(X_STANDARDIZED_PATH)
    trial_metadata: pd.DataFrame = pd.read_csv(TRIAL_METADATA_PATH)

    if X_standardized.shape[0] != len(trial_metadata):
        raise ValueError(
            "Filas de X_standardized no coinciden con metadata: "
            f"{X_standardized.shape[0]} vs {len(trial_metadata)}"
        )

    return X_standardized, trial_metadata


def compute_pca_projection(X_standardized: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    """Calcula proyección PCA 2D."""
    pca: PCA = PCA(n_components=2, random_state=97)

    coordinates: np.ndarray = pca.fit_transform(X_standardized)

    metadata: dict[str, Any] = {
        "method": "pca",
        "n_components": 2,
        "explained_variance_ratio": pca.explained_variance_ratio_.tolist(),
        "explained_variance_ratio_sum": float(np.sum(pca.explained_variance_ratio_)),
    }

    return coordinates, metadata


def compute_umap_projection(X_standardized: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    """Calcula proyección UMAP 2D."""
    if umap is None:
        raise ImportError(
            "No está instalado umap-learn. Instala con: pip install umap-learn"
        )

    reducer: Any = umap.UMAP(
        n_components=2,
        n_neighbors=15,
        min_dist=0.1,
        metric="euclidean",
        random_state=97,
    )

    coordinates: np.ndarray = reducer.fit_transform(X_standardized)

    metadata: dict[str, Any] = {
        "method": "umap",
        "n_components": 2,
        "n_neighbors": 15,
        "min_dist": 0.1,
        "metric": "euclidean",
        "random_state": 97,
    }

    return coordinates, metadata


def compute_tsne_projection(X_standardized: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    """Calcula proyección t-SNE 2D."""
    tsne: TSNE = TSNE(
        n_components=2,
        perplexity=30.0,
        learning_rate="auto",
        init="pca",
        random_state=97,
    )

    coordinates: np.ndarray = tsne.fit_transform(X_standardized)

    metadata: dict[str, Any] = {
        "method": "tsne",
        "n_components": 2,
        "perplexity": 30.0,
        "learning_rate": "auto",
        "init": "pca",
        "random_state": 97,
    }

    return coordinates, metadata


def build_projection_dataframe(
    coordinates: np.ndarray,
    trial_metadata: pd.DataFrame,
    method: str,
) -> pd.DataFrame:
    """Construye DataFrame final con metadata + coordenadas."""
    projection_df: pd.DataFrame = trial_metadata.copy()

    projection_df["projection_method"] = method
    projection_df["x"] = coordinates[:, 0]
    projection_df["y"] = coordinates[:, 1]

    return projection_df


def save_projection(
    method: str,
    coordinates: np.ndarray,
    method_metadata: dict[str, Any],
    trial_metadata: pd.DataFrame,
) -> dict[str, Any]:
    """Guarda una proyección 2D en CSV y devuelve metadata."""
    projection_df: pd.DataFrame = build_projection_dataframe(
        coordinates=coordinates,
        trial_metadata=trial_metadata,
        method=method,
    )

    output_file: Path = PROJECTIONS_DIR / f"{method}_2d.csv"
    projection_df.to_csv(output_file, index=False)

    saved_metadata: dict[str, Any] = {
        **method_metadata,
        "output_file": str(output_file.relative_to(DATASET_DIR)),
        "num_points": int(coordinates.shape[0]),
        "coordinate_shape": list(coordinates.shape),
    }

    print(f"[OK] Proyección {method.upper()} guardada:", output_file)

    return saved_metadata


def generate_projections(methods: list[str]) -> None:
    """Genera las proyecciones solicitadas."""
    X_standardized, trial_metadata = load_inputs()

    all_metadata: dict[str, Any] = {
        "input_file": str(X_STANDARDIZED_PATH.relative_to(DATASET_DIR)),
        "metadata_file": str(TRIAL_METADATA_PATH.relative_to(DATASET_DIR)),
        "input_shape": list(X_standardized.shape),
        "methods": {},
    }

    for method in methods:
        print(f"[INFO] Generando proyección: {method}")

        if method == "pca":
            coordinates, method_metadata = compute_pca_projection(
                X_standardized=X_standardized,
            )
        elif method == "umap":
            coordinates, method_metadata = compute_umap_projection(
                X_standardized=X_standardized,
            )
        elif method == "tsne":
            coordinates, method_metadata = compute_tsne_projection(
                X_standardized=X_standardized,
            )
        else:
            raise ValueError(f"Método no soportado: {method}")

        saved_metadata: dict[str, Any] = save_projection(
            method=method,
            coordinates=coordinates,
            method_metadata=method_metadata,
            trial_metadata=trial_metadata,
        )

        all_metadata["methods"][method] = saved_metadata

    metadata_file: Path = PROJECTIONS_DIR / "projection_metadata.json"

    with metadata_file.open("w", encoding="utf-8") as file:
        json.dump(all_metadata, file, indent=2, ensure_ascii=False)

    print("[OK] Metadata de proyecciones guardada:", metadata_file)


def main() -> None:
    """Punto de entrada principal."""
    args: argparse.Namespace = parse_arguments()

    prepare_output_directory(clean=args.clean)

    methods: list[str] = parse_methods(methods_text=args.methods)

    generate_projections(methods=methods)


if __name__ == "__main__":
    main()


# USO:
# Todas las proyecciones:
# python -m backend.scripts.representations.generate_latent_projections --clean
#
# Solo PCA:
# python -m backend.scripts.representations.generate_latent_projections --methods pca --clean
#
# PCA y UMAP:
# python -m backend.scripts.representations.generate_latent_projections --methods pca,umap --clean
# eso es todo