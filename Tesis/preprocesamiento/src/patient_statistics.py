# RAIZ/preprocesamiento/src/patient_statistics.py

from typing import Dict, List, Tuple
from collections import defaultdict

def accumulate_patient_label_stats(
    patient_id: str,
    labels: List[Tuple[int, int, str]],
    stats: Dict[str, Dict[str, float]],
) -> None:
    """
    Acumula segundos de seizure y bckg para un paciente.

    stats[patient_id] = {
        "seizure_seconds": float,
        "bckg_seconds": float
    }
    """
    if patient_id not in stats:
        stats[patient_id] = {
            "seizure_seconds": 0.0,
            "bckg_seconds": 0.0,
        }

    for start, end, label in labels:
        duration: float = float(end - start)
        if label == "seiz":
            stats[patient_id]["seizure_seconds"] += duration
        elif label == "bckg":
            stats[patient_id]["bckg_seconds"] += duration


def build_patient_ranking(
    stats: Dict[str, Dict[str, float]]
) -> List[Dict[str, float]]:
    """
    Devuelve lista ordenada por seizure_seconds (desc).
    """
    ranking: List[Dict[str, float]] = []

    for patient_id, values in stats.items():
        ranking.append({
            "patient_id": patient_id,
            "seizure_seconds": values["seizure_seconds"],
            "seizure_minutes": values["seizure_seconds"] / 60.0,
            "bckg_seconds": values["bckg_seconds"],
            "bckg_minutes": values["bckg_seconds"] / 60.0,
        })

    ranking.sort(
        key=lambda x: x["seizure_seconds"],
        reverse=True,
    )
    return ranking

import json
import os

def save_patient_ranking_json(
    ranking: List[Dict[str, float]],
    output_path: str,
) -> None:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ranking, f, indent=2)