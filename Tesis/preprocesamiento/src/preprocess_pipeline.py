# Ruta: RAIZ/preprocesamiento/src/preprocess_pipeline.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Set, Optional

import os
import numpy as np
import mne
from scipy.signal import iirnotch, lfilter

# Reusamos funciones del data_reader_2023.py (que ahora está en preprocesamiento/src)
from data_reader_2023 import (
    get_channels_from_raw,
    butter_bandpass_filter,
    resample_data_in_each_channel,
    slice_signals_into_binary_segments,
    get_labels_complete_from_csv_bi_clasificacion_binaria,
    cubo,
)

from patient_statistics import (
    accumulate_patient_label_stats
)

@dataclass(frozen=True)
class PreprocessParams:
    """
    Parámetros del pipeline pesado.

    Importante: estos valores deben coincidir con los del notebook
    (NO los cambiamos aquí, solo los recibimos).
    """
    lowcut: float
    highcut: float
    fs: int
    resampleFS: int
    segment_interval: int
    seizure_types: List[str]
    seizure_overlapping_ratio: List[float]
    skip_reference_types: Set[str]


def extract_reference_type_from_path(edf_path: str) -> str:
    """
    Extrae reference_type desde EDF path:
    .../edf/{split}/{patient}/{session}/{reference_type}/{file}.edf
    """
    parts: List[str] = edf_path.split(os.sep)
    idx_edf: int = parts.index("edf")
    reference_type: str = parts[idx_edf + 4]
    return reference_type

def extract_patient_id_from_path(edf_path: str) -> str:
    """
    Extrae patient_id desde EDF path:
    .../edf/{split}/{patient}/{session}/{reference_type}/{file}.edf
    """
    parts: List[str] = edf_path.split(os.sep)
    idx_edf: int = parts.index("edf")
    patient_id: str = parts[idx_edf + 2]
    return patient_id


def extract_patient_session_id(edf_path: str) -> str:
    """
    Devuelve el nombre base para el archivo .npy
    Ej: aaaaaauj_s004_t000 (sin extensión).
    """
    """Returns the final component of a pathname"""
    base: str = os.path.basename(edf_path)
    return base[:-4]  # remove ".edf"


def ensure_output_dirs(base_out: str, split_name: str, seizure_types: List[str]) -> None:
    for lab in seizure_types:
        os.makedirs(os.path.join(base_out, split_name, lab), exist_ok=True)


def bandpass_and_notch_filter(
    signals: np.ndarray,
    *,
    params: PreprocessParams,
) -> List[np.ndarray]:
    """
    Aplica bandpass + notch(1Hz) + notch(60Hz) a cada canal.
    Retorna lista de arrays 1D (uno por canal)
    """
    # Notch sobre resampleFS (igual que tu notebook)
    notch_1_b: np.ndarray
    notch_1_a: np.ndarray
    notch_1_b, notch_1_a = iirnotch(1.0, Q=30.0, fs=params.resampleFS)

    notch_60_b: np.ndarray
    notch_60_a: np.ndarray
    notch_60_b, notch_60_a = iirnotch(60.0, Q=30.0, fs=params.resampleFS)

    filtered_signals: List[np.ndarray] = []

    for i in range(signals.shape[0]):
        bandpass_filtered_signal: np.ndarray = butter_bandpass_filter(
            signals[i, :],
            params.lowcut,
            params.highcut,
            params.fs,
            order=3,
        )
        filtered_1_signal: np.ndarray = lfilter(notch_1_b, notch_1_a, bandpass_filtered_signal)
        filtered_60_signal: np.ndarray = lfilter(notch_60_b, notch_60_a, filtered_1_signal)
        filtered_signals.append(filtered_60_signal)

    return filtered_signals


def save_segments_append(
    out_base: str,
    split_name: str,
    label_name: str,
    patient_session: str,
    windows: List[np.ndarray],
) -> int:
    """
    Guarda ventanas (cada una shape [22, L]) en:
      out_base/split/label/patient_session.npy

    Si existe, concatena.
    Retorna cuántas ventanas se guardaron (después de concatenar).
    """
    folder_base: str = os.path.join(out_base, split_name, label_name)
    os.makedirs(folder_base, exist_ok=True)

    save_file: str = os.path.join(folder_base, f"{patient_session}.npy")
    new_arr: np.ndarray = np.array(windows)

    if os.path.isfile(save_file):
        existing_data: np.ndarray = np.load(save_file, allow_pickle=True)
        merged: np.ndarray = np.concatenate((existing_data, new_arr), axis=0)
        np.save(save_file, merged)
        return int(merged.shape[0])

    np.save(save_file, new_arr)
    return int(new_arr.shape[0])


