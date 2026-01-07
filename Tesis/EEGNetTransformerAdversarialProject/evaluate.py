# evaluate.py

from typing import Dict
import os

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from config.settings import (
    nclasses,
    sequence_length,
    num_eeg_channels,
    batch_size,
    device,
    data_root,
)
from data.dataloader import get_test_loader
from models.eegnet_transformer import EEGTransformerNet
from evaluation.metrics import compute_classification_metrics


def evaluate_on_test() -> None:
    """
    Evalúa el modelo entrenado únicamente sobre el conjunto TEST
    y guarda todas las métricas necesarias para análisis posterior.
    """

    print("\n📦 Cargando TEST dataloader...")
    test_loader: DataLoader = get_test_loader(
        data_root=data_root,
        batch_size=batch_size,
    )

    print("🧠 Cargando modelo entrenado...")
    model: nn.Module = EEGTransformerNet(
        nb_classes=nclasses,
        sequence_length=sequence_length,
        eeg_chans=num_eeg_channels,
        F1=16,
        D=2,
        eegnet_kernel_size=32,
        dropout_eegnet=0.3,
        eegnet_pooling_1=5,
        eegnet_pooling_2=5,
        MSA_num_heads=2,
        flag_positional_encoding=True,
        transformer_dim_feedforward=256,
        num_transformer_layers=1,
    ).to(device)

    model_path: str = "results/baseline/model/EEGNetTransformerNet.pth"
    model.load_state_dict(torch.load(model_path, map_location=device))
    model.eval()

    print("🔍 Evaluando modelo en TEST...")
    metrics: Dict[str, object] = compute_classification_metrics(
        model=model,
        dataloader=test_loader,
        target_names=["bckg", "seizure"],
    )

    # ==========================
    # Guardado de resultados
    # ==========================
    output_dir: str = os.path.join("results", "test_metrics")
    os.makedirs(output_dir, exist_ok=True)

    np.save(
        os.path.join(output_dir, "confusion_matrix.npy"),
        metrics["confusion_matrix"],
    )

    np.save(
        os.path.join(output_dir, "y_true.npy"),
        metrics["y_true"],
    )

    np.save(
        os.path.join(output_dir, "y_pred.npy"),
        metrics["y_pred"],
    )

    with open(os.path.join(output_dir, "classification_report.txt"), "w") as f:
        f.write(metrics["classification_report"])

    print("💾 Resultados TEST guardados en:", output_dir)

    # ==========================
    # Liberar memoria
    # ==========================
    del test_loader
    torch.cuda.empty_cache()
    print("[INFO] Test loader liberado de memoria.")


if __name__ == "__main__":
    evaluate_on_test()
