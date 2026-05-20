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
    app.run(debug=True, port=5000)


# cd Visual_Analytic_DEAP
# python -m backend.app