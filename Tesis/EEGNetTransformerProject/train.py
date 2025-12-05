# train.py

import os
import time
from typing import List

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader

from config.settings import (
    nclasses,
    sequence_length,
    num_eeg_channels,
    batch_size,
    device,
    data_root,
    debug_mode_flag,
)
from data.dataloader import get_dataloaders
from models.eegnet_transformer import EEGTransformerNet


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion,
    optimizer,
    epoch: int,
) -> float:
    model.train()
    running_loss: float = 0.0

    for inputs, labels in dataloader:
        inputs, labels = inputs.to(device), labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs.float())
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)

    epoch_loss: float = running_loss / len(dataloader.dataset)
    print(f"Epoch {epoch} - Training loss: {epoch_loss:.4f}")
    return epoch_loss


def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion,
) -> float:
    model.eval()
    running_loss: float = 0.0

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs.float())
            loss = criterion(outputs, labels)
            running_loss += loss.item() * inputs.size(0)

    val_loss: float = running_loss / len(dataloader.dataset)
    print(f"Validation loss: {val_loss:.4f}")
    return val_loss


def evaluate_metrics(
    model: nn.Module,
    dataloader: DataLoader,
) -> None:
    model.eval()
    all_preds: List[int] = []
    all_labels: List[int] = []

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            outputs = model(inputs.float())
            preds = torch.argmax(outputs, dim=1).cpu().numpy()

            all_preds.extend(preds)
            all_labels.extend(labels.numpy())

    # Matriz de confusión
    cm = confusion_matrix(all_labels, all_preds)
    print("Matriz de confusión:")
    print(cm)

    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=["bckg", "seiz"],
        yticklabels=["bckg", "seiz"],
    )
    plt.xlabel("Predicho")
    plt.ylabel("Real")
    plt.title("Matriz de Confusión")
    plt.show()

    # Reporte de métricas
    report = classification_report(
        all_labels,
        all_preds,
        target_names=["bckg", "seiz"],
        digits=4,
    )
    print("Reporte de métricas:")
    print(report)


def main() -> None:
    print("\nCargando datos...")
    # train_loader, val_loader, test_loader = get_dataloaders(data_root, batch_size)
    train_loader, _, val_loader = get_dataloaders(data_root, batch_size)

    print("Instanciando modelo...")
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
        MSA_num_heads=2,              # para 6GB VRAM
        flag_positional_encoding=True,
        transformer_dim_feedforward=256,  # reducido para tu GPU
        num_transformer_layers=1,    # menos capas para reducir uso de memoria
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    num_epochs: int = 150  # número pequeño para prueba

    print("\nEntrenando modelo...")
    train_losses: List[float] = []
    val_losses: List[float] = []

    for epoch in range(1, num_epochs + 1):
        # Entrenamiento para una época, retorna pérdida promedio
        avg_train_loss: float = train_one_epoch(
            model,
            train_loader,
            criterion,
            optimizer,
            epoch,
        )

        # Evaluación sobre conjunto de validación
        val_loss: float = evaluate(model, val_loader, criterion)

        # Registro de pérdidas para graficar
        train_losses.append(avg_train_loss)
        val_losses.append(val_loss)

    print("\nEntrenamiento finalizado. Evaluando en test...")
    # evaluate(model, test_loader, criterion)
    evaluate(model, val_loader, criterion)

    model_path: str = os.path.join("results", "EEGTransformerNet.pth")
    torch.save(model.state_dict(), model_path)

    print("\n🔍 Evaluando métricas finales...")
    # evaluate_metrics(model, test_loader)
    evaluate_metrics(model, val_loader)  # aquí val_loader es el test_loader

    print(f"Modelo guardado en: {model_path}")

    os.makedirs("results/loss_data", exist_ok=True)
    np.save("results/loss_data/train_losses.npy", np.array(train_losses))
    np.save("results/loss_data/val_losses.npy", np.array(val_losses))
    print("Pérdidas guardadas en results/loss_data/")


if __name__ == "__main__":
    main()
