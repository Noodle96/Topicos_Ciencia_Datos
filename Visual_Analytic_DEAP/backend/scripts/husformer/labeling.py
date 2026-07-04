from __future__ import annotations


def valence_to_label(valence: float) -> int:
    """
    Convierte una valencia continua (escala 1-9 de participant_ratings) en una
    etiqueta discreta de 3 clases, con el mismo esquema que usa el código de
    ejemplo original de Husformer para DEAP (make_data/Pre-DEAP.py):

    - Valencia baja  (1 a 3) -> -1
    - Valencia media (4 a 6) ->  1
    - Valencia alta  (7 a 9) ->  2

    Lanza ValueError si la valencia está fuera del rango esperado [1, 9].
    """
    rounded_valence: int = round(valence)

    if 1 <= rounded_valence <= 3:
        return -1
    elif 4 <= rounded_valence <= 6:
        return 1
    elif 7 <= rounded_valence <= 9:
        return 2

    raise ValueError(
        f"Valencia fuera de rango esperado [1, 9]: {valence} "
        f"(redondeada: {rounded_valence})."
    )
