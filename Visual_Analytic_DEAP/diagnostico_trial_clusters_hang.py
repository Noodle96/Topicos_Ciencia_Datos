"""
Diagnostico standalone (NO pasa por Flask) para aislar el cuelgue de
/api/husformer/trial-clusters -- el unico endpoint que, en TODOS los logs
de esta sesion, nunca aparecio completado ni una sola vez. Mismo patron que
diagnostico_trial_attention_hang.py, pero apuntado al endpoint que
realmente falla (antes se probo con trial-attention por error).

Correr desde la raiz de Visual_Analytic_DEAP:
    python diagnostico_trial_clusters_hang.py
"""
import time

print("Importando el servicio...")
t0 = time.time()

from backend.services.husformer_trial_service import load_husformer_trial_clusters

print(f"Import listo ({time.time() - t0:.2f}s). Llamando a load_husformer_trial_clusters('kmeans', 3)...")
t0 = time.time()

data = load_husformer_trial_clusters(method="kmeans", param_value=3)

print(f"LISTO en {time.time() - t0:.2f}s. num_clusters={data.get('num_clusters')}")
