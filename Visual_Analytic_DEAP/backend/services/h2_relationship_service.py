from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.utils.paths import DATASET_DIR


RELATIONSHIPS_DIR: Path = DATASET_DIR / "processed" / "relationships"


def load_json(file_path: Path) -> dict[str, Any]:
    """Carga un archivo JSON y devuelve su contenido como diccionario."""
    with file_path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = json.load(file)

    return data


def get_relationship_file_path(participant_id: int, trial: int) -> Path:
    """
    Construye la ruta del archivo de relaciones H2
    correspondiente a un participante y trial.
    """
    participant_code: str = f"s{participant_id:02d}"
    file_name: str = f"trial_{trial:02d}_relationships.json"

    return RELATIONSHIPS_DIR / participant_code / file_name


def load_trial_relationships(
    participant_id: int,
    trial: int,
) -> dict[str, Any]:
    """
    Carga el archivo JSON de relaciones EEG ↔ periféricas
    correspondiente a un trial procesado.
    """
    relationship_file: Path = get_relationship_file_path(
        participant_id=participant_id,
        trial=trial,
    )

    if not relationship_file.exists():
        raise FileNotFoundError(
            f"No existe archivo de relaciones: {relationship_file}"
        )

    return load_json(relationship_file)

def find_trial_by_experiment(
    participant_id: int,
    experiment_id: int,
) -> int:
    """
    Busca qué trial corresponde a un Experiment_id para un participante.

    En DEAP:
    - Experiment_id representa el estímulo real.
    - Trial representa el orden local de presentación para cada participante.
    """
    participant_code: str = f"s{participant_id:02d}"
    participant_dir: Path = RELATIONSHIPS_DIR / participant_code

    if not participant_dir.exists():
        raise FileNotFoundError(
            f"No existe carpeta de relaciones: {participant_dir}"
        )

    relationship_files: list[Path] = sorted(
        participant_dir.glob("trial_*_relationships.json")
    )

    for relationship_file in relationship_files:
        data: dict[str, Any] = load_json(relationship_file)

        if int(data.get("experiment_id")) == experiment_id:
            return int(data.get("trial"))

    raise FileNotFoundError(
        "No se encontró un trial para "
        f"participant={participant_id}, experiment={experiment_id}"
    )


def build_relationship_matrix(
    participant_id: int,
    trial: int,
) -> dict[str, Any]:
    """
    Construye una estructura tipo matriz EEG × periféricas.

    Esta salida está diseñada específicamente para
    visualización en D3.js.

    Retorna:
    - eeg_channels
    - peripheral_channels
    - cells
    """
    data: dict[str, Any] = load_trial_relationships(
        participant_id=participant_id,
        trial=trial,
    )

    relationships: list[dict[str, Any]] = data.get(
        "relationships",
        [],
    )

    eeg_channels: list[str] = sorted(
        {
            str(item["eeg_channel"])
            for item in relationships
        }
    )

    peripheral_channels: list[str] = sorted(
        {
            str(item["peripheral_channel"])
            for item in relationships
        }
    )

    cells: list[dict[str, Any]] = []

    for item in relationships:
        correlation: float | None = item["correlation"]

        cells.append(
            {
                "eeg_channel": item["eeg_channel"],
                "peripheral_channel": item["peripheral_channel"],
                "correlation": correlation,
                "abs_correlation": (
                    abs(float(correlation))
                    if correlation is not None
                    else None
                ),
            }
        )

    result: dict[str, Any] = {
        "participant_id": data.get("participant_id"),
        "trial": data.get("trial"),
        "experiment_id": data.get("experiment_id"),
        "phase": data.get("phase"),
        "method": data.get("method"),
        "during_start_sec": data.get("during_start_sec"),
        "during_end_sec": data.get("during_end_sec"),
        "eeg_channels": eeg_channels,
        "peripheral_channels": peripheral_channels,
        "cells": cells,
    }

    return result