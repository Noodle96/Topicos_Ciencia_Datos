from __future__ import annotations

import os

# ⚠️ REAPLICADO (2026-07-22, más tarde el mismo día): esto se había
# revertido antes (ver historial en git) tras un diagnóstico standalone que
# no encontró el problema en el cálculo en sí. Se reaplica ahora porque el
# panorama cambió: A3 agrega un cálculo nuevo y pesado (matriz de similitud
# 1280x1280) que se recalcula en CADA carga de página, al mismo tiempo que
# el clustering de A2 -- dos cálculos numpy pesados corriendo en paralelo
# (threaded=True) es justo el escenario donde choques de BLAS son más
# probables, aunque antes (con un solo cálculo pesado a la vez) no se haya
# detectado. Forzar cada librería numérica a un solo hilo interno evita
# que se pisen entre sí sin necesidad de volver a un servidor de un solo
# hilo.
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

# ⚠️ NUEVO (2026-07-22) -- causa raíz más probable, encontrada revisando
# TODOS los logs de la sesión: `trial-clusters` (A2, KMeans/HDBSCAN vía
# scikit-learn/joblib) NUNCA aparece completado en ningún log, en ningún
# intento, mientras que trial-projection/tarea1-projection sí. joblib puede
# lanzar PROCESOS hijos (fork) para paralelizar el ajuste del modelo --
# hacer fork() de un proceso que tiene varios hilos vivos (nuestro Flask
# con threaded=True) es una causa clásica y bien documentada de deadlock, y
# puede congelar TODO el proceso (no solo esa request), explicando por qué
# hasta endpoints sin relación (trial-attention, la página misma) quedan
# colgados después. Esta variable le dice a joblib que use SOLO threads,
# nunca procesos -- debe fijarse ANTES de que joblib/sklearn se importen
# por primera vez (por eso acá arriba, antes de los imports de rutas/
# servicios más abajo).
os.environ.setdefault("JOBLIB_MULTIPROCESSING", "0")

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
    # threaded=False -- ARREGLO DEFINITIVO CONFIRMADO (2026-07-22).
    #
    # Historia resumida (detalle completo de cada paso intermedio en el
    # historial de git y en estado_proyecto.md, memoria del proyecto):
    # /api/husformer/trial-clusters (y más tarde también trial-pattern-
    # network, el endpoint nuevo de A3) se quedaban colgados de forma
    # reproducible -- a veces arrastrando con ellos a TODO el servidor,
    # incluso endpoints sin relación. Se probó, en orden, desactivar el
    # reloader, desactivar debug, limitar hilos de BLAS, evitar que joblib
    # haga fork -- ninguno solucionó el cuelgue de raíz.
    #
    # Diagnóstico decisivo: tanto llamar al servicio de clustering
    # directamente (diagnostico_trial_clusters_hang.py) como invocarlo vía
    # el test_client de Flask (diagnostico_flask_test_client.py) terminaban
    # rápido -- PERO los dos corren en el hilo principal. `threaded=True`
    # hace que el servidor real cree un HILO NUEVO por cada request, algo
    # que ningún diagnóstico anterior reproducía. Confirmado (2026-07-22,
    # con Russell probándolo en vivo): con threaded=False, el clustering
    # completa sin problema -- scikit-learn/joblib no es seguro corriendo
    # en un hilo secundario creado por el servidor de desarrollo de Flask.
    #
    # Costo aceptado: sin threading, un request lento bloquea a los demás
    # mientras corre -- aceptable, porque ya confirmamos que el clustering
    # en sí es rápido (~0.1-0.2s) una vez que corre en el hilo correcto.
    app.run(debug=False, port=5000, threaded=False, use_reloader=False)


# cd Visual_Analytic_DEAP
# python -m backend.app