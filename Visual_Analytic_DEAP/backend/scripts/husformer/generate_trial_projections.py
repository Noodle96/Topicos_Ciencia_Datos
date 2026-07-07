"""
Agrega `last_hs` (representación fusionada de Husformer, extraída por
`extract_representations.py`) a nivel de TRIAL, y genera sus proyecciones 2D
(PCA/UMAP/t-SNE) para la Vista A ("Espacio de Representaciones Fusionadas",
sub-panel A1) del sistema de visual analytics.

Contexto de la decisión de diseño (confirmada por Russell, 2026-07-07, ver
"Aggregación de `last_hs` por trial" en estado_proyecto.md): `last_hs` se
extrae y se guarda por VENTANA de 1s (76,769 ventanas en total, ver
`extract_representations.py`), pero la Vista A opera a nivel de trial. La
agregación elegida es **mean-pooling simple**: el vector de un trial es el
promedio aritmético de los vectores `last_hs` (40 floats) de las ventanas que
lo componen (60 ventanas por trial, salvo S28/trial 40 con 29 — grabación BDF
real cortada, ver `extract_representations.py`).

Este script es DELIBERADAMENTE independiente de
`backend/scripts/representations/generate_latent_projections.py` (que opera
sobre `X_features_standardized.npy`, las features manuales de Tarea1) —
decisión explícita de Russell para no mezclar ambos pipelines de
representación, aunque ambos terminan proyectando con PCA/UMAP/t-SNE: las
funciones puras de cómputo de cada proyección (`compute_pca_projection`,
`compute_umap_projection`, `compute_tsne_projection`) y el armado del
DataFrame de salida (`build_projection_dataframe`) SÍ se reutilizan por
import directo, para no duplicar esa lógica -- ninguna de esas funciones toca
`X_features`/Tarea1 en disco, solo reciben arrays/DataFrames como parámetros.
Tarea1 no se toca ni se sobreescribe en ningún paso de este script.

Uso (desde la raíz del proyecto):
    python -m backend.scripts.husformer.generate_trial_projections
    python -m backend.scripts.husformer.generate_trial_projections --methods pca,umap
    python -m backend.scripts.husformer.generate_trial_projections --clean
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from backend.scripts.representations.generate_latent_projections import (
    build_projection_dataframe,
    compute_pca_projection,
    compute_tsne_projection,
    compute_umap_projection,
    parse_methods,
)
from backend.utils.paths import DATASET_DIR

from . import config

SPLIT_NAMES: tuple[str, ...] = ("train", "valid", "test")
GROUP_COLUMNS: tuple[str, str] = ("participant_id", "trial")

TRIAL_LAST_HS_PATH: Path = config.REPRESENTATIONS_DIR / "trial_last_hs.npy"
TRIAL_LAST_HS_STANDARDIZED_PATH: Path = config.REPRESENTATIONS_DIR / "trial_last_hs_standardized.npy"
TRIAL_METADATA_PATH: Path = config.REPRESENTATIONS_DIR / "trial_metadata.csv"
AGGREGATION_METADATA_PATH: Path = config.REPRESENTATIONS_DIR / "trial_aggregation_metadata.json"

PROJECTIONS_DIR: Path = config.REPRESENTATIONS_DIR / "projections"


def parse_arguments() -> argparse.Namespace:
    """Define los argumentos de línea de comandos del script."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=(
            "Agrega last_hs por trial (mean-pooling sobre las ventanas de 1s) "
            "y genera proyecciones PCA/UMAP/t-SNE para la Vista A (sub-panel A1)."
        )
    )

    parser.add_argument(
        "--methods",
        type=str,
        default="pca,umap,tsne",
        help="Métodos de proyección separados por coma. Ejemplo: pca,umap,tsne",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Elimina las salidas previas (agregación + proyecciones) antes de generar nuevas.",
    )

    return parser.parse_args()


