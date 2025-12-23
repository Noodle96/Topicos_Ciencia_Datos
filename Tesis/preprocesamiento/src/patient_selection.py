from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional, Set
from collections import defaultdict
import os
import json
import random

# Esta clase es principalmente para almacenar datos, no lógica compleja
# genera métodos automáticamente:
#    __init__ (constructor)
#    __repr__ (para imprimir bonito)
#    __eq__ (comparación)
#    opcionalmente __hash__, __lt__, etc.
@dataclass(frozen=True) # hace que la instancia sea INMUTABLE
class PatientSummary:
    """
    Resumen por paciente para el criterio de selección.

    Attributes:
        patient_id: ID del paciente (ej. 'aaaaaauj')
        seizure_seconds: Total de segundos etiquetados como seizure (sumados desde csv_bi)
        edf_count: Cantidad de EDF considerados para este paciente
        edf_paths: Lista de EDF paths pertenecientes al paciente (filtrados por referencia)
    """
    patient_id: str
    seizure_seconds: int
    bckg_seconds: int
    ratio: float
    edf_count: int
    edf_paths: List[str]

@dataclass(frozen=True)
class PatientJsonSummary:
    """
    Resumen por paciente para guardar en JSON.

    Attributes:
        patient_id: ID del paciente (ej. 'aaaaaauj')
        seizure_minutes: Total de minutos etiquetados como seizure (sumados desde csv_bi)
        bckg_minutes: Total de minutos etiquetados como bckg (sumados desde csv_bi)
        seizure_intervals: cantidad de intervalos de seizure
        bckg_intervals: cantidad de intervalos de bckg

    """
    patient_id: str
    seizure_minutes: float
    bckg_minutes: float
    seizure_intervals: int
    bckg_intervals: int

def extract_patient_and_reference_from_path(edf_path: str) -> Tuple[str, str]:
    """
    Extrae (patient_id, reference_type) desde un path EDF TUSZ 2023.

    Formato típico:
    .../edf/{split}/{patient}/{session}/{reference_type}/{file}.edf

    Returns:
        (patient_id, reference_type)
    """
    parts: List[str] = edf_path.split(os.sep)
    # print(f"parts: {parts}")
    idx_edf: int = parts.index("edf")
    # print(f"idx_edf: {idx_edf}")    
    patient_id: str = parts[idx_edf + 2]
    # print(f"patient_id: {patient_id}")
    reference_type: str = parts[idx_edf + 4]
    # print(f"reference_type: {reference_type}")
    return patient_id, reference_type


def seizure_seconds_from_labels(labels: List[Tuple[int, int, str]]) -> int:
    """
    Suma la duración total (en segundos) de intervalos con etiqueta seizure.

    labels: lista (start_sec, end_sec, label)
    """
    total: int = 0
    for s, e, lab in labels:
        lab_norm: str = lab.lower()
        if lab_norm in {"seiz", "seizure"} and e > s:
            total += (e - s)
    return total

def background_seconds_from_labels(
    labels: List[Tuple[int, int, str]]
) -> int:
    """
    Suma la duración total (en segundos) de intervalos con etiqueta bckg.

    labels: lista (start_sec, end_sec, label)
    """
    total: int = 0
    for s, e, lab in labels:
        lab_norm: str = lab.lower()
        if lab_norm in {"bckg", "background"} and e > s:
            total += (e - s)
    return total

def seizure_intervals(labels: List[Tuple[int, int, str]]) -> int:
    """
    Cuenta la cantidad de intervalos con etiqueta seizure.

    labels: lista (start_sec, end_sec, label)
    """
    total: int = 0
    for s, e, lab in labels:
        lab_norm: str = lab.lower()
        if lab_norm in {"seiz", "seizure"} and e > s:
            total += 1
    return total

def background_intervals(labels: List[Tuple[int, int, str]]) -> int:
    """
    Cuenta la cantidad de intervalos con etiqueta bckg.

    labels: lista (start_sec, end_sec, label)
    """
    total: int = 0
    for s, e, lab in labels:
        lab_norm: str = lab.lower()
        if lab_norm in {"bckg", "background"} and e > s:
            total += 1
    return total

