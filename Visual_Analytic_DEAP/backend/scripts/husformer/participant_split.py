from __future__ import annotations

from . import config


def get_participant_split(participant_id: int) -> str:
    """
    Retorna a qué split (train/valid/test) pertenece un participante.

    Usa la asignación fija guardada en config.PARTICIPANT_TO_SPLIT, calculada
    una sola vez con semilla fija y "congelada" como constante para garantizar
    reproducibilidad exacta entre corridas (ver config.py para el detalle de
    cómo se generó).
    """
    if participant_id not in config.PARTICIPANT_TO_SPLIT:
        raise ValueError(
            f"Participante {participant_id} no tiene split asignado en config.py."
        )

    return config.PARTICIPANT_TO_SPLIT[participant_id]


def validate_full_participant_coverage() -> None:
    """
    Verifica que los 32 participantes de DEAP estén asignados a exactamente
    un split, sin duplicados ni participantes faltantes. Chequeo defensivo
    pensado para correrse antes de construir el dataset completo.
    """
    expected_participants: set[int] = set(range(1, 33))
    assigned_participants: set[int] = set(config.PARTICIPANT_TO_SPLIT.keys())

    missing_participants: set[int] = expected_participants - assigned_participants
    unexpected_participants: set[int] = assigned_participants - expected_participants

    if missing_participants:
        raise ValueError(
            f"Participantes sin split asignado: {sorted(missing_participants)}"
        )

    if unexpected_participants:
        raise ValueError(
            f"IDs de participante inesperados en config.py: "
            f"{sorted(unexpected_participants)}"
        )