def prepare_output_directories(clean: bool) -> None:
    """Prepara las carpetas de salida (agregación y proyecciones)."""
    if clean:
        for path in (TRIAL_LAST_HS_PATH, TRIAL_LAST_HS_STANDARDIZED_PATH, TRIAL_METADATA_PATH, AGGREGATION_METADATA_PATH):
            if path.exists():
                path.unlink()
        if PROJECTIONS_DIR.exists():
            shutil.rmtree(PROJECTIONS_DIR)

    config.REPRESENTATIONS_DIR.mkdir(parents=True, exist_ok=True)
    PROJECTIONS_DIR.mkdir(parents=True, exist_ok=True)


def load_manifest() -> pd.DataFrame:
    """Carga el manifest de trazabilidad ventana->contexto (participante/trial/split)."""
    if not config.HUSFORMER_MANIFEST_FILE.exists():
        raise FileNotFoundError(
            f"No existe el manifest: {config.HUSFORMER_MANIFEST_FILE}. "
            "Correr primero backend/scripts/husformer/build_husformer_dataset.py."
        )

    return pd.read_csv(config.HUSFORMER_MANIFEST_FILE)


def load_split_last_hs(split_name: str) -> np.ndarray:
    """
    Carga `last_hs` (N_ventanas_del_split, d_m) de un split, extraído por
    `extract_representations.py`. La fila `i` corresponde exactamente al
    `local_id == i` de ese split (ver docstring de `manifest.py`).
    """
    npz_path: Path = config.REPRESENTATIONS_DIR / f"{split_name}_representations.npz"

    if not npz_path.exists():
        raise FileNotFoundError(
            f"No existe: {npz_path}. Correr primero "
            "python -m backend.scripts.husformer.extract_representations"
        )

    with np.load(npz_path) as data:
        return data["last_hs"]


def build_window_last_hs_matrix(manifest: pd.DataFrame) -> np.ndarray:
    """
    Arma la matriz `last_hs` (N_ventanas_totales, d_m), alineada fila a fila
    con `manifest` (mismo orden), uniendo cada split vía `local_id` -- la
    misma reconexión que describe `manifest.py` para el backend en vivo.
    """
    d_m: int | None = None
    last_hs_full: np.ndarray | None = None

    for split_name in SPLIT_NAMES:
        split_row_mask: np.ndarray = (manifest["split"] == split_name).to_numpy()

        if not split_row_mask.any():
            continue

        split_last_hs: np.ndarray = load_split_last_hs(split_name)

        if d_m is None:
            d_m = split_last_hs.shape[1]
            last_hs_full = np.zeros((len(manifest), d_m), dtype=np.float32)

        local_ids: np.ndarray = manifest.loc[split_row_mask, "local_id"].to_numpy()
        last_hs_full[split_row_mask] = split_last_hs[local_ids]  # type: ignore[index]

    if last_hs_full is None:
        raise RuntimeError(
            "No se encontró ningún split con datos -- revisar "
            "REPRESENTATIONS_DIR y el manifest."
        )

    return last_hs_full


def aggregate_by_trial(
    manifest: pd.DataFrame,
    window_last_hs: np.ndarray,
) -> tuple[np.ndarray, pd.DataFrame]:
    """
    Mean-pooling de `last_hs` sobre las ventanas de cada trial.

    Decisión de diseño confirmada por Russell (2026-07-07): promedio
    aritmético simple de los vectores `last_hs` de las ventanas de 1s que
    componen el trial -- ver "Aggregación de last_hs por trial" en
    estado_proyecto.md. Cada trial normalmente aporta 60 ventanas, salvo
    S28/trial 40 con 29 (grabación BDF real cortada, no es un bug, ver
    `extract_representations.py`).
    """
    manifest_indexed: pd.DataFrame = manifest.reset_index(drop=True).copy()
    manifest_indexed["_row_index"] = np.arange(len(manifest_indexed))

    trial_rows: list[dict[str, Any]] = []
    trial_last_hs_vectors: list[np.ndarray] = []

    grouped = manifest_indexed.groupby(list(GROUP_COLUMNS), sort=True)

    for (participant_id, trial), group_df in grouped:
        row_indices: np.ndarray = group_df["_row_index"].to_numpy()
        trial_last_hs_vectors.append(window_last_hs[row_indices].mean(axis=0))

        splits_in_trial: np.ndarray = group_df["split"].unique()
        if len(splits_in_trial) != 1:
            raise ValueError(
                f"Trial (participant_id={participant_id}, trial={trial}) tiene "
                f"ventanas repartidas en más de un split: {splits_in_trial.tolist()} -- "
                "no debería pasar, el split es por participante completo "
                "(ver PARTICIPANT_SPLIT en config.py)."
            )

        first_row: pd.Series = group_df.iloc[0]
        trial_rows.append(
            {
                "participant_id": int(participant_id),
                "trial": int(trial),
                "split": str(splits_in_trial[0]),
                "valence": float(first_row["valence"]),
                "arousal": float(first_row["arousal"]),
                "dominance": float(first_row["dominance"]),
                "liking": float(first_row["liking"]),
                "n_windows_aggregated": int(len(group_df)),
            }
        )

    trial_metadata: pd.DataFrame = pd.DataFrame(trial_rows)
    trial_last_hs: np.ndarray = np.stack(trial_last_hs_vectors, axis=0).astype(np.float32)

    return trial_last_hs, trial_metadata


