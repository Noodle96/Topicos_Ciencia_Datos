# evaluate_adversarial.py

from __future__ import annotations

import os
from typing import Dict

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

from config.settings import (
    data_root,
    batch_size,
    device,
    nclasses,
    sequence_length,
    num_eeg_channels,
)

from data.dataloader_adversarial import get_adversarial_test_loader

from models.eegnet_transformer import EEGTransformerNet
from models.eegnet_transformer_adversarial import EEGNetTransformerAdversarial

from evaluation.metrics_adversarial import (
    compute_adversarial_classification_metrics,
)


@torch.no_grad()
def evaluate_on_test() -> None:
    """
    Evalúa el modelo adversarial en TEST (solo clasificación de eventos)
    y guarda los mismos artefactos que el baseline para comparación.
    """

    print("\n📦 Cargando DataLoader adversarial (TEST)...")
    test_loader: DataLoader = get_adversarial_test_loader(
        data_root=data_root,
        batch_size=batch_size,
    )

    test_dataset = test_loader.dataset
    num_domains: int = len(test_dataset.patient_to_domain)

    print(f"🧬 Número de dominios (pacientes en TEST): {num_domains}")

    # ======================================================
    # Backbone
    # ======================================================
    print("🧠 Inicializando backbone...")
    backbone: EEGTransformerNet = EEGTransformerNet(
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

    # ======================================================
    # Modelo adversarial
    # ======================================================
    model: nn.Module = EEGNetTransformerAdversarial(
        backbone=backbone,
        num_classes=nclasses,
        num_domains=num_domains,
        dropout=0.5,
    ).to(device)

    model_path: str = "results/adversarial/model/EEGNetTransformerAdversarial.pth"
    print(f"📂 Cargando pesos desde: {model_path}")

    # model.load_state_dict(torch.load(model_path, map_location=device))

    
    state_dict = torch.load(model_path, map_location=device)

    # 🔥 Eliminamos pesos del domain_head (no aplican en TEST)
    state_dict = {
        k: v for k, v in state_dict.items()
        if not k.startswith("domain_head")
    }

    model.load_state_dict(state_dict, strict=False)

    model.eval()

    # ======================================================
    # Evaluación (CLASIFICACIÓN)
    # ======================================================
    print("🔍 Evaluando modelo adversarial en TEST (solo clasificación)...")

    metrics: Dict[str, object] = compute_adversarial_classification_metrics(
        model=model,
        dataloader=test_loader,
        device=device,
        target_names=["bckg", "seizure"],
        grl_lambda_eval=0.0,  # GRL apagado en evaluación
    )

    # ======================================================
    # Guardado (MISMO FORMATO QUE BASELINE)
    # ======================================================
    output_dir: str = os.path.join(
        "results",
        "adversarial",
        "test_metrics",
    )
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

    print("💾 Resultados adversariales TEST guardados en:", output_dir)

    # ======================================================
    # Liberar memoria
    # ======================================================
    del test_loader
    torch.cuda.empty_cache()
    print("[INFO] Test loader liberado de memoria.")


if __name__ == "__main__":
    evaluate_on_test()
