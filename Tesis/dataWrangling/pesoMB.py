from pathlib import Path
import pandas as pd

paths = list(Path("../dataset/tuh_eeg_seizure/v2.0.3/edf/").rglob("*.edf"))
sizes = [p.stat().st_size / (1024 * 1024) for p in paths]  # Convertir a MB

df = pd.DataFrame({"filename": [p.name for p in paths], "size_MB": sizes})


import matplotlib.pyplot as plt

plt.boxplot(df["size_MB"])
plt.title("Distribución del tamaño de archivos .edf")
plt.ylabel("Tamaño (MB)")
plt.grid(True)
plt.show()