def validate_trial_last_hs(trial_last_hs: np.ndarray) -> None:
    """Verifica que la matriz agregada no tenga NaN ni Inf antes de proyectar."""
    num_nan: int = int(np.isnan(trial_last_hs).sum())
    num_inf: int = int(np.isinf(trial_last_hs).sum())

    if num_nan > 0 or num_inf > 0:
        raise ValueError(
            f"trial_last_hs contiene valores inválidos: NaN={num_nan}, Inf={num_inf}"
        )


def standardize_trial_last_hs(trial_last_hs: np.ndarray) -> tuple[np.ndarray, StandardScaler]:
    """Aplica StandardScaler (z = (x - mean) / std) antes de proyectar, igual que Tarea1."""
    scaler: StandardScaler = StandardScaler()
    trial_last_hs_standardized: np.ndarray = scaler.fit_transform(trial_last_hs)
    return trial_last_hs_standardized, scaler


def save_aggregation_outputs(
    trial_last_hs: np.ndarray,
    trial_last_hs_standardized: np.ndarray,
    trial_metadata: pd.DataFrame,
    scaler: StandardScaler,
) -> None:
    """Guarda la agregación por trial: arrays crudo/estandarizado, metadata y CSV de contexto."""
    np.save(TRIAL_LAST_HS_PATH, trial_last_hs)
    np.save(TRIAL_LAST_HS_STANDARDIZED_PATH, trial_last_hs_standardized)
    trial_metadata.to_csv(TRIAL_METADATA_PATH, index=False)

    metadata: dict[str, Any] = {
        "aggregation_method": "mean_pooling",
        "description": (
            "Promedio aritmético de last_hs sobre las ventanas de 1s de cada "
            "trial (decisión confirmada 2026-07-07, ver estado_proyecto.md)."
        ),
        "input_files": [
            str((config.REPRESENTATIONS_DIR / f"{split}_representations.npz").relative_to(DATASET_DIR))
            for split in SPLIT_NAMES
        ],
        "manifest_file": str(config.HUSFORMER_MANIFEST_FILE.relative_to(DATASET_DIR)),
        "num_trials": int(trial_last_hs.shape[0]),
        "d_m": int(trial_last_hs.shape[1]),
        "normalization_method": "StandardScaler",
        "global_mean_after_standardization": float(np.mean(trial_last_hs_standardized)),
        "global_std_after_standardization": float(np.std(trial_last_hs_standardized)),
        "windows_per_trial_summary": {
            "expected": 60,
            "min_observed": int(trial_metadata["n_windows_aggregated"].min()),
            "trials_with_fewer_windows": int((trial_metadata["n_windows_aggregated"] < 60).sum()),
        },
        "output_files": {
            "trial_last_hs": str(TRIAL_LAST_HS_PATH.relative_to(DATASET_DIR)),
            "trial_last_hs_standardized": str(TRIAL_LAST_HS_STANDARDIZED_PATH.relative_to(DATASET_DIR)),
            "trial_metadata": str(TRIAL_METADATA_PATH.relative_to(DATASET_DIR)),
        },
    }

    with AGGREGATION_METADATA_PATH.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2, ensure_ascii=False)

    print(f"[OK] Agregación por trial guardada: {TRIAL_LAST_HS_PATH} (shape {trial_last_hs.shape})")
    print(f"[OK] Metadata de agregación: {AGGREGATION_METADATA_PATH}")


