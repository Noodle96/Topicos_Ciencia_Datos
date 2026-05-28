from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.utils.paths import DATASET_DIR


RELATIONSHIPS_DIR: Path = DATASET_DIR / "processed" / "relationships"

CHANNEL_GROUPS: dict[str, list[str]] = {
    "EEG": [
        "Fp1", "AF3", "F7", "F3", "FC1", "FC5", "T7", "C3",
        "CP1", "CP5", "P7", "P3", "Pz", "PO3", "O1", "Oz",
        "O2", "PO4", "P4", "P8", "CP6", "CP2", "C4", "T8",
        "FC6", "FC2", "F4", "F8", "AF4", "Fp2", "Fz", "Cz",
    ],
    "EXG": [
        "EXG1", "EXG2", "EXG3", "EXG4",
        "EXG5", "EXG6", "EXG7", "EXG8",
    ],
    "PERIPHERAL": [
        "GSR1", "Resp", "Plet", "Temp",
    ],
}


def load_json(file_path: Path) -> dict[str, Any]:
    """Carga un archivo JSON y devuelve su contenido como diccionario."""
    with file_path.open("r", encoding="utf-8") as file:
        data: dict[str, Any] = json.load(file)

    return data


def get_relationship_file_path(
    participant_id: int,
    trial: int,
) -> Path:
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
    Carga el archivo JSON de relaciones H2 correspondiente
    a un participante y trial procesado.
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


def validate_group_and_channel(
    row_group: str,
    reference_group: str,
    reference_channel: str,
) -> None:
    """
    Valida que los grupos existan y que el canal de referencia
    pertenezca al grupo de referencia seleccionado.
    """
    if row_group not in CHANNEL_GROUPS:
        raise ValueError(f"Grupo Y inválido: {row_group}")

    if reference_group not in CHANNEL_GROUPS:
        raise ValueError(f"Grupo de referencia inválido: {reference_group}")

    if reference_channel not in CHANNEL_GROUPS[reference_group]:
        raise ValueError(
            f"El canal {reference_channel} no pertenece al grupo "
            f"{reference_group}"
        )


def find_relationship_correlation(
    relationships: list[dict[str, Any]],
    row_group: str,
    row_channel: str,
    reference_group: str,
    reference_channel: str,
) -> float | None:
    """
    Busca la correlación entre un canal de fila y un canal de referencia.

    El preprocessing guarda relaciones por pares de grupos en una dirección
    específica. Esta función revisa ambas direcciones para que el frontend
    pueda pedir row_group/reference_group sin preocuparse por el orden.
    """
    for item in relationships:
        source_group: str = str(item.get("source_group"))
        source_channel: str = str(item.get("source_channel"))
        target_group: str = str(item.get("target_group"))
        target_channel: str = str(item.get("target_channel"))

        is_direct_match: bool = (
            source_group == row_group
            and source_channel == row_channel
            and target_group == reference_group
            and target_channel == reference_channel
        )

        is_reverse_match: bool = (
            source_group == reference_group
            and source_channel == reference_channel
            and target_group == row_group
            and target_channel == row_channel
        )

        if is_direct_match or is_reverse_match:
            correlation: Any = item.get("correlation")

            if correlation is None:
                return None

            return float(correlation)

    return None


def build_cross_participant_relationship_matrix(
    experiment_id: int,
    row_group: str,
    reference_group: str,
    reference_channel: str,
) -> dict[str, Any]:
    """
    Construye una matriz de relaciones por participantes.

    Filas:
    - canales del grupo Y seleccionado.

    Columnas:
    - participantes S01...S32.

    Celda:
    - correlación entre row_channel y reference_channel
      para un participante durante un experimento específico.
    """
    validate_group_and_channel(
        row_group=row_group,
        reference_group=reference_group,
        reference_channel=reference_channel,
    )

    row_channels: list[str] = CHANNEL_GROUPS[row_group]
    participants: list[dict[str, Any]] = []
    cells: list[dict[str, Any]] = []

    for participant_id in range(1, 33):
        participant_label: str = f"S{participant_id:02d}"

        try:
            trial: int = find_trial_by_experiment(
                participant_id=participant_id,
                experiment_id=experiment_id,
            )

            trial_data: dict[str, Any] = load_trial_relationships(
                participant_id=participant_id,
                trial=trial,
            )

            relationships: list[dict[str, Any]] = trial_data.get(
                "relationships",
                [],
            )

            participants.append(
                {
                    "participant_id": participant_id,
                    "participant_label": participant_label,
                    "trial": trial,
                    "available": True,
                }
            )

            for row_channel in row_channels:
                correlation: float | None = find_relationship_correlation(
                    relationships=relationships,
                    row_group=row_group,
                    row_channel=row_channel,
                    reference_group=reference_group,
                    reference_channel=reference_channel,
                )

                cells.append(
                    {
                        "participant_id": participant_id,
                        "participant_label": participant_label,
                        "trial": trial,
                        "row_group": row_group,
                        "row_channel": row_channel,
                        "reference_group": reference_group,
                        "reference_channel": reference_channel,
                        "correlation": correlation,
                        "abs_correlation": (
                            abs(correlation)
                            if correlation is not None
                            else None
                        ),
                    }
                )

        except FileNotFoundError:
            participants.append(
                {
                    "participant_id": participant_id,
                    "participant_label": participant_label,
                    "trial": None,
                    "available": False,
                }
            )

            for row_channel in row_channels:
                cells.append(
                    {
                        "participant_id": participant_id,
                        "participant_label": participant_label,
                        "trial": None,
                        "row_group": row_group,
                        "row_channel": row_channel,
                        "reference_group": reference_group,
                        "reference_channel": reference_channel,
                        "correlation": None,
                        "abs_correlation": None,
                    }
                )

    result: dict[str, Any] = {
        "experiment_id": experiment_id,
        "phase": "during",
        "method": "pearson",
        "row_group": row_group,
        "reference_group": reference_group,
        "reference_channel": reference_channel,
        "row_channels": row_channels,
        "participants": participants,
        "cells": cells,
    }

    return result