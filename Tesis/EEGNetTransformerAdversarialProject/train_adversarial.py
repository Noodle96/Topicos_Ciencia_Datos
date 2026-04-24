# train_adversarial.py

from __future__ import annotations

import os
from typing import List

import numpy as np
import torch
import torch.nn as nn

from config.settings import (
    data_root,
    batch_size,
    device,
    nclasses,
    sequence_length,
    num_eeg_channels,
)

from data.dataloader_adversarial import (
    get_adversarial_train_val_loaders,
)

from models.eegnet_transformer import EEGTransformerNet
from models.eegnet_transformer_adversarial import (
    EEGNetTransformerAdversarial,
)

from training.adversarial_trainer import (
    train_one_epoch_adversarial,
    validate_one_epoch_adversarial,
    AdversarialEpochStats,
)


def main() -> None:
    print("\n📦 Cargando DataLoaders adversariales (TRAIN / VAL)...")

    train_loader, val_loader = get_adversarial_train_val_loaders(
        data_root=data_root,
        batch_size=batch_size,
    )

    # ======================================================
    # Número de dominios = número de pacientes en TRAIN
    # ======================================================
    train_dataset = train_loader.dataset
    num_domains: int = len(train_dataset.patient_to_domain)

    print(f"🧬 Número de dominios (pacientes en TRAIN): {num_domains}")

    # ======================================================
    # Backbone (EEGNet + Transformer)
    # ======================================================
    print("🧠 Inicializando backbone EEGTransformerNet...")
    backbone = EEGTransformerNet(
        nb_classes=nclasses,  # no se usa directamente aquí, pero se mantiene coherencia
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
    # Modelo adversarial (CON GRL)
    # ======================================================
    print("⚔️ Inicializando modelo adversarial (DANN)...")
    model = EEGNetTransformerAdversarial(
        backbone=backbone,
        num_classes=nclasses,     # bckg / seizure
        num_domains=num_domains,  # pacientes
        dropout=0.5,
    ).to(device)

    # ======================================================
    # Losses y optimizador
    # ======================================================
    criterion_class = nn.CrossEntropyLoss()
    criterion_domain = nn.CrossEntropyLoss()

    optimizer = torch.optim.Adam(
        model.parameters(),
        lr=1e-4,
    )

    # ======================================================
    # Entrenamiento
    # ======================================================
    num_epochs: int = 30
    lambda_max: float = 0.25

    train_stats: List[AdversarialEpochStats] = []
    val_stats: List[AdversarialEpochStats] = []

    print("\n🚀 Iniciando entrenamiento adversarial...")
    for epoch in range(1, num_epochs + 1):
        train_epoch_stats = train_one_epoch_adversarial(
            model=model,
            dataloader=train_loader,
            criterion_class=criterion_class,
            criterion_domain=criterion_domain,
            optimizer=optimizer,
            device=device,
            epoch=epoch,
            total_epochs=num_epochs,
            lambda_max=lambda_max,
            use_amp=True,
        )

        val_epoch_stats = validate_one_epoch_adversarial(
            model=model,
            dataloader=val_loader,
            criterion_class=criterion_class,
            criterion_domain=criterion_domain,
            device=device,
            epoch=epoch,
            total_epochs=num_epochs,
            lambda_eval=1.0,
            use_amp=True,
        )

        train_stats.append(train_epoch_stats)
        val_stats.append(val_epoch_stats)

    # ======================================================
    # Guardado de resultados
    # ======================================================
    print("\n💾 Guardando resultados adversariales...")
    os.makedirs("results/adversarial/model", exist_ok=True)

    torch.save(
        model.state_dict(),
        "results/adversarial/model/EEGNetTransformerAdversarial.pth",
    )
    # para los stats
    os.makedirs("results/adversarial/stats", exist_ok=True)
    np.save(
        "results/adversarial/stats/train_stats.npy",
        np.array([s.__dict__ for s in train_stats], dtype=object),
    )
    np.save(
        "results/adversarial/stats/val_stats.npy",
        np.array([s.__dict__ for s in val_stats], dtype=object),
    )

    print("✅ Entrenamiento adversarial finalizado correctamente.")

    # ======================================================
    # Liberar memoria
    # ======================================================
    del train_loader
    del val_loader
    torch.cuda.empty_cache()
    print("[INFO] DataLoaders liberados de memoria.")


if __name__ == "__main__":
    main()
