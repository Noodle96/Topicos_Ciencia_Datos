# evaluation/plots.py

from typing import List

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


def plot_confusion_matrix(
    cm: np.ndarray,
    class_names: List[str],
    title: str = "Confusion Matrix",
) -> None:
    """
    Dibuja una matriz de confusión usando seaborn.

    Args:
        cm: np.ndarray de shape (C, C)
        class_names: nombres de las clases
        title: título del gráfico
    """
    plt.figure(figsize=(6, 5))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=class_names,
        yticklabels=class_names,
    )
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.title(title)
    plt.tight_layout()
    plt.show()
