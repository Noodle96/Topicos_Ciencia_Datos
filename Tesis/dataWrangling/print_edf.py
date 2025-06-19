from typing import Dict, List, Any
import matplotlib.pyplot as plt
from pyedflib import EdfReader
import pandas as pd
import numpy as np
from pathlib import Path


def extraer_info_canales(path_edf: Path) -> pd.DataFrame:
    """
    Extrae una tabla con la información por canal de un archivo .edf:
    incluye frecuencia, unidad, prefiltrado, valores únicos, min/max de la señal,
    rango físico del header y verificación si están dentro del rango.
    """
    with EdfReader(str(path_edf)) as f:
        n_channels = f.signals_in_file
        data = []

        for i in range(n_channels):
            signal = f.readSignal(i)
            label = f.getLabel(i)
            freq = f.getSampleFrequency(i)
            unit = f.getPhysicalDimension(i)
            prefilter = f.getPrefilter(i)
            n_samples = f.getNSamples()[i]
            phys_min = f.getPhysicalMinimum(i)
            phys_max = f.getPhysicalMaximum(i)
            real_min = np.min(signal)
            real_max = np.max(signal)

            dentro_rango = phys_min <= real_min <= phys_max and phys_min <= real_max <= phys_max

            data.append({
                "Canal": i,
                "Etiqueta": label,
                "Frecuencia (Hz)": freq,
                "Muestras": n_samples,
                "Unidad": unit,
                "Prefiltrado": prefilter,
                "Valores únicos": len(np.unique(signal)),
                "Valor mínimo señal": real_min,
                "Valor máximo señal": real_max,
                "Físico mínimo (header)": phys_min,
                "Físico máximo (header)": phys_max,
                "Dentro del rango físico": dentro_rango
            })

        return pd.DataFrame(data)

def graficar_superpuestos_con_colores(
    path_edf: Path,
    segundos: int,
    n_canales: int,
    output_path: Path
) -> None:
    """
    Grafica los primeros `n_canales` superpuestos con desplazamiento vertical
    en un solo gráfico, con diferentes colores para cada canal.
    """
    with EdfReader(str(path_edf)) as f:
        total_canales = f.signals_in_file
        n_canales = min(n_canales, total_canales)

        plt.figure(figsize=(15, 6))
        colores: List[str] = plt.cm.tab20.colors  # paleta de 20 colores

        for i in range(n_canales):
            fs = f.getSampleFrequency(i)
            n_muestras = int(segundos * fs)
            signal = f.readSignal(i)[:n_muestras]
            tiempo = np.arange(len(signal)) / fs

            offset = i * 100  # desplazamiento vertical artificial
            signal_offset = signal + offset
            label = f.getLabel(i)

            plt.plot(tiempo, signal_offset, label=label, color=colores[i % len(colores)])

        plt.xlabel("Tiempo (s)")
        plt.title(f"{n_canales} canales superpuestos – primeros {segundos} segundos")
        plt.yticks([])  # Opcional: ocultar eje Y
        plt.legend(loc='upper right', fontsize='small', ncol=2)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close()

def main() -> None:
    # ⚠️ Reemplaza esta ruta con el archivo .edf real que deseas analizar
    # datapath: str = "../dataset/tuh_eeg_seizure/v2.0.3/edf/train/aaaaarew/s001_2014/01_tcp_ar/aaaaarew_s001_t000.edf"
    data_path = "../dataset/tuh_eeg_seizure/v2.0.3/edf/train/aaaaaauj/s004_2012/01_tcp_ar/aaaaaauj_s004_t000.edf"

    # path_edf: Path = Path(data_path)
    # output_dir: Path = Path("salida_train")
    # output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Extraer información por canal y guardar en CSV
    # df_info = extraer_info_canales(path_edf)
    # df_info.to_csv(output_dir / "info_canales.csv", index=False)
    # print(df_info)

    path_edf: Path = Path(data_path)  # ← Reemplaza con tu ruta real
    output_path: Path = Path("primeros_n_canales.png")

    graficar_superpuestos_con_colores(
            path_edf=path_edf,
            segundos=5,
            n_canales=10,
            output_path=output_path
    )
if __name__ == "__main__":
    main()
