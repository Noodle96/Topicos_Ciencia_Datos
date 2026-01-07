# evaluation/metrics.py

from typing import Dict, List

import numpy as np
import torch
import torch.nn as nn
from sklearn.metrics import classification_report, confusion_matrix
from torch.utils.data import DataLoader
from config.settings import device

def compute_classification_metrics(
    model: nn.Module,
    dataloader: DataLoader,
    target_names: List[str],
    adversarial: bool = False,
) -> Dict[str, object]:
    """
    Calcula métricas de clasificación para un dataloader dado.

    Returns:
        Dict con:
          - confusion_matrix: np.ndarray
          - classification_report: str
          - y_true: np.ndarray
          - y_pred: np.ndarray
    """
    model.eval()

    all_preds: List[int] = []
    all_labels: List[int] = []

    with torch.no_grad():
        for inputs, labels in dataloader:
            inputs = inputs.to(device)
            labels = labels.to(device)

            # outputs = model(inputs.float())
            if adversarial:
                outputs, _ = model(inputs.float(), grl_lambda=0.0)
            else:
                outputs = model(inputs.float())

            preds = torch.argmax(outputs, dim=1)

            all_preds.extend(preds.cpu().numpy().tolist())
            all_labels.extend(labels.cpu().numpy().tolist())

    y_true: np.ndarray = np.array(all_labels)
    y_pred: np.ndarray = np.array(all_preds)

    cm: np.ndarray = confusion_matrix(y_true, y_pred)

    report: str = classification_report(
        y_true,
        y_pred,
        target_names=target_names,
        digits=4,
    )

    return {
        "confusion_matrix": cm,
        "classification_report": report,
        "y_true": y_true,
        "y_pred": y_pred,
    }