# extraer el total de segundos del path asociado al EDF
def total_seconds_from_edf_path( edf_path: str) -> int:
    """
    Extrae la duración total (en segundos) desde el EDF path.

    Args:
        edf_path: ruta al archivo EDF

    Returns:
        duración total en segundos
    """
    label_csv: str = edf_path[:-4] + ".csv_bi"

    with open(label_csv, "r") as f:
        header_lines = []
        for line in f:
            if line.startswith("#"):
                header_lines.append(line.strip())
        # Extraer duración
        for line in header_lines:
            if line.lower().startswith("# duration"):
                parts = line.split("=")
                duration_sec = int(float(parts[1].strip().split()[0]))
                return duration_sec
    return -1 # imposible case


# def seizure_seconds_from_labels(
#     labels: List[Tuple[float, float, str]]
# ) -> float:
#     """
#     Suma la duración total (en segundos) de intervalos con etiqueta seizure.

#     labels: lista (start_sec, end_sec, label)
#     """
#     total: float = 0.0

#     for s, e, lab in labels:
#         lab_norm: str = lab.lower()
#         if lab_norm in {"seiz", "seizure"} and e > s:
#             total += (e - s)

#     return total

# En Python, el * NO es un parámetro. Es un separador sintáctico que significa:
# A partir de aquí, TODOS los parámetros deben pasarse por nombre (keyword-only)
def scan_patient_summaries(
    edf_paths: List[str],
    path_json_output: Optional[str] = None,
    outJson: Optional[List[Dict[str, float]]] = None,
    *,
    skip_reference_types: Set[str],
    get_labels_complete_fn,  # función: (edf_path:str) -> List[(s,e,label)]
) -> Dict[str, PatientSummary]:
    """
    Escanea EDF paths y produce un resumen por paciente usando SOLO csv_bi.

    Importante:
    - NO carga la señal EDF.
    - Solo llama a get_labels_complete_fn(edf_path) que lee el csv_bi asociado.

    Returns:
        dict patient_id -> PatientSummary
    """
    # Si la clave no existe, crea una lista vacía automáticamente
    paths_by_patient: Dict[str, List[str]] = defaultdict(list)

    # 1) agrupar EDF por paciente (filtrando referencias no deseadas)
    for p in edf_paths:
        patient_id, ref_type = extract_patient_and_reference_from_path(p)
        if ref_type in skip_reference_types:
            continue
        paths_by_patient[patient_id].append(p)

    # 2) sumar seizure_seconds por paciente
    out: Dict[str, PatientSummary] = {}

    # En outjson veremos las estadisticas por paciente
    # outJson: List[Dict[str, float]] = [] # pasado por referencia
    
    static_id: int = 0
    for patient_id, paths in paths_by_patient.items():
        total_seiz: int = 0
        total_backg: int = 0
        total = 0
        total_seizure_intervals: int = 0
        total_bckg_intervals: int = 0
        ok_paths: List[str] = []
        static_id += 1

        for edf_path in paths:
            try:
                # print("In try\n")
                labels: List[Tuple[int, int, str]] = get_labels_complete_fn(edf_path)
                total_seiz += seizure_seconds_from_labels(labels)
                total_backg += background_seconds_from_labels(labels)
                total += total_seconds_from_edf_path(edf_path)
                total_seizure_intervals += seizure_intervals(labels)
                total_bckg_intervals += background_intervals(labels)
                ok_paths.append(edf_path)
            except Exception as e:
                # Si falta csv_bi o hay error, lo saltamos (sin detener todo)
                print(f"[WARN] labels fail: {edf_path} -> {e}")
                continue

        out[patient_id] = PatientSummary(
            patient_id=patient_id,
            seizure_seconds=int(total_seiz),
            bckg_seconds=int(total_backg),
            ratio=float(total_seiz)/(total_seiz + total_backg) if (total_seiz + total_backg) > 0 else 0.0,
            edf_count=int(len(ok_paths)),
            edf_paths=ok_paths,
        )
        outJson.append({
            "static_id": static_id,
            "patient_id": patient_id,
            "total_minutes": total / 60.0,
            "total_seconds": total,
            "total_seconds_accounted": total_seiz + total_backg,
            "bool_verified_total": total == (total_seiz + total_backg),
            "seizure_seconds": total_seiz,
            "seizure_minutes": total_seiz / 60.0,
            "bckg_seconds": total_backg,
            "bckg_minutes": total_backg / 60.0,
            "seizure_intervals": total_seizure_intervals,
            "bckg_intervals": total_bckg_intervals,
            "ratio": total_seiz/(total_seiz + total_backg) if (total_seiz + total_backg) > 0 else 0.0,
        })
        outJson.sort(
            key=lambda x: x["seizure_minutes"],
            # key=lambda x: x["ratio"],
            reverse=True,
        )
        os.makedirs(os.path.dirname(path_json_output), exist_ok=True)
        with open(path_json_output, "w", encoding="utf-8") as f:
            json.dump(outJson, f, indent=2)
    return out


