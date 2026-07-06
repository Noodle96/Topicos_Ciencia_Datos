"""
Smoke test para el fix de atencion cross-modal (bug #6, 2026-07-06).

Este script NO entrena nada -- carga el checkpoint que Russell ya genero
(output/hus.pt, entrenado con d_m=40 + el fix de return_attn en models.py/
transformer.py) y corre UN solo batch pequeno con return_attn=True, para
confirmar que esa rama nueva de HUSFORMERModel.forward() (el diccionario de
atencion) funciona sin errores de forma antes de escribir el script real de
extraccion de representaciones (candidato:
backend/scripts/husformer/extract_representations.py).

Por que hace falta este script aparte: la corrida de entrenamiento normal
(main.py -> train.py -> test.py) NUNCA llama a return_attn=True -- esos 3
archivos no cambiaron. Por lo tanto, aunque la corrida de 1 epoca ya
confirmo que el resto del modelo (d_m=40, combined_dim) funciona bien
(n_parameters=596243 exacto, sin errores de shape), la rama return_attn=True
en si NO se ha ejecutado ni una sola vez con datos reales todavia -- ni en
el sandbox de Claude (sin PyTorch instalado ahi) ni en la maquina de
Russell (main.py no la usa). Este script es la primera ejecucion real de
esa rama, y corre en segundos (un solo batch chico, sin entrenamiento).

Uso: parado en husformer_deap_va/, con el mismo entorno virtual activado:
    python test_return_attn.py
"""
import argparse

import torch
from torch.utils.data import DataLoader

from src.utils import get_data

DATA_PATH = "data"
DATASET = "husformer"
CHECKPOINT_PATH = "output/hus.pt"
SMOKE_BATCH_SIZE = 4  # chico a proposito -- esto no es una prueba de rendimiento

use_cuda = torch.cuda.is_available()
torch.set_default_tensor_type("torch.cuda.FloatTensor" if use_cuda else "torch.FloatTensor")

print(f"Cargando datos de test cacheados desde '{DATA_PATH}/{DATASET}_test.dt'...")
data_args = argparse.Namespace(data_path=DATA_PATH)
test_data = get_data(data_args, DATASET, "test")

generator = torch.Generator(device="cuda") if use_cuda else None
test_loader = DataLoader(test_data, batch_size=SMOKE_BATCH_SIZE, shuffle=True, generator=generator)

print(f"Cargando el modelo entrenado desde '{CHECKPOINT_PATH}'...")
model = torch.load(CHECKPOINT_PATH, weights_only=False)
model.eval()

batch_X, batch_Y, batch_META = next(iter(test_loader))
sample_ind, m1, m2, m3, m4, m5 = batch_X
if use_cuda:
    m1, m2, m3, m4, m5 = m1.cuda(), m2.cuda(), m3.cuda(), m4.cuda(), m5.cuda()

print(
    f"\nBatch de prueba: {m1.size(0)} ventanas "
    f"(shapes: m1={tuple(m1.shape)}, m2={tuple(m2.shape)}, m3={tuple(m3.shape)}, "
    f"m4={tuple(m4.shape)}, m5={tuple(m5.shape)})"
)

with torch.no_grad():
    output, last_hs, attn_weights = model(m1, m2, m3, m4, m5, return_attn=True)

print("\n--- return_attn=True: SIN ERRORES ---")
print(f"output.shape:  {tuple(output.shape)}   (esperado: (batch, 3) -- 3 clases de valencia)")
print(f"last_hs.shape: {tuple(last_hs.shape)}   (esperado: (batch, 40) -- d_m=40)")

print(f"\nClaves de attn_weights: {list(attn_weights.keys())}")
for key, layers in attn_weights.items():
    shapes = [tuple(layer.shape) for layer in layers]
    print(f"  attn_weights['{key}']: lista de {len(layers)} capas, shapes por capa: {shapes}")

print(
    "\nSi todo lo de arriba corrio sin traceback, el fix del bug #6 "
    "(atencion cross-modal) queda validado con datos reales, y ya se puede "
    "empezar a escribir el script de extraccion de representaciones sobre "
    "esta misma base."
)
