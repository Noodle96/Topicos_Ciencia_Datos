"""
Smoke test + benchmark para el fix de atencion cross-modal (bug #6, 2026-07-06).

Este script NO entrena nada -- carga el checkpoint que Russell ya genero
(output/hus.pt, entrenado con d_m=40 + el fix de return_attn en models.py/
transformer.py) y hace dos cosas:

1. Corre UN solo batch pequeno con return_attn=True, para confirmar que esa
   rama nueva de HUSFORMERModel.forward() (el diccionario de atencion)
   funciona sin errores de forma. Esto ya se confirmo el 2026-07-06 (shapes
   correctas, sin traceback) -- se deja aqui sin cambios.

2. NUEVO (2026-07-06, segunda vuelta): mide el tiempo real de una pasada
   hacia adelante (forward, sin entrenar) para 1 SOLA ventana, con y sin
   return_attn=True. Esto reemplaza una estimacion ("deberia tardar menos de
   100ms") por un numero medido en la maquina real de Russell -- necesario
   para decidir si calcular la atencion cruda y detallada "al vuelo" (cuando
   el usuario abre una ventana puntual en el sistema) es viable en terminos
   de latencia, en vez de precalcularla y guardarla para todo el dataset
   (que pesaria >1TB, ver conversacion). Se hace un warmup de 3 corridas
   (descartadas del promedio, porque la primera llamada a CUDA suele incluir
   inicializacion perezosa que no se repite despues) y luego 20 corridas
   medidas, reportando promedio/min/max en milisegundos.

Uso: parado en husformer_deap_va/, con el mismo entorno virtual activado:
    python test_return_attn.py
"""
import argparse
import time

import torch
from torch.utils.data import DataLoader

from src.utils import get_data

DATA_PATH = "data"
DATASET = "husformer"
CHECKPOINT_PATH = "output/hus.pt"
SMOKE_BATCH_SIZE = 4  # chico a proposito -- esto no es una prueba de rendimiento
BENCHMARK_WARMUP_RUNS = 3
BENCHMARK_MEASURED_RUNS = 20

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
    "(atencion cross-modal) queda validado con datos reales."
)


def _time_forward_ms(m1_1, m2_1, m3_1, m4_1, m5_1, return_attn):
    """Mide en milisegundos una sola pasada hacia adelante (sin gradiente).

    FIX (2026-07-06, husformer_deap_va): torch.cuda.synchronize() es
    necesario ANTES de leer el reloj (start y end) porque las operaciones en
    GPU son asincronas -- sin sincronizar, time.time() mediria solo cuanto
    tarda Python en *encolar* la operacion, no cuanto tarda la GPU en
    terminarla de verdad, dando un numero falsamente bajo.
    """
    if use_cuda:
        torch.cuda.synchronize()
    start = time.time()
    with torch.no_grad():
        model(m1_1, m2_1, m3_1, m4_1, m5_1, return_attn=return_attn)
    if use_cuda:
        torch.cuda.synchronize()
    end = time.time()
    return (end - start) * 1000.0


# Una sola ventana (batch=1), simulando "el usuario abre 1 ventana puntual
# en el sistema" -- el escenario real de calcular la atencion al vuelo.
m1_1, m2_1, m3_1, m4_1, m5_1 = m1[0:1], m2[0:1], m3[0:1], m4[0:1], m5[0:1]

print(
    f"\n--- Benchmark: tiempo de 1 pasada hacia adelante, batch=1 "
    f"({BENCHMARK_WARMUP_RUNS} warmup descartadas + {BENCHMARK_MEASURED_RUNS} medidas) ---"
)

for label, return_attn in [("return_attn=False", False), ("return_attn=True", True)]:
    for _ in range(BENCHMARK_WARMUP_RUNS):
        _time_forward_ms(m1_1, m2_1, m3_1, m4_1, m5_1, return_attn)

    times_ms = [
        _time_forward_ms(m1_1, m2_1, m3_1, m4_1, m5_1, return_attn)
        for _ in range(BENCHMARK_MEASURED_RUNS)
    ]
    avg_ms = sum(times_ms) / len(times_ms)
    print(
        f"  {label:18s}: promedio {avg_ms:7.2f} ms   "
        f"(min {min(times_ms):7.2f} ms, max {max(times_ms):7.2f} ms)"
    )

print(
    "\nEste 'promedio' con return_attn=True es la latencia real que tendria "
    "calcular la atencion cruda y detallada AL VUELO para 1 sola ventana "
    "(sin precalcularla ni guardarla) -- lo que decide si es viable hacerlo "
    "bajo demanda en el sistema en vez de precomputar y guardar >1TB."
)