def save_projection(
    method: str,
    coordinates: np.ndarray,
    method_metadata: dict[str, Any],
    trial_metadata: pd.DataFrame,
) -> dict[str, Any]:
    """Guarda una proyección 2D en CSV y devuelve su metadata (mismo formato que Tarea1)."""
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


def generate_projections(
    methods: list[str],
    trial_last_hs_standardized: np.ndarray,
    trial_metadata: pd.DataFrame,
) -> None:
    """Genera y guarda las proyecciones 2D solicitadas para la Vista A (sub-panel A1)."""
    all_metadata: dict[str, Any] = {
        "input_file": str(TRIAL_LAST_HS_STANDARDIZED_PATH.relative_to(DATASET_DIR)),
        "metadata_file": str(TRIAL_METADATA_PATH.relative_to(DATASET_DIR)),
        "input_shape": list(trial_last_hs_standardized.shape),
        "methods": {},
    }

    for method in methods:
        print(f"[INFO] Generando proyección: {method}")

        if method == "pca":
            coordinates, method_metadata = compute_pca_projection(X_standardized=trial_last_hs_standardized)
        elif method == "umap":
            coordinates, method_metadata = compute_umap_projection(X_standardized=trial_last_hs_standardized)
        elif method == "tsne":
            coordinates, method_metadata = compute_tsne_projection(X_standardized=trial_last_hs_standardized)
        else:
            raise ValueError(f"Método no soportado: {method}")

        all_metadata["methods"][method] = save_projection(
            method=method,
            coordinates=coordinates,
            method_metadata=method_metadata,
            trial_metadata=trial_metadata,
        )

    metadata_file: Path = PROJECTIONS_DIR / "projection_metadata.json"

    with metadata_file.open("w", encoding="utf-8") as file:
        json.dump(all_metadata, file, indent=2, ensure_ascii=False)

    print("[OK] Metadata de proyecciones guardada:", metadata_file)


def main() -> None:
    """Ejecuta el pipeline completo: last_hs por ventana -> mean-pool por trial -> proyecciones 2D."""
    args: argparse.Namespace = parse_arguments()
    methods: list[str] = parse_methods(methods_text=args.methods)

    prepare_output_directories(clean=args.clean)

    print("[INFO] Cargando manifest y last_hs por ventana...")
    manifest: pd.DataFrame = load_manifest()
    window_last_hs: np.ndarray = build_window_last_hs_matrix(manifest=manifest)

    print(f"[INFO] Agregando {len(manifest)} ventanas en trials (mean-pooling)...")
    trial_last_hs, trial_metadata = aggregate_by_trial(manifest=manifest, window_last_hs=window_last_hs)
    validate_trial_last_hs(trial_last_hs=trial_last_hs)

    trial_last_hs_standardized, scaler = standardize_trial_last_hs(trial_last_hs=trial_last_hs)
    save_aggregation_outputs(
        trial_last_hs=trial_last_hs,
        trial_last_hs_standardized=trial_last_hs_standardized,
        trial_metadata=trial_metadata,
        scaler=scaler,
    )

    generate_projections(
        methods=methods,
        trial_last_hs_standardized=trial_last_hs_standardized,
        trial_metadata=trial_metadata,
    )

    print(f"\n[OK] Pipeline completo. {trial_last_hs.shape[0]} trials procesados.")


if __name__ == "__main__":
    main()


# ============================================================
# USO
# ============================================================
# Pipeline completo (agregación + las 3 proyecciones):
#   python -m backend.scripts.husformer.generate_trial_projections
#
# Solo algunas proyecciones:
#   python -m backend.scripts.husformer.generate_trial_projections --methods pca,umap
#
# Limpiando salidas previas antes de regenerar:
#   python -m backend.scripts.husformer.generate_trial_projections --clean
