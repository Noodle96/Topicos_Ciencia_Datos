from pathlib import Path
import pandas as pd
from pyedflib import EdfReader
from typing import Dict, Tuple, List
import os
import time
import matplotlib.pyplot as plt


def graficar_desde_csv(csv_path: Path, output_dir: Path) -> None:
    df: pd.DataFrame = pd.read_csv(csv_path, index_col=0)
    df_sin_total = df.drop(index="total", errors="ignore")

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Gráfico comparando por tipo de archivo en cada partición
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    df_sin_total.plot(kind='bar', ax=ax1, rot=0)
    ax1.set_title("Registros por tipo de archivo por partición")
    ax1.set_ylabel("Cantidad de registros")
    ax1.set_xlabel("Partición")
    ax1.legend(title="Tipo de archivo")
    plt.tight_layout()
    fig1.savefig(output_dir / "grafico_por_particion.png")
    plt.close(fig1)

    # 2. Gráfico total por tipo de archivo
    if "total" in df.index:
        fig2, ax2 = plt.subplots(figsize=(6, 5))
        df.loc["total"].plot(kind='bar', ax=ax2, rot=0)
        ax2.set_title("Total de registros por tipo de archivo")
        ax2.set_ylabel("Cantidad de registros")
        ax2.set_xlabel("Tipo de archivo")
        plt.tight_layout()
        fig2.savefig(output_dir / "grafico_total_por_extension.png")
        plt.close(fig2)

    # 3. Un gráfico por tipo de archivo comparando particiones
    for col in df.columns:
        fig, ax = plt.subplots(figsize=(6, 5))
        df_sin_total[col].plot(kind='bar', ax=ax, rot=0)
        ax.set_title(f"Comparación por partición para archivos {col.upper()}")
        ax.set_ylabel("Cantidad de registros")
        ax.set_xlabel("Partición")
        plt.tight_layout()
        fig.savefig(output_dir / f"grafico_{col}_por_particion.png")
        plt.close(fig)

def get_all_TUSZ_2023_session_paths(
    rootPath: str
) -> Tuple[List[str], List[str], Dict[str, int]]:
    session_paths: List[str] = []
    all_patients: List[str] = os.listdir(rootPath)
    reference_type_count: Dict[str, int] = {}

    for patient in all_patients:
        patient_dir: str = os.path.join(rootPath, patient)
        patient_sessions: List[str] = os.listdir(patient_dir)
        for patient_session in patient_sessions:
            session_dir: str = os.path.join(patient_dir, patient_session)
            reference_types: List[str] = os.listdir(session_dir)
            for reference_type in reference_types:
                reference_type_count[reference_type] = reference_type_count.get(reference_type, 0) + 1
                ref_dir: str = os.path.join(session_dir, reference_type)
                files: List[str] = os.listdir(ref_dir)
                for file in files:
                    if file.endswith(".edf"):
                        full_path: str = os.path.join(ref_dir, file)
                        session_paths.append(full_path)

    return session_paths, all_patients, reference_type_count

def contar_registros_edf_pyedflib(path: Path) -> int:
    """
    Retorna el número de data records en el archivo EDF usando pyedflib.
    """
    try:
        with EdfReader(str(path)) as f:
            return f.datarecords_in_file
    except Exception:
        return 0

def contar_registros_edf_bytes(path: Path) -> int:
    """
    Lee el número de registros desde los bytes 236–244 del header general del archivo EDF.
    """
    try:
        with open(path, 'rb') as f:
            f.seek(236)
            record_bytes: bytes = f.read(8)
            return int(record_bytes.decode().strip())
    except Exception:
        return 0


def contar_registros_csv(path: Path) -> int:
    """
    Cuenta el número de registros en un archivo .csv o .csv_bi, asumiendo
    5 líneas de comentario y 1 línea de encabezado.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            n: int = sum(1 for _ in f)
        return max(0, n - 6)
    except Exception:
        return 0


def procesar_multiples_particiones(root_dataset_path: Path) -> pd.DataFrame:
    """
    Procesa las particiones 'train', 'dev' y 'eval' automáticamente y devuelve un único DataFrame.
    """
    particiones: List[str] = ['train', 'dev', 'eval']
    df_final = pd.DataFrame()

    for part in particiones:
        path_part = root_dataset_path / part
        edf_paths, _, _ = get_all_TUSZ_2023_session_paths(str(path_part))
        registro_counts: Dict[str, int] = {'edf': 0, 'csv': 0, 'csv_bi': 0}

        for edf_path_str in edf_paths:
            edf_path: Path = Path(edf_path_str)
            registro_counts['edf'] += contar_registros_edf_pyedflib(edf_path)
            registro_counts['csv'] += contar_registros_csv(edf_path.with_suffix('.csv'))
            registro_counts['csv_bi'] += contar_registros_csv(edf_path.with_suffix('.csv_bi'))

        df_part = pd.DataFrame([registro_counts], index=[part])
        df_final = pd.concat([df_final, df_part])

    df_total = pd.DataFrame([df_final.sum()], index=["total"])
    return pd.concat([df_final, df_total])


def main() -> None:
    initTime = time.time()
    root_dataset_path: Path = Path('../dataset/tuh_eeg_seizure/v2.0.3/edf/')
    df_resultado: pd.DataFrame = procesar_multiples_particiones(root_dataset_path)
    endTime = time.time()
    print(f"Tiempo total de procesamiento: {endTime - initTime:.2f} segundos")
    print(df_resultado)
    df_resultado.to_csv("resumen_registros_tusz.csv")
    print("Graficando...")
    graficar_desde_csv(Path("resumen_registros_tusz.csv"), Path("graficas_salida"))



    # TESTING
    # data_path = "../dataset/tuh_eeg_seizure/v2.0.3/edf/train/aaaaaauj/s004_2012/01_tcp_ar/aaaaaauj_s004_t000.edf"
    # data_path = Path(data_path)
    # print(data_path)
    # print("Número de registros EDF (pyedflib):", contar_registros_edf_pyedflib(data_path))
    # print("Número de registros EDF (bytes):", contar_registros_edf_bytes(data_path))
    # print("Número de registros CSV:", contar_registros_csv(data_path.with_suffix('.csv')))
    # print("Número de registros CSV_BI:", contar_registros_csv(data_path.with_suffix('.csv_bi')))
    


# Ejecutar
if __name__ == "__main__":
    main()