"""
Diagnostico standalone (NO pasa por Flask) para aislar si el cuelgue de
/api/husformer/trial-attention (confirmado con curl, 2026-07-22 -- el
request llega al backend y nunca responde, CPU en reposo) esta en el
CODIGO/DATO en si, o es especifico de como Flask lo esta sirviendo
(threading, reloader, etc).

Correr desde la raiz de Visual_Analytic_DEAP:
    python diagnostico_trial_attention_hang.py
"""
import time

print("Importando el servicio...")
t0 = time.time()

from backend.services.husformer_attention_service import load_husformer_trial_attention

print(f"Import listo ({time.time() - t0:.2f}s). Llamando a load_husformer_trial_attention(22, 18)...")
t0 = time.time()

data = load_husformer_trial_attention(participant_id=22, trial=18)

print(f"LISTO en {time.time() - t0:.2f}s. num_windows={data['num_windows']}")
