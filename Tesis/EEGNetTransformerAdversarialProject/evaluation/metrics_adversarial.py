# evaluation/metrics_adversarial.py

from typing import Dict, List

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from sklearn.metrics import confusion_matrix, classification_report


@torch.no_grad()
def compute_adversarial_classification_metrics(
    *,
    model: nn.Module,
    dataloader: DataLoader,
    device: torch.device,
    target_names: List[str],
    grl_lambda_eval: float = 0.0,
) -> Dict[str, object]:
    """
    Calcula métricas de CLASIFICACIÓN para un modelo adversarial en TEST o VAL.

    ⚠️ Importante:
    - El DataLoader debe devolver: (x, y_class, y_domain)
    - SOLO se evalúa clasificación de eventos (y_class)
    - El dominio NO se evalúa aquí
    - GRL se desactiva usando grl_lambda_eval=0.0

    Args:
        model: Modelo EEGNetTransformerAdversarial entrenado.
        dataloader: DataLoader adversarial (TEST o VAL).
        device: torch.device.
        target_names: nombres de clases (ej. ["bckg", "seizure"]).
        grl_lambda_eval: lambda para GRL en evaluación (default=0.0).

    Returns:
        Dict con:
            - confusion_matrix : np.ndarray
            - classification_report : str
            - y_true : np.ndarray
            - y_pred : np.ndarray
    """

    model.eval()

    all_preds: List[int] = []
    all_labels: List[int] = []

    for batch in dataloader:
        # batch = (x, y_class, y_domain)
        x, y_class, _ = batch  # y_domain NO se usa aquí

        x = x.to(device, non_blocking=True)
        y_class = y_class.to(device, non_blocking=True)

        # Forward adversarial (solo logits de clase)
        class_logits, _ = model(x, grl_lambda=grl_lambda_eval)

        preds: torch.Tensor = torch.argmax(class_logits, dim=1)

        all_preds.extend(preds.cpu().numpy().tolist())
        all_labels.extend(y_class.cpu().numpy().tolist())

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
