"""
Diagnostico standalone -- usa el "test client" de Flask, que llama a la app
directamente en memoria SIN pasar por sockets/red real. Si esto funciona
rapido pero el servidor real (curl/navegador) sigue colgado, el problema
esta especificamente en la capa de red del servidor de desarrollo
(Werkzeug), no en el despacho de rutas de Flask ni en el codigo de las
vistas.

Correr desde la raiz de Visual_Analytic_DEAP:
    python diagnostico_flask_test_client.py
"""
import time

print("Importando create_app...")
t0 = time.time()

from backend.app import create_app

print(f"Import listo ({time.time() - t0:.2f}s). Creando la app...")
t0 = time.time()

app = create_app()
client = app.test_client()

print(f"App creada ({time.time() - t0:.2f}s). Llamando a /api/husformer/trial-attention vía test_client...")
t0 = time.time()

response = client.get("/api/husformer/trial-attention?participant_id=22&trial=18")

print(f"LISTO en {time.time() - t0:.2f}s. status={response.status_code}")
