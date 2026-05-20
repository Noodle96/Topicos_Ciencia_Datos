from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from backend.utils.paths import PARTICIPANT_RATINGS_FILE, METADATA_DIR

VALID_AXIS_VARIABLES: set[str] = {
    "Valence",
    "Arousal",
    "Dominance",
    "Liking",
}

VIDEO_LIST_FILE = METADATA_DIR / "video_list_fixed.xlsx"


def load_emotion_space_points(
    x_variable: str,
    y_variable: str,
    participant: str = "all",
    experiment: str = "all",
) -> List[Dict[str, Any]]:
    """
    Carga los puntos del espacio emocional desde participant_ratings.xls.

    Cada punto representa un trial de un participante.
    """

    if x_variable not in VALID_AXIS_VARIABLES:
        raise ValueError(f"Variable X no válida: {x_variable}")

    if y_variable not in VALID_AXIS_VARIABLES:
        raise ValueError(f"Variable Y no válida: {y_variable}")

    ratings_df: pd.DataFrame = pd.read_excel(PARTICIPANT_RATINGS_FILE)

    video_df: pd.DataFrame = pd.read_excel(VIDEO_LIST_FILE)
    video_df = video_df[
        [
            "Experiment_id",
            "Lastfm_tag",
            "Artist",
            "Title",
        ]
    ].copy()

    ratings_df = ratings_df.merge(
        video_df,
        on="Experiment_id",
        how="left",
    )

    if participant != "all":
        participant_id: int = int(participant)
        ratings_df = ratings_df[ratings_df["Participant_id"] == participant_id]

    if experiment != "all":
        experiment_id: int = int(experiment)

        ratings_df = ratings_df[
            ratings_df["Experiment_id"] == experiment_id
        ]

    selected_columns: list[str] = [
        "Participant_id",
        "Trial",
        "Experiment_id",
        "Lastfm_tag",
        "Artist",
        "Title",
        "Valence",
        "Arousal",
        "Dominance",
        "Liking",
        "Familiarity",
    ]

    ratings_df = ratings_df[selected_columns].copy()

    ratings_df["x"] = ratings_df[x_variable]
    ratings_df["y"] = ratings_df[y_variable]

    ratings_df = ratings_df.dropna(subset=["x", "y"])

    # Convertimos valores NaN a None para que Flask genere JSON válido.
    # Esto es importante porque Familiarity tiene valores faltantes
    # en participantes como S02, S15 y S23.
    ratings_df = ratings_df.astype(object).where(
        pd.notnull(ratings_df),
        None,
    )

    points: List[Dict[str, Any]] = ratings_df.to_dict(orient="records")

    return points
