from __future__ import annotations

from pathlib import Path

# =========================
# ROOT DEL PROYECTO
# =========================

PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent.parent


# =========================
# DATASET
# =========================

DATASET_DIR: Path = PROJECT_ROOT / "dataset"
RAW_DIR: Path = DATASET_DIR / "raw"

METADATA_DIR: Path = RAW_DIR / "metadata"
BDF_DIR: Path = RAW_DIR / "bdf"


# =========================
# METADATA FILES
# =========================

PARTICIPANT_RATINGS_FILE: Path = METADATA_DIR / "participant_ratings.xls"
ONLINE_RATINGS_FILE: Path = METADATA_DIR / "online_ratings.xls"
VIDEO_LIST_FILE: Path = METADATA_DIR / "video_list_fixed.xlsx"
PARTICIPANT_QUESTIONNAIRE_FILE: Path = METADATA_DIR / "participant_questionnaire.xls"
