from __future__ import annotations

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from pathlib import Path
from typing import Any

from backend.routes.metadata_routes import metadata_blueprint
from backend.routes.emotion_routes import emotion_blueprint
from backend.routes.signal_routes import signal_blueprint

# TO H2
from backend.routes.h2_relationship_routes import (h2_relationship_bp,)
from backend.routes.h2_timeseries_routes import (h2_timeseries_bp,)
from backend.routes.h2_local_relationship_routes import (h2_local_relationship_bp,)
from backend.routes.h2_participant_profile_routes import (h2_participant_profile_bp,)

from backend.routes.tarea1_routes import tarea1_bp

# TO HUSFORMER (Vista A/B/C)
from backend.routes.husformer_trial_routes import husformer_trial_bp
from backend.routes.husformer_attention_routes import husformer_attention_bp

BASE_DIR: Path = Path(__file__).resolve().parent.parent
FRONTEND_DIR: Path = BASE_DIR / "frontend"


def create_app() -> Flask:
    """
    Crea y configura la aplicación Flask principal.
    """
    app: Flask = Flask(__name__)
    CORS(app)

    app.register_blueprint(metadata_blueprint)
    app.register_blueprint(emotion_blueprint)
    app.register_blueprint(signal_blueprint)
    
    # TO H2
    app.register_blueprint(h2_relationship_bp,url_prefix="/api/h2",)
    app.register_blueprint(h2_timeseries_bp,url_prefix="/api/h2",)
    app.register_blueprint(h2_local_relationship_bp,url_prefix="/api/h2",)
    app.register_blueprint(h2_participant_profile_bp,url_prefix="/api/h2",)
    
    # para tarea 1
    app.register_blueprint( tarea1_bp, url_prefix="/api/tarea1",)

    # para Husformer (Vista A/B/C) -- Vista A (trial-projection/trial-
    # clusters) + Vista B (trial-attention). Vista C se agrega como
    # blueprint nuevo bajo el mismo url_prefix cuando se implemente (mismo
    # patrón que los 4 blueprints de H2 arriba).
    app.register_blueprint(husformer_trial_bp, url_prefix="/api/husformer",)
    app.register_blueprint(husformer_attention_bp, url_prefix="/api/husformer",)

    @app.route("/api/health", methods=["GET"])
    def health_check() -> Any:
        """
        Endpoint simple para verificar que el backend está funcionando.
        """
        return jsonify(
            {
                "status": "ok",
                "message": "Backend Flask conectado correctamente",
                "project": "Visual_Analytic_DEAP",
            }
        )

    @app.route("/", methods=["GET"])
    def serve_index() -> Any:
        """
        Sirve la página principal del frontend.
        """
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.route("/<path:filename>", methods=["GET"])
    def serve_frontend_files(filename: str) -> Any:
        """
        Sirve archivos estáticos del frontend: CSS, JS, etc.
        """
        return send_from_directory(FRONTEND_DIR, filename)

    return app


app: Flask = create_app()


if __name__ == "__main__":
    # threaded=True (2026-07-15): mitigación agregada al diagnosticar que
    # /api/husformer/trial-clusters se quedaba colgado (probable deadlock de
    # joblib/sklearn con el reloader de Flask, ver estado_proyecto.md) -- sin
    # esto, el servidor de desarrollo es de UN SOLO HILO, así que un request
    # colgado bloqueaba TODOS los demás endpoints (H1/H2/Tarea1 incluidos,
    # aunque no tengan nada que ver con clustering). Con threaded=True, un
    # request colgado ya no tumba el resto del servidor -- pero esto NO
    # arregla la causa raíz del colgado en sí, solo contiene el daño.
    app.run(debug=True, port=5000, threaded=True)


# cd Visual_Analytic_DEAP
# python -m backend.app