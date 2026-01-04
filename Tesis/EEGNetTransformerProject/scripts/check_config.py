import os
import sys

PROJECT_ROOT: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
print(f"Project root: {PROJECT_ROOT}")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# scripts/check_config.py
from config.settings import (
    binary_classifier_flag,
    segment_interval,
    sequence_length,
    num_eeg_channels,
    nclasses,
    batch_size,
    seizure_types,
    data_root,
    device,
)

from config.train_config import small_config


def main() -> None:
    print("=== SETTINGS.PY ===")
    print(f"binary_classifier_flag: {binary_classifier_flag}")
    print(f"segment_interval: {segment_interval}")
    print(f"sequence_length: {sequence_length}")
    print(f"num_eeg_channels: {num_eeg_channels}")
    print(f"nclasses: {nclasses}")
    print(f"batch_size: {batch_size}")
    print(f"seizure_types: {seizure_types}")
    print(f"data_root: {data_root}")
    print(f"device: {device}")

    print("\n=== TRAIN_CONFIG.PY (small_config) ===")
    for k, v in small_config.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
