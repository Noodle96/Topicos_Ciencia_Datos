"""
Service de la Vista B (Atención Temporal del Trial, B1/B2/B3).

Lee el manifest (`husformer_manifest.csv`) + los `.npz` de
`extract_representations.py` (`attn_final_summary` por ventana) para armar,
dado un trial, la serie temporal de "dominancia de modalidad" que alimenta
B1 (heatmap) y B2 (líneas superpuestas).

Reducción confirmada con Russell (2026-07-15): `attn_final_summary` es una
matriz 5x5 por ventana (fila = modalidad que pregunta/query, columna =
modalidad atendida/key, ver docstring de `compute_final_attention_summary`
en extract_representations.py). Para "qué modalidad domina la
representación fusionada" (T4), se promedia sobre las FILAS (eje query)
para cada columna -- es decir, cuánta atención recibe en promedio cada
modalidad de parte de TODAS las demás (incluida ella misma), no cuánto
pregunta cada una. Justificación completa (con ejemplo numérico) en
`md/husformer_vista_b_resumen_implementacion.md` (pendiente de escribir al
cerrar Vista B).

Este servicio NO precomputa nada -- igual que el clustering de A2, arma la
serie al vuelo por request (leer ~60 filas de manifest + indexar ~60
matrices 5x5 ya en memoria es del mismo orden de costo que A2, trivial).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.utils.paths import DATASET_DIR


REPRESENTATION_INPUTS_DIR: Path = DATASET_DIR / "processed" / "representation_inputs"
HUSFORMER_MANIFEST_FILE: Path = REPRESENTATION_INPUTS_DIR / "husformer_manifest.csv"

REPRESENTATIONS_DIR: Path = DATASET_DIR / "processed" / "representations" / "husformer"

# Mismo orden m1..m5 que MODALITY_CHANNEL_GROUPS (backend/scripts/husformer/
# config.py) y que modality_labels en extraction_metadata.json -- EEG=32ch,
# EOG=4ch, EMG=4ch, GSR=1ch, Resp+Plet+Temp=3ch.
MODALITY_LABELS: dict[str, str] = {
    "modality_1": "EEG",
    "modality_2": "EOG",
    "modality_3": "EMG",
    "modality_4": "GSR",
    "modality_5": "Resp+Plet+Temp",
}


def _load_manifest() -> pd.DataFrame:
    """Carga el manifest de trazabilidad ventana->contexto (participante/trial/split)."""
    if not HUSFORMER_MANIFEST_FILE.exists():
        raise FileNotFoundError(
            f"No existe el manifest: {HUSFORMER_MANIFEST_FILE}. "
            "Ejecuta backend/scripts/husformer/build_husformer_dataset.py primero."
        )

    return pd.read_csv(HUSFORMER_MANIFEST_FILE)


def _load_split_attn_final_summary(split_name: str) -> np.ndarray:
    """Carga attn_final_summary (N_ventanas_del_split, 5, 5) de un split."""
    npz_path: Path = REPRESENTATIONS_DIR / f"{split_name}_representations.npz"

    if not npz_path.exists():
        raise FileNotFoundError(
            f"No existe: {npz_path}. Ejecuta "
            "backend/scripts/husformer/extract_representations.py primero."
        )

    with np.load(npz_path) as data:
        return data["attn_final_summary"]


def _load_split_attn_cross_summary(split_name: str) -> np.ndarray:
    """
    Carga attn_cross_summary (N_ventanas_del_split, 5, 5) de un split.

    A diferencia de attn_final_summary (auto-atención del transformer de
    fusión final, usado en B1/B2), attn_cross_summary resume los 5 módulos
    de atención cruzada `trans_m{i}_all` -- fila = módulo/modalidad que
    "pregunta", columna = modalidad fuente de la que atiende. Ver docstring
    de compute_cross_modal_summary en extract_representations.py.
    """
    npz_path: Path = REPRESENTATIONS_DIR / f"{split_name}_representations.npz"

    if not npz_path.exists():
        raise FileNotFoundError(
            f"No existe: {npz_path}. Ejecuta "
            "backend/scripts/husformer/extract_representations.py primero."
        )

    with np.load(npz_path) as data:
        return data["attn_cross_summary"]


def load_husformer_trial_attention(participant_id: int, trial: int) -> dict[str, Any]:
    """
    Serie temporal de dominancia de modalidad para un trial (Vista B, B1/B2).

    Para cada ventana de 1s del trial (ordenadas cronológicamente por
    window_index), reduce su attn_final_summary (5x5: query x key) a un
    vector de 5 valores promediando sobre el eje query (filas) -- cuánta
    atención recibe cada modalidad en promedio de todas las que preguntan.

    Los 5 valores devueltos por ventana (`modality_1`..`modality_5`) son
    PORCENTAJES (0-100, siempre suman 100 dentro de una misma ventana) --
    no el peso crudo de atención. Ver comentario en el cuerpo de la función
    para la derivación matemática exacta.
    """
    manifest: pd.DataFrame = _load_manifest()

    trial_rows: pd.DataFrame = manifest[
        (manifest["participant_id"] == participant_id)
        & (manifest["trial"] == trial)
    ].sort_values("window_index")

    if trial_rows.empty:
        raise ValueError(
            f"No se encontraron ventanas para participant_id={participant_id}, "
            f"trial={trial} en el manifest."
        )

    splits_in_trial: np.ndarray = trial_rows["split"].unique()
    if len(splits_in_trial) != 1:
        raise ValueError(
            f"Trial (participant_id={participant_id}, trial={trial}) tiene "
            f"ventanas repartidas en más de un split: {splits_in_trial.tolist()} -- "
            "no debería pasar, el split es por participante completo."
        )

    split_name: str = str(splits_in_trial[0])
    attn_final_summary: np.ndarray = _load_split_attn_final_summary(split_name)

    local_ids: np.ndarray = trial_rows["local_id"].to_numpy()
    trial_attn: np.ndarray = attn_final_summary[local_ids]  # (n_windows, 5, 5)

    # Promedio sobre el eje query (filas, axis=1): "cuánta atención recibe
    # cada modalidad (columna/key) de todas las que preguntan (filas/query)".
    modality_dominance: np.ndarray = trial_attn.mean(axis=1)  # (n_windows, 5)

    # Reescalado a PORCENTAJE DE DOMINANCIA dentro de la ventana (2026-07-17,
    # a pedido de Russell) -- justificado en Munzner Cap. 3 ("Derive":
    # producir un atributo nuevo por transformación de uno existente) y
    # Aigner Cap. 4 (4.2.2: tareas de COMPARACIÓN -- T4 compara 5 modalidades
    # entre sí -- requieren que todas compartan una escala unificada). El
    # peso crudo de dominancia ronda ~1/640 (0.0015-0.002), un rango donde
    # la variación real (confirmada tras desactivar attn_mask y reentrenar
    # 40 épocas) queda comprimida en el 3er-4to dígito decimal --
    # prácticamente ilegible en una UI (dos valores distintos redondeaban
    # ambos a "0.002").
    #
    # La suma de los 5 valores de dominancia de UNA ventana es, por
    # construcción matemática (softmax por fila real sobre 640 posiciones,
    # ver docstring del módulo), SIEMPRE 1/128 = 0.0078125, sin importar el
    # contenido -- así que dividir por esa suma y multiplicar por 100 no es
    # un reescalado arbitrario: es la participación relativa REAL de cada
    # modalidad dentro del total de esa ventana (siempre suma 100%, línea
    # base uniforme = 20% por modalidad). Se calcula empíricamente (dividir
    # por la suma real de esa ventana, no por la constante teórica 1/128)
    # para ser robustos a cualquier desviación numérica mínima.
    row_sums: np.ndarray = modality_dominance.sum(axis=1, keepdims=True)  # (n_windows, 1)
    modality_dominance_pct: np.ndarray = modality_dominance / row_sums * 100.0

    windows: list[dict[str, Any]] = []

    for row_position, (_, row) in enumerate(trial_rows.iterrows()):
        weights: np.ndarray = modality_dominance_pct[row_position]

        window_entry: dict[str, Any] = {
            "window_index": int(row["window_index"]),
            "window_start_sec": float(row["window_start_sec"]),
        }

        for modality_key, weight in zip(MODALITY_LABELS.keys(), weights):
            window_entry[modality_key] = float(weight)

        windows.append(window_entry)

    return {
        "participant_id": participant_id,
        "trial": trial,
        "split": split_name,
        "num_windows": len(windows),
        "modality_labels": MODALITY_LABELS,
        "windows": windows,
    }


def load_husformer_window_cross_attention(
    participant_id: int, trial: int, window_index: int
) -> dict[str, Any]:
    """
    Matriz 5x5 CRUDA de atención cross-modal (attn_cross_summary) de UNA
    ventana puntual (Vista C, C1).

    A diferencia de load_husformer_trial_attention (B1/B2), que reduce las
    60 ventanas de un trial a un vector de 5 valores por ventana promediando
    sobre el eje query, acá se devuelve la matriz 5x5 completa de UNA sola
    ventana, sin promediar ni reescalar -- C1 muestra el detalle de "quién
    le presta atención a quién" en ese instante puntual, que es justamente
    lo que B1/B2 esconden al promediar sobre el eje query.

    fila = módulo/modalidad que "pregunta" (trans_m{i}_all), columna =
    modalidad fuente atendida. No son porcentajes de dominancia como en
    B1/B2 (ese reescalado se justifica ahí porque se compara relativa entre
    5 modalidades DENTRO de una ventana ya promediada); acá se devuelve el
    peso de atención promedio tal cual, ya que C1 no compara entre
    modalidades sino que expone la matriz completa fila x columna.
    """
    manifest: pd.DataFrame = _load_manifest()

    window_rows: pd.DataFrame = manifest[
        (manifest["participant_id"] == participant_id)
        & (manifest["trial"] == trial)
        & (manifest["window_index"] == window_index)
    ]

    if window_rows.empty:
        raise ValueError(
            f"No se encontró la ventana window_index={window_index} para "
            f"participant_id={participant_id}, trial={trial} en el manifest."
        )

    if len(window_rows) > 1:
        raise ValueError(
            f"Se encontró más de una fila para participant_id={participant_id}, "
            f"trial={trial}, window_index={window_index} -- el manifest "
            "debería tener una fila única por (participante, trial, ventana)."
        )

    window_row: pd.Series = window_rows.iloc[0]
    split_name: str = str(window_row["split"])
    local_id: int = int(window_row["local_id"])

    attn_cross_summary: np.ndarray = _load_split_attn_cross_summary(split_name)
    window_matrix: np.ndarray = attn_cross_summary[local_id]  # (5, 5)

    return {
        "participant_id": participant_id,
        "trial": trial,
        "window_index": window_index,
        "window_start_sec": float(window_row["window_start_sec"]),
        "split": split_name,
        "modality_labels": MODALITY_LABELS,
        "matrix": window_matrix.astype(float).tolist(),
    }