def process_one_edf(
    edf_path: str,
    *,
    split_name: str,
    out_base: str,
    params: PreprocessParams,
    patient_stats_accumulator: Optional[Dict[str, Dict[str, float]]]=None,
) -> Dict[str, int]:
    """
    Procesa 1 EDF completo y guarda sus segmentos.

    Returns:
        dict con conteos por clase: {"bckg": n, "seizure": m}
        Si se salta, retorna {}.
    """
    print("[process_one_edf] Processing:", edf_path)
    ref_type: str = extract_reference_type_from_path(edf_path)
    if ref_type in params.skip_reference_types:
        return {}

    # -------------------------------------------------
    # 1)        Carga de la señal cruda EDF           -
    # -------------------------------------------------
    raw: mne.io.BaseRaw = mne.io.read_raw_edf(edf_path, preload=True, verbose="warning")

    thisFS: int = int(raw.info["sfreq"])

    # --------------------------------------------------
    # 2)   Extracción de canales(montaje diferencial)  -
    # --------------------------------------------------
    flag_wrong: bool
    signals: np.ndarray
    flag_wrong, signals = get_channels_from_raw(raw)
    if flag_wrong:
        print("[process_one_edf] skipping EDF due to wrong channels:", edf_path)
        return {}

    # --------------------------------------------------
    # 3)           Filtrado bandpass + notch           -
    # --------------------------------------------------
    filtered_signals: List[np.ndarray] = bandpass_and_notch_filter(signals, params=params)

    # --------------------------------------------------
    # 4)        Remuestreo a resampleFS (250)          -
    # --------------------------------------------------
    if thisFS == params.resampleFS:
        resampled_signals: List[np.ndarray] = filtered_signals[:]
    else:
        resampled_signals: List[np.ndarray] = resample_data_in_each_channel(filtered_signals, thisFS, params.resampleFS)


    # --------------------------------------------------
    # 5) Leer siempre el CSV binario y completar huecos- 
    # --------------------------------------------------
    labels: List[Tuple[int, int, str]] = get_labels_complete_from_csv_bi_clasificacion_binaria(edf_path)

    # Esta funcion es llamada por referencia desde el notebook principal
    # para motivas de estadisticas por paciente
    accumulate_patient_label_stats(
        extract_patient_id_from_path(edf_path),
        labels,
        patient_stats_accumulator,
    )
    # Segmentación binaria
    segments: List[List[List[np.ndarray]]] = slice_signals_into_binary_segments(
        resampled_signals,
        params.resampleFS,
        labels,
        float(params.segment_interval),
        params.seizure_types,
        params.seizure_overlapping_ratio,
    )

    patient_session: str = extract_patient_session_id(edf_path)

    # Guardado
    counts: Dict[str, int] = {}
    for i, label_name in enumerate(params.seizure_types):
        if not segments[i]:
            continue

        windows: List[np.ndarray] = []
        for interval_windows in segments[i]:
            for w in interval_windows:
                windows.append(w)

        if not windows:
            continue

        total_after: int = save_segments_append(
            out_base=out_base,
            split_name=split_name,
            label_name=label_name,
            patient_session=patient_session,
            windows=windows,
        )
        counts[label_name] = total_after

    return counts


def run_preprocessing_for_split(
    edf_paths: List[str],
    *,
    split_name: str,
    out_base: str,
    params: PreprocessParams,
    max_edfs: Optional[int],
    patient_stats_accumulator: Optional[Dict[str, Dict[str, float]]]=None,
) -> Dict[str, int]:
    """
    Procesa una lista de EDF para un split (train/val/test).

    Args:
        edf_paths: lista EDF ya filtrada por pacientes seleccionados
        split_name: 'train' | 'val' | 'test'
        out_base: carpeta base de salida (segment_interval_4_sec)
        max_edfs: para cortar rápido (None = procesa todos)

    Returns:
        conteos agregados por clase: {"bckg": X, "seizure": Y}
    """
    ensure_output_dirs(out_base, split_name, params.seizure_types)

    totals: Dict[str, int] = {lab: 0 for lab in params.seizure_types}
    processed: int = 0

    for edf_path in edf_paths:
        if max_edfs is not None and processed >= max_edfs:
            print("[run_preprocessing_for_split] first conditional")
            break

        counts: Dict[str, int] = process_one_edf(
            edf_path,
            split_name=split_name,
            out_base=out_base,
            params=params,
            patient_stats_accumulator=patient_stats_accumulator,
        )

        # counts devuelve "total_after" por archivo, pero para el resumen
        # acumulamos solo ventanas nuevas aproximadas como "len guardado en ese llamado".
        # Aquí, por simplicidad y trazabilidad, solo contamos archivos procesados.
        for lab in params.seizure_types:
            if lab in counts:
                # No sabemos cuántas fueron nuevas vs acumuladas sin cargar el .npy anterior;
                # para tracking fino, luego podemos retornar ventanas_nuevas.
                totals[lab] += 1

        processed += 1

    print(f"[{split_name}] EDF procesados: {processed}")
    print(f"[{split_name}] Archivos con segmentos por clase (conteo aproximado): {totals}")
    return totals
