"""
Diagnostico standalone (NO depende de Flask ni de ningun servicio) para
verificar la observacion de Russell (2026-07-22): la matriz de C1
(attn_cross_summary) parece casi no cambiar entre ventanas de un mismo
trial (seg 1 a 60).

Mismo tipo de chequeo que diagnostico_attn_final.py (el que encontro el bug
real de la mascara causal) -- comparamos:
  (a) variabilidad DENTRO de un trial: std de attn_cross_summary entre sus
      ~60 ventanas.
  (b) variabilidad ENTRE trials: std de la matriz PROMEDIO de cada trial,
      calculada sobre todos los trials del dataset.

Si (a) << (b): la observacion de Russell es correcta -- la firma de fusion
cross-modal es basicamente una propiedad ESTABLE del trial, no algo que
fluctue ventana a ventana. Eso justifica rediseñar Vista C para comparar
TRIALS entre si, en vez de ventanas dentro de un trial.

Si (a) es del mismo orden que (b), o si (a) es ~0 en terminos ABSOLUTOS
(no solo relativos) -- podria ser otro bug de escala/legibilidad como el de
la mascara causal, no una caracteristica real del dato. Hay que mirar los
numeros con cuidado, no solo la conclusion.

Tambien se corre el mismo calculo sobre attn_final_summary (el dato de
B1/B2) como punto de comparacion -- para ver si esta "estabilidad dentro
del trial" es especial de attn_cross_summary o es igual en los dos.

Correr desde la raiz de Visual_Analytic_DEAP:
    python diagnostico_attn_cross.py
"""
import numpy as np
import pandas as pd

MANIFEST_PATH = "dataset/processed/representation_inputs/husformer_manifest.csv"
REPR_DIR = "dataset/processed/representations/husformer"

manifest = pd.read_csv(MANIFEST_PATH)
print("manifest:", manifest.shape, "columnas:", manifest.columns.tolist())
print()


def cargar_attn(split, key):
    data = np.load(f"{REPR_DIR}/{split}_representations.npz")
    return data[key]  # (N_split, 5, 5)


def analizar(key, etiqueta):
    print(f"=== {etiqueta} ({key}) ===")

    # ---- 1) Casos de ejemplo: variabilidad DENTRO de un trial ----
    casos = [(1, 1), (1, 9), (5, 20), (10, 15)]
    stds_intra_ejemplos = []

    for pid, trial in casos:
        rows = manifest[
            (manifest["participant_id"] == pid) & (manifest["trial"] == trial)
        ].sort_values("window_index")

        if rows.empty:
            print(f"  S{pid:02d} T{trial}: no encontrado en manifest")
            continue

        split = rows["split"].iloc[0]
        attn = cargar_attn(split, key)
        local_ids = rows["local_id"].to_numpy()
        trial_attn = attn[local_ids]  # (n_windows, 5, 5)

        std_intra = trial_attn.std(axis=0)  # (5, 5) -- std entre ventanas
        stds_intra_ejemplos.append(std_intra.mean())

        print(f"  S{pid:02d} T{trial}: n_windows={len(rows)}")
        print(f"    media sobre ventanas (5x5):\n{trial_attn.mean(axis=0)}")
        print(f"    std ENTRE ventanas del mismo trial (5x5):\n{std_intra}")
        print(f"    std promedio (escalar, resume la matriz de arriba): {std_intra.mean():.8f}")
        print()

    # ---- 2) TODOS los trials: variabilidad ENTRE trials ----
    medias_por_trial = []

    for split in manifest["split"].unique():
        attn = cargar_attn(split, key)
        sub = manifest[manifest["split"] == split]

        for (pid, trial), grupo in sub.groupby(["participant_id", "trial"]):
            local_ids = grupo["local_id"].to_numpy()
            media_trial = attn[local_ids].mean(axis=0)  # (5, 5)
            medias_por_trial.append(media_trial)

    medias_por_trial = np.stack(medias_por_trial, axis=0)  # (n_trials, 5, 5)
    std_entre_trials = medias_por_trial.std(axis=0)  # (5, 5)

    print(f"  n_trials analizados: {medias_por_trial.shape[0]}")
    print(f"  std ENTRE trials (de la media de cada trial), matriz 5x5:\n{std_entre_trials}")
    print(f"  std ENTRE trials promedio (escalar): {std_entre_trials.mean():.8f}")
    print()

    std_intra_promedio = np.mean(stds_intra_ejemplos) if stds_intra_ejemplos else float("nan")
    std_entre_promedio = std_entre_trials.mean()

    print(f"  RESUMEN {etiqueta}:")
    print(f"    std intra-trial (promedio de los 4 casos de ejemplo): {std_intra_promedio:.8f}")
    print(f"    std entre-trials (todos los trials):                 {std_entre_promedio:.8f}")
    if std_intra_promedio > 0:
        print(f"    razon (entre-trials / intra-trial): {std_entre_promedio / std_intra_promedio:.2f}x")
    print()
    print()

    return std_intra_promedio, std_entre_promedio


print("############################################################")
print("# attn_cross_summary -- dato de C1 (lo que reporto Russell) #")
print("############################################################")
print()
cross_intra, cross_entre = analizar("attn_cross_summary", "attn_cross_summary (C1)")

print("############################################################")
print("# attn_final_summary -- dato de B1/B2, punto de comparacion #")
print("############################################################")
print()
final_intra, final_entre = analizar("attn_final_summary", "attn_final_summary (B1/B2)")

print("=== COMPARACION FINAL ===")
print(f"attn_cross_summary : intra={cross_intra:.8f}  entre={cross_entre:.8f}")
print(f"attn_final_summary : intra={final_intra:.8f}  entre={final_entre:.8f}")
