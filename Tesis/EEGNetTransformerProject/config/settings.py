# config/settings.py
from typing import List
import os

import torch

# ===== General flags =====
binary_classifier_flag: bool = True
debug_mode_flag: bool = False


# ===== Dataset configuration =====
segment_interval: int = 4  # Duration of each EEG window in seconds
resampleFS: int = 250  # Sampling frequency after resampling
sequence_length: int = resampleFS * segment_interval
num_eeg_channels: int = 22  # Fixed number of EEG channels
nclasses: int = 2 if binary_classifier_flag else 4
batch_size: int = 64  # original 1024 # Recommended for 6GB VRAM(me GPU)


# ===== Seizure types =====
seizure_types: List[str] = (
    ["bckg", "seizure"] if binary_classifier_flag else ["fnsz", "gnsz", "cpsz", "bckg"]
)

# ===== Ruta al dataset según flags =====
data_root: str = os.path.join(
    "..",
    "data_procesada",
    "TUSZ_processed_binary_individual_segments",
    f"segment_interval_{segment_interval}_sec",
)
# print(f"Data root set to: {data_root}")
# Si es binario y balanceado → usa TUSZ_processed_binary_balanced_individual_segments
# Si es binario no balanceado → usa TUSZ_processed_binary_individual_segments
# Si es multiclass → usa TUSZ_processed_multiclass_individual_segments
#

# # ===== Device =====
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# print(f"Using device: {device}")