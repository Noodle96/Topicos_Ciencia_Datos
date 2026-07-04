from __future__ import annotations

from backend.scripts.preprocess_representation_inputs import (
    AUTONOMIC_CHANNELS,
    EEG_CHANNELS_GENEVA_ORDER,
    EMG_CHANNELS,
    EOG_CHANNELS,
)
from backend.utils.paths import DATASET_DIR


# ============================================================
# RUTAS
# ============================================================

PROCESSED_DIR = DATASET_DIR / "processed"
REPRESENTATION_INPUTS_DIR = PROCESSED_DIR / "representation_inputs"
REPRESENTATION_METADATA_FILE = REPRESENTATION_INPUTS_DIR / "representation_metadata.csv"
HUSFORMER_MANIFEST_FILE = REPRESENTATION_INPUTS_DIR / "husformer_manifest.csv"

# husformer_deap_va/ es NUESTRA copia de trabajo del repo Husformer (repositorio
# hermano de backend/ y dataset/, bajo la raíz del proyecto). El clon original
# Husformer/ se deja intacto como referencia pristina; todas las modificaciones
# (src/5 -> src/, main-5.py -> main.py, fixes a los bugs conocidos, etc.) se
# hacen únicamente dentro de husformer_deap_va/.
HUSFORMER_DIR = DATASET_DIR.parent / "husformer_deap_va"
HUSFORMER_DATA_DIR = HUSFORMER_DIR / "data"
HUSFORMER_PKL_FILE = HUSFORMER_DATA_DIR / "Husformer.pkl"


# ============================================================
# VENTANEO (ver windowing.py)
# ============================================================

WINDOW_SECONDS: float = 1.0


# ============================================================
# MODALIDADES — Decisión 1, resuelta el 2026-07-04: 5 modalidades.
# ============================================================
# GSR1 se separa como su propia modalidad (modality_4) por ser la señal
# autonómica más informativa para valencia/activación según la literatura
# DEAP; Resp/Plet/Temp quedan agrupadas en modality_5. Los nombres de canal
# se reutilizan directamente de preprocess_representation_inputs.py para no
# duplicar (y arriesgar un typo en) la lista de 32 canales EEG.

MODALITY_CHANNEL_GROUPS: dict[str, list[str]] = {
    "modality_1": list(EEG_CHANNELS_GENEVA_ORDER),                                # EEG, 32 canales
    "modality_2": list(EOG_CHANNELS),                                             # EOG, 4 canales
    "modality_3": list(EMG_CHANNELS),                                             # EMG, 4 canales
    "modality_4": ["GSR1"],                                                       # GSR, 1 canal
    "modality_5": [canal for canal in AUTONOMIC_CHANNELS if canal != "GSR1"],     # Resp+Plet+Temp, 3 canales
}


# ============================================================
# SPLIT POR PARTICIPANTE — Decisión 3, resuelta el 2026-07-04.
# ============================================================
# Calculado una sola vez con semilla fija y luego "congelado" aquí como
# constante, para que el split sea idéntico entre corridas sin depender de
# qué versión de numpy/su generador aleatorio esté instalada.
#
# Cómo se generó (no se re-ejecuta en el pipeline, solo queda documentado
# aquí por trazabilidad):
#   import numpy as np
#   pool = [p for p in range(1, 33) if p != 28]   # S28 se fuerza a 'train'
#   rng = np.random.default_rng(seed=97)          # misma semilla que ICA/PCA/UMAP/t-SNE del proyecto
#   mezclado = rng.permutation(pool).tolist()
#   test, valid, train = mezclado[:3], mezclado[3:6], mezclado[6:] + [28]
#
# S28 se excluyó del sorteo y se forzó a 'train' porque sus eventos se
# reconstruyen a partir de participant_ratings.xls (ver
# SPECIAL_RECONSTRUCTED_SUBJECTS en preprocess_trials.py), no del canal
# Status real — un caso menos confiable como referencia de evaluación.

RANDOM_SEED: int = 97

PARTICIPANT_SPLIT: dict[str, list[int]] = {
    "test": [3, 6, 27],
    "valid": [11, 13, 26],
    "train": [
        1, 2, 4, 5, 7, 8, 9, 10, 12, 14, 15, 16, 17, 18, 19, 20,
        21, 22, 23, 24, 25, 28, 29, 30, 31, 32,
    ],
}

PARTICIPANT_TO_SPLIT: dict[int, str] = {
    participant_id: split_name
    for split_name, participant_ids in PARTICIPANT_SPLIT.items()
    for participant_id in participant_ids
}


# ============================================================
# ETIQUETAS — Decisión 2, resuelta el 2026-07-04: valencia como etiqueta
# principal (ver labeling.py para el esquema exacto de conversión).
# ============================================================

LABEL_SOURCE_COLUMN: str = "valence"
