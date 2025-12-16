from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional, Set
from collections import defaultdict
import os
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
    edf_count: int
    edf_paths: List[str]

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


def scan_patient_summaries(
    edf_paths: List[str],
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

    for patient_id, paths in paths_by_patient.items():
        total_seiz: int = 0
        ok_paths: List[str] = []

        for edf_path in paths:
            try:
                labels: List[Tuple[int, int, str]] = get_labels_complete_fn(edf_path)
                total_seiz += seizure_seconds_from_labels(labels)
                ok_paths.append(edf_path)
            except Exception as e:
                # Si falta csv_bi o hay error, lo saltamos (sin detener todo)
                print(f"[WARN] labels fail: {edf_path} -> {e}")
                continue

        out[patient_id] = PatientSummary(
            patient_id=patient_id,
            seizure_seconds=int(total_seiz),
            edf_count=int(len(ok_paths)),
            edf_paths=ok_paths,
        )

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
