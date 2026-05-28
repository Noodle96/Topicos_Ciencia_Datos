from __future__ import annotations

from typing import Any

from flask import Blueprint, jsonify, request

from backend.services.h2_participant_profile_service import (
    build_participant_profile_comparison,
)


h2_participant_profile_bp: Blueprint = Blueprint(
    "h2_participant_profile",
    __name__,
)


# Uso:
# /api/h2/participant-profiles?participants=S07,S18,S21
@h2_participant_profile_bp.route(
    "/participant-profiles",
    methods=["GET"],
)
def get_h2_participant_profiles() -> tuple[Any, int]:
    """
    Devuelve una comparación de metadata humana para participantes seleccionados.
    """
    participants_arg: str | None = request.args.get("participants")

    if participants_arg is None or participants_arg.strip() == "":
        return jsonify(
            {
                "error": "Parámetro requerido: participants."
            }
        ), 400

    try:
        participant_ids: list[str] = [
            participant.strip()
            for participant in participants_arg.split(",")
            if participant.strip()
        ]

        data: dict[str, Any] = build_participant_profile_comparison(
            participant_ids=participant_ids
        )

        return jsonify(data), 200

    except FileNotFoundError as error:
        return jsonify({"error": str(error)}), 404

    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    except Exception as error:
        return jsonify(
            {
                "error": (
                    "Error interno al comparar perfiles de participantes: "
                    f"{error}"
                )
            }
        ), 500