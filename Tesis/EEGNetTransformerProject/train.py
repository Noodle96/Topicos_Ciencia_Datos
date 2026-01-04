# train.py

import os
from typing import List, Dict

import numpy as np
import torch
import torch.nn as nn

from config.settings import (
    batch_size,
    data_root,
    device,
    nclasses,
    num_eeg_channels,
    sequence_length,
)
from data.dataloader import get_train_val_loaders
from models.eegnet_transformer import EEGTransformerNet
from training.trainer import train_one_epoch, validate_one_epoch
from evaluation.metrics import compute_classification_metrics


def main() -> None:

    results_root: str = "results/baseline"
    loss_dir: str = os.path.join(results_root, "losses")
    metrics_dir: str = os.path.join(results_root, "metrics")
    model_dir: str = os.path.join(results_root, "model")

    for d in [loss_dir, metrics_dir, model_dir]:
        os.makedirs(d, exist_ok=True)

    print("\n📦 Cargando dataloaders para train y val...")
    train_loader, val_loader = get_train_val_loaders(
        data_root=data_root,
        batch_size=batch_size,
    )

    print("🧠 Instanciando modelo baseline...")
    model = EEGTransformerNet(
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

    criterion: nn.Module = nn.CrossEntropyLoss()
    optimizer: torch.optim.Optimizer = torch.optim.Adam(
        model.parameters(),
        lr=1e-4,
    )

    num_epochs: int = 30
    train_losses: List[float] = []
    val_losses: List[float] = []

    print("\n🚀 Iniciando entrenamiento...")
    for epoch in range(1, num_epochs + 1):
        train_loss: float = train_one_epoch(
            model=model,
            dataloader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            epoch=epoch,
        )

        val_loss: float = validate_one_epoch(
            model=model,
            dataloader=val_loader,
            criterion=criterion,
        )

        train_losses.append(train_loss)
        val_losses.append(val_loss)

    print("\n📊 Evaluando métricas finales (VAL)... y guardando")
    metrics: Dict[str, object] = compute_classification_metrics(
        model=model,
        dataloader=val_loader,
        target_names=["bckg", "seizure"],
    )

    # ===============================
    # Guardar métricas de VALIDATION
    # ===============================
    np.save(
        os.path.join(metrics_dir, "val_confusion.npy"),
        metrics["confusion_matrix"],
    )

    np.save(
        os.path.join(metrics_dir, "val_y_true.npy"),
        metrics["y_true"],
    )

    np.save(
        os.path.join(metrics_dir, "val_y_pred.npy"),
        metrics["y_pred"],
    )

    with open(
        os.path.join(metrics_dir, "val_classification_report.txt"),
        "w",
    ) as f:
        f.write(metrics["classification_report"])

    print("📁 Métricas de VALIDATION guardadas.")


    print("\n💾 Guardando modelo y pérdidas...")
    torch.save(
        model.state_dict(),
        os.path.join(model_dir, "EEGNetTransformerNet.pth"),
    )

    np.save(
        os.path.join(loss_dir, "train_losses.npy"),
        np.array(train_losses),
    )

    np.save(
        os.path.join(loss_dir, "val_losses.npy"),
        np.array(val_losses),
    )

    print("✅ Entrenamiento baseline finalizado.")

    # ======================================================
    # LIBERAR MEMORIA DE TRAIN Y VAL LOADERS
    # ======================================================
    del train_loader
    del val_loader
    torch.cuda.empty_cache()
    print("[INFO] Train y Val loaders liberados de memoria.")


if __name__ == "__main__":
    main()
