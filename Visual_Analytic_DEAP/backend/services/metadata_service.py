from __future__ import annotations

import pandas as pd

from typing import Any, Dict

from backend.utils.paths import PARTICIPANT_RATINGS_FILE, VIDEO_LIST_FILE


def load_metadata_summary() -> Dict[str, Any]:
    """
    Carga un resumen básico de metadata del dataset DEAP.
    """

    # =========================
    # PARTICIPANT RATINGS
    # =========================

    participant_df: pd.DataFrame = pd.read_excel(PARTICIPANT_RATINGS_FILE)

    # =========================
    # VIDEO LIST
    # =========================

    video_df: pd.DataFrame = pd.read_excel(VIDEO_LIST_FILE)

    # =========================
    # RESUMEN
    # =========================

    summary: Dict[str, Any] = {
        "num_participants": int(participant_df["Participant_id"].nunique()),
        "num_trials": int(len(participant_df)),
        "num_experiment_videos": int(video_df["Experiment_id"].notna().sum()),
        "self_assessment_variables": [
            "Valence",
            "Arousal",
            "Dominance",
            "Liking",
            "Familiarity",
        ],
    }

    return summary
