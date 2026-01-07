# training/trainer.py

from typing import List, Tuple

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from config.settings import device

def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    epoch: int,
) -> float:
    # print("device in trainer.py:", device)
    """
    Entrena el modelo por una época completa.

    Returns:
        float: pérdida promedio de la época
    """
    model.train()
    running_loss: float = 0.0

    for inputs, labels in dataloader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs.float())
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)

    epoch_loss: float = running_loss / len(dataloader.dataset)
    print(f"[TRAIN] Epoch {epoch} - Loss: {epoch_loss:.4f}")
    return epoch_loss


def validate_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
) -> float:
    """
    Evalúa el modelo en validación.

    Returns:
        float: pérdida promedio de validación
    """
    model.eval()
    running_loss: float = 0.0

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            outputs = model(inputs.float())
            loss = criterion(outputs, labels)

            running_loss += loss.item() * inputs.size(0)

    val_loss: float = running_loss / len(dataloader.dataset)
    print(f"[VAL] Loss: {val_loss:.4f}")
    return val_loss
