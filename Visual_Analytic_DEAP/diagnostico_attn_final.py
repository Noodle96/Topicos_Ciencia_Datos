"""
Diagnostico standalone (NO depende de Flask ni del servicio nuevo) para
aislar si la casi-invarianza de attn_final_summary entre trials/ventanas
que reporto Russell es (a) un bug de indexing en la extraccion, o (b) un
colapso real de la atencion del modelo entrenado.

Correr desde la raiz de Visual_Analytic_DEAP:
    python diagnostico_attn_final.py
"""
import numpy as np
import pandas as pd

MANIFEST_PATH = "dataset/processed/representation_inputs/husformer_manifest.csv"
REPR_DIR = "dataset/processed/representations/husformer"

manifest = pd.read_csv(MANIFEST_PATH)
print("manifest: ", manifest.shape, "columnas:", manifest.columns.tolist())

# 1) Local_id es realmente unico y contiguo por split?
for split in manifest["split"].unique():
    sub = manifest[manifest["split"] == split]
    print(
        f"  split={split} n_rows={len(sub)} n_unique_local_id={sub['local_id'].nunique()} "
        f"min={sub['local_id'].min()} max={sub['local_id'].max()}"
    )

print()

# 2) Dentro de un mismo trial, varia attn_final_summary entre ventanas?
#    Y entre trials distintos, varia la media?
casos = [(1, 1), (1, 9), (5, 20), (10, 15)]

for pid, trial in casos:
    rows = manifest[
        (manifest["participant_id"] == pid) & (manifest["trial"] == trial)
    ].sort_values("window_index")

    if rows.empty:
        print(f"S{pid:02d} T{trial}: no encontrado en manifest")
        continue

    split = rows["split"].iloc[0]
    data = np.load(f"{REPR_DIR}/{split}_representations.npz")
    attn = data["attn_final_summary"]  # (N_split, 5, 5)

    local_ids = rows["local_id"].to_numpy()
    print(f"S{pid:02d} T{trial}: split={split} n_windows={len(rows)} local_ids[:5]={local_ids[:5]}")

    trial_attn = attn[local_ids]  # (n_windows, 5, 5)
    dominance = trial_attn.mean(axis=1)  # (n_windows, 5) -- promedio sobre filas/query

    print("  dominance media sobre las ventanas del trial:", dominance.mean(axis=0))
    print("  dominance std ENTRE ventanas del mismo trial:", dominance.std(axis=0))
    print()

# 3) Variabilidad global del array crudo -- independiente de cualquier
#    indexing nuestro. Si esto ya da std ~0, el problema esta en la
#    extraccion/el modelo, no en mi codigo de agregacion.
print("--- Variabilidad global de attn_final_summary por split ---")
for split in ["train", "valid", "test"]:
    data = np.load(f"{REPR_DIR}/{split}_representations.npz")
    attn = data["attn_final_summary"]
    print(
        f"{split}: shape={attn.shape} std_global={attn.std():.8f} "
        f"mean_global={attn.mean():.8f}"
    )
    # std por celda de la matriz 5x5, calculado sobre las N ventanas del split
    print("  std por celda (5x5), sobre N ventanas:\n", attn.std(axis=0))
