from __future__ import annotations

from flask import Blueprint, jsonify

from backend.services.metadata_service import load_metadata_summary

metadata_blueprint: Blueprint = Blueprint("metadata", __name__)

# Uso: GET http://127.0.0.1:5000/api/metadata/summary
@metadata_blueprint.route("/api/metadata/summary", methods=["GET"])
def metadata_summary():
    """
    Endpoint que devuelve un resumen básico
    de metadata del dataset DEAP.
    """

    summary = load_metadata_summary()

    return jsonify(summary)
