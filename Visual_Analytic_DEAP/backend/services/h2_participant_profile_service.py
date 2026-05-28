from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from backend.utils.paths import DATASET_DIR


QUESTIONNAIRE_FILE: Path = (
    DATASET_DIR
    / "raw"
    / "metadata"
    / "participant_questionnaire.xls"
)


CATEGORICAL_ATTRIBUTES: list[str] = [
    "Gender",
    "Handedness",
    "Vision",
    "Vision Aid",
    "Education",
    "Alcohol consumption",
    "Coffee consumption",
    "Black/Green tea consumption",
    "Tobacco consumption",
    "Level of Alertness",
]


NUMERIC_ATTRIBUTES: list[str] = [
    "Age",
    "Hours of sleep last night",
    "Head circumference (cm)",
    "Distance Nasion-Inion (cm)",
    "Distance left - right jaw hinge (cm)",
]


def normalize_participant_id(value: Any) -> str:
    """Convierte un identificador de participante al formato SXX."""
    text_value: str = str(value).strip()

    if text_value.upper().startswith("S"):
        number_part: int = int(text_value[1:])
        return f"S{number_part:02d}"

    number_value: int = int(float(text_value))
    return f"S{number_value:02d}"


def clean_value(value: Any) -> Any:
    """Normaliza valores vacíos, NaN, N/A o XX como None."""
    if pd.isna(value):
        return None

    text_value: str = str(value).strip()

    if text_value in {"", "N/A", "NA", "nan", "NaN", "XX"}:
        return None

    return value


def load_questionnaire_dataframe() -> pd.DataFrame:
    """Carga participant_questionnaire.xls como DataFrame limpio."""
    if not QUESTIONNAIRE_FILE.exists():
        raise FileNotFoundError(
            f"No existe participant_questionnaire.xls: {QUESTIONNAIRE_FILE}"
        )

    dataframe: pd.DataFrame = pd.read_excel(QUESTIONNAIRE_FILE)

    dataframe["Participant_id"] = dataframe["Participant_id"].apply(
        normalize_participant_id
    )

    return dataframe


def build_participant_records(
    participant_ids: list[str],
) -> list[dict[str, Any]]:
    """Construye registros limpios para los participantes seleccionados."""
    dataframe: pd.DataFrame = load_questionnaire_dataframe()

    selected_ids: set[str] = {
        normalize_participant_id(participant_id)
        for participant_id in participant_ids
    }

    filtered_dataframe: pd.DataFrame = dataframe[
        dataframe["Participant_id"].isin(selected_ids)
    ]

    records: list[dict[str, Any]] = []

    for _, row in filtered_dataframe.iterrows():
        record: dict[str, Any] = {
            "Participant_id": row["Participant_id"],
            "categorical": {},
            "numeric": {},
        }

        for attribute in CATEGORICAL_ATTRIBUTES:
            record["categorical"][attribute] = clean_value(
                row.get(attribute)
            )

        for attribute in NUMERIC_ATTRIBUTES:
            cleaned_value: Any = clean_value(row.get(attribute))

            try:
                record["numeric"][attribute] = (
                    float(cleaned_value)
                    if cleaned_value is not None
                    else None
                )
            except ValueError:
                record["numeric"][attribute] = None

        records.append(record)

    records.sort(key=lambda item: item["Participant_id"])

    return records


def build_common_patterns(
    records: list[dict[str, Any]],
) -> list[str]:
    """
    Detecta patrones comunes simples entre participantes seleccionados.

    Solo considera atributos categóricos con valores no nulos.
    """
    common_patterns: list[str] = []

    if len(records) < 2:
        return common_patterns

    for attribute in CATEGORICAL_ATTRIBUTES:
        values: list[Any] = [
            record["categorical"].get(attribute)
            for record in records
        ]

        non_null_values: list[Any] = [
            value for value in values if value is not None
        ]

        if len(non_null_values) != len(records):
            continue

        unique_values: set[Any] = set(non_null_values)

        if len(unique_values) == 1:
            common_value: Any = non_null_values[0]
            common_patterns.append(
                f"All selected participants share {attribute}: {common_value}."
            )

    return common_patterns


def build_numeric_ranges(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Construye rangos numéricos para comparar participantes."""
    ranges: list[dict[str, Any]] = []

    for attribute in NUMERIC_ATTRIBUTES:
        values: list[float] = []

        for record in records:
            value: float | None = record["numeric"].get(attribute)

            if value is not None:
                values.append(value)

        if not values:
            ranges.append(
                {
                    "attribute": attribute,
                    "min": None,
                    "max": None,
                    "range": None,
                }
            )
            continue

        min_value: float = min(values)
        max_value: float = max(values)

        ranges.append(
            {
                "attribute": attribute,
                "min": min_value,
                "max": max_value,
                "range": max_value - min_value,
            }
        )

    return ranges


def build_participant_profile_comparison(
    participant_ids: list[str],
) -> dict[str, Any]:
    """
    Construye una comparación de perfiles humanos para participantes seleccionados.

    La respuesta está pensada para visualizar:
    - patrones comunes;
    - atributos categóricos;
    - atributos numéricos;
    - valores faltantes.
    """
    records: list[dict[str, Any]] = build_participant_records(
        participant_ids=participant_ids
    )

    result: dict[str, Any] = {
        "selected_participants": [
            record["Participant_id"] for record in records
        ],
        "categorical_attributes": CATEGORICAL_ATTRIBUTES,
        "numeric_attributes": NUMERIC_ATTRIBUTES,
        "records": records,
        "common_patterns": build_common_patterns(records),
        "numeric_ranges": build_numeric_ranges(records),
    }

    return result