def select_top_patients_by_seizure_seconds(
    patient_map: Dict[str, PatientSummary],
    *,
    k: Optional[int],
    min_seizure_seconds: int,
) -> List[str]:
    """
    Selecciona pacientes ordenando por seizure_seconds descendente.

    Args:
        patient_map: dict patient_id -> PatientSummary
        k: número máximo de pacientes a seleccionar (None = todos)
        min_seizure_seconds: filtro mínimo para incluir un paciente

    Returns:
        Lista de patient_id seleccionados
    """
    items: List[Tuple[str, int]] = [
        (pid, summary.seizure_seconds)
        for pid, summary in patient_map.items()
        if summary.seizure_seconds >= min_seizure_seconds
    ]
    items.sort(key=lambda x: x[1], reverse=True)

    if k is None:
        return [pid for pid, _ in items]
    return [pid for pid, _ in items[:k]]


def select_top_patients_by_some_criteria(
    patient_map: Dict[str, PatientSummary],
    *,
    k: Optional[int],
    min_seizure_seconds: int,
) -> List[str]:
    """
    Selecciona pacientes ordenando por algun criterio modificable descendente.

    Args:
        patient_map: dict patient_id -> PatientSummary
        k: número máximo de pacientes a seleccionar (None = todos)
        min_seizure_seconds: filtro mínimo para incluir un paciente

    Returns:
        Lista de patient_id seleccionados
    """
    items: List[Tuple[str, int]] = [
        (pid, summary.ratio)
        for pid, summary in patient_map.items()
        if summary.seizure_seconds >= min_seizure_seconds
    ]
    items.sort(key=lambda x: x[1], reverse=True)

    if k is None:
        return [pid for pid, _ in items]
    return [pid for pid, _ in items[:k]]


def split_train_val_patients(
    patient_ids: List[str],
    *,
    k_train: int,
    k_val: int,
    seed: int,
) -> Tuple[List[str], List[str]]:
    """
    Dado un pool de pacientes, hace split reproducible.

    Se espera que `patient_ids` tenga al menos k_train + k_val pacientes.
    """
    rng = random.Random(seed)
    pool = patient_ids[:]
    rng.shuffle(pool)

    train_patients: List[str] = pool[:k_train]
    val_patients: List[str] = pool[k_train:k_train + k_val]
    return train_patients, val_patients


def filter_paths_by_patients(
    edf_paths: List[str],
    *,
    selected_patients: Set[str],
    skip_reference_types: Set[str],
) -> List[str]:
    """
    Filtra EDF paths dejando solo los que pertenezcan a `selected_patients`.
    """
    out: List[str] = []
    for p in edf_paths:
        pid, ref = extract_patient_and_reference_from_path(p)
        if ref in skip_reference_types:
            continue
        if pid in selected_patients:
            out.append(p)
    return out


def summarize_patients(
    name: str,
    patient_ids: List[str],
    patient_map: Dict[str, PatientSummary],
) -> None:
    """
    Imprime un resumen rápido de seizure_seconds para un conjunto de pacientes.
    """
    secs: List[int] = [patient_map[p].seizure_seconds for p in patient_ids if p in patient_map]
    if not secs:
        print(f"{name}: (sin datos)")
        return
    print(
        f"{name}: n={len(secs)} | "
        f"min={min(secs)}s | max={max(secs)}s | avg={sum(secs)/len(secs):.2f}s"
    )
