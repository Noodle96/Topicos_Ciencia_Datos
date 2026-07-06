"""
Extrae, para TODO el dataset ya entrenado, las representaciones fusionadas
(`last_hs`) y un resumen de atención cross-modal agregado por modalidad, sin
guardar la atención cruda y completa (esa se calcula al vuelo en el backend,
ver más abajo).

Contexto de la decisión de diseño (ya cerrada con Russell, 2026-07-06, ver
"📦 Estrategia de almacenamiento de atención cross-modal" en
estado_proyecto.md): cada ventana de 1s produce ~16MB de atención cruda
(5 módulos cross-modales + la auto-atención final, 5 capas cada uno) -- con
~76,800 ventanas en todo el dataset (32 participantes x 40 trials x 60
ventanas), guardar todo crudo pesaría más de 1TB. En vez de eso, este script
guarda por ventana:

1. `last_hs`: el embedding fusionado (d_m floats, barato).
2. `attn_cross_summary`: resumen (5, 5) de los 5 módulos `trans_m{i}_all` --
   fila = módulo/modalidad que "pregunta", columna = modalidad fuente,
   promediando capas + eje temporal + posiciones dentro de cada bloque de
   modalidad fuente.
3. `attn_final_summary`: resumen (5, 5) de la auto-atención final
   (`trans_final`) -- fila = modalidad query, columna = modalidad key, mismo
   tipo de promedio.

La matriz de atención cruda y completa (capa por capa, posición por posición)
NO se guarda para ninguna ventana -- se calcula bajo demanda en el backend,
solo cuando el usuario abre una ventana puntual para inspeccionarla en
detalle. Esto fue validado como viable con un benchmark real de timing
(`test_return_attn.py`, ~25ms/ventana con return_attn=True, batch=1),
imperceptible para una interacción de UI.

Uso (desde la raíz del proyecto, con el entorno virtual de husformer_deap_va
activado -- necesita torch):
    python -m backend.scripts.husformer.extract_representations
    python -m backend.scripts.husformer.extract_representations --split test
    python -m backend.scripts.husformer.extract_representations --batch_size 16 --clean
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch.utils.data import DataLoader

from . import config

# husformer_deap_va/ NO es un paquete Python del proyecto (no tiene imports
# rooted en la raíz del repo) -- se corre normalmente como `cd
# husformer_deap_va && python main.py`, y por eso `main.py` puede hacer
# `from src.models import HUSFORMERModel` porque Python agrega automáticamente
# el directorio del script (husformer_deap_va/) a sys.path. Como este script
# vive en backend/scripts/husformer/ y se corre desde la raíz del proyecto,
# hay que agregar husformer_deap_va/ a sys.path a mano ANTES de importar nada
# de src/ o modules/, para que esos imports resuelvan igual que dentro de
# husformer_deap_va/.
if str(config.HUSFORMER_DIR) not in sys.path:
    sys.path.insert(0, str(config.HUSFORMER_DIR))

# FIX (mismo motivo que test_return_attn.py): hay que fijar el tensor type por
# defecto ANTES de importar src.dataset/src.utils, porque src/dataset.py fija
# esto mismo como efecto secundario al importarse -- se deja explícito aquí
# también para que quede claro y no dependa de ese efecto secundario.
use_cuda: bool = torch.cuda.is_available()
torch.set_default_tensor_type("torch.cuda.FloatTensor" if use_cuda else "torch.FloatTensor")

from src.utils import get_data  # noqa: E402  (import diferido, ver comentario de sys.path arriba)

DATASET_NAME: str = "husformer"  # minúsculas -- ver bug #7 en estado_proyecto.md
N_MODALITY_GROUPS: int = 5
SPLIT_NAMES: tuple[str, ...] = ("train", "valid", "test")


def parse_arguments() -> argparse.Namespace:
    """Define los argumentos de línea de comandos del script."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=(
            "Corre inferencia con el modelo Husformer ya entrenado sobre los "
            "splits del dataset y guarda last_hs + resumen de atención "
            "agregado por modalidad (NO la atención cruda completa)."
        )
    )

    parser.add_argument(
        "--split",
        type=str,
        default="all",
        choices=["all", "train", "valid", "test"],
        help="Qué split procesar. Por defecto, los 3.",
    )

    parser.add_argument(
        "--batch_size",
        type=int,
        default=32,
        help=(
            "Batch de INFERENCIA (no de entrenamiento). Al no haber backward "
            "pass ni grafo de autograd (torch.no_grad()), el costo de "
            "memoria por ventana es menor que durante el entrenamiento "
            "(donde batch_size=24 usó ~5.2GB de los 6GB disponibles) -- pero "
            "no se midió el límite exacto en inferencia, así que 32 es un "
            "default conservador. Si aparece OutOfMemoryError, bajar este "
            "valor; no hace falta tocar nada más."
        ),
    )

    parser.add_argument(
        "--checkpoint",
        type=str,
        default=str(config.HUSFORMER_CHECKPOINT_FILE),
        help="Ruta al checkpoint entrenado (default: output/hus.pt del proyecto).",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Elimina la carpeta de salida (REPRESENTATIONS_DIR) antes de extraer.",
    )

    return parser.parse_args()


def prepare_output_directory(clean: bool) -> None:
    """Prepara la carpeta de salida de las representaciones extraídas."""
    if clean and config.REPRESENTATIONS_DIR.exists():
        shutil.rmtree(config.REPRESENTATIONS_DIR)

    config.REPRESENTATIONS_DIR.mkdir(parents=True, exist_ok=True)


def load_trained_model(checkpoint_path: Path) -> torch.nn.Module:
    """
    Carga el modelo Husformer ya entrenado desde un checkpoint.

    Igual que test_return_attn.py: save_model() (src/utils.py) guarda el
    objeto COMPLETO del modelo con torch.save(model, ...), no un state_dict,
    así que torch.load(...) alcanza sin reconstruir hyp_params.
    """
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"No existe el checkpoint entrenado: {checkpoint_path}. "
            "Hay que entrenar primero (cd husformer_deap_va && python main.py)."
        )

    model: torch.nn.Module = torch.load(str(checkpoint_path), weights_only=False)
    model.eval()
    return model


def _mean_over_layers(layer_tensors: list[torch.Tensor]) -> torch.Tensor:
    """Promedia una lista de tensores (uno por capa) en un solo tensor."""
    return torch.stack(layer_tensors, dim=0).mean(dim=0)


def compute_cross_modal_summary(
    attn_weights: dict[str, list[torch.Tensor]],
    n_groups: int = N_MODALITY_GROUPS,
) -> torch.Tensor:
    """
    Resume los 5 módulos cross-modales (attn_weights['m1_all']..['m5_all']).

    Cada módulo m{i}_all entrega, por capa, una matriz de atención de forma
    (batch, tgt_len=128, src_len=640): cuánta atención presta cada instante de
    la modalidad i (target) a cada una de las 640 posiciones concatenadas de
    las 5 modalidades (source, en el mismo orden m1..m5 que 'proj_all' en
    models.py). Este resumen promedia las 5 capas (self.layers=5, ver
    get_network() en models.py), el eje temporal completo (128 instantes) y,
    dentro del eje source, las 128 posiciones que corresponden a cada una de
    las 5 modalidades fuente.

    Retorna un tensor (batch, 5, 5): fila i = módulo m{i}_all (la modalidad
    que "pregunta"), columna j = modalidad fuente (la que "responde"). Base
    directa para T6 ("qué modalidad recibe mayor peso de atención cross-modal
    en un instante/ventana dado").
    """
    module_keys: list[str] = ["m1_all", "m2_all", "m3_all", "m4_all", "m5_all"]
    per_module_vectors: list[torch.Tensor] = []

    for module_key in module_keys:
        averaged_layers: torch.Tensor = _mean_over_layers(attn_weights[module_key])
        batch_size, tgt_len, src_len = averaged_layers.shape
        group_size: int = src_len // n_groups
        grouped: torch.Tensor = averaged_layers.view(batch_size, tgt_len, n_groups, group_size)
        module_vector: torch.Tensor = grouped.mean(dim=(1, 3))  # (batch, n_groups)
        per_module_vectors.append(module_vector)

    return torch.stack(per_module_vectors, dim=1)  # (batch, 5, 5)


def compute_final_attention_summary(
    attn_weights: dict[str, list[torch.Tensor]],
    n_groups: int = N_MODALITY_GROUPS,
) -> torch.Tensor:
    """
    Resume la auto-atención final (attn_weights['final']), que opera sobre la
    concatenación completa de las 5 modalidades (640 = 5*128, mismo orden
    m1..m5 que 'last_hs1' en models.py).

    Promedia las 5 capas y colapsa TANTO el eje query como el eje key (cada
    uno de 640) en 5 grupos de 128. Retorna (batch, 5, 5): "quién le presta
    atención a quién" a nivel de modalidad -- base para T7 (consistencia del
    patrón de dominancia de modalidad a lo largo del tiempo con el
    conocimiento fisiológico esperado).
    """
    averaged_layers: torch.Tensor = _mean_over_layers(attn_weights["final"])
    batch_size, tgt_len, src_len = averaged_layers.shape
    tgt_group_size: int = tgt_len // n_groups
    src_group_size: int = src_len // n_groups
    grouped: torch.Tensor = averaged_layers.view(
        batch_size, n_groups, tgt_group_size, n_groups, src_group_size
    )
    return grouped.mean(dim=(2, 4))  # (batch, 5, 5)


def extract_split(
    split_name: str,
    model: torch.nn.Module,
    batch_size: int,
) -> dict[str, np.ndarray]:
    """
    Corre inferencia con return_attn=True sobre TODAS las ventanas de un
    split, y arma los arrays finales indexados por local_id.

    'local_id' es exactamente el campo 'id' guardado en Husformer.pkl por
    dataset_builder.py (np.arange(n_windows) dentro de cada split) -- y
    Multimodal_Datasets.__getitem__() (husformer_deap_va/src/dataset.py) lo
    expone tal cual como META. Se usa shuffle=False (no hace falta el
    torch.Generator(device='cuda') del bug #8, que solo aplica con
    shuffle=True) y de todas formas se verifica cada local_id recibido contra
    META, en vez de asumir que el orden del DataLoader es 0..N-1 -- defensivo
    y prácticamente gratis.
    """
    print(f"\n[INFO] Cargando datos cacheados del split '{split_name}'...")
    data_args = argparse.Namespace(data_path=str(config.HUSFORMER_DATA_DIR))
    dataset = get_data(data_args, DATASET_NAME, split_name)

    n_windows: int = len(dataset)
    d_m: int = int(getattr(model, "d_m", 40))

    last_hs_all = np.zeros((n_windows, d_m), dtype=np.float32)
    cross_summary_all = np.zeros((n_windows, N_MODALITY_GROUPS, N_MODALITY_GROUPS), dtype=np.float32)
    final_summary_all = np.zeros((n_windows, N_MODALITY_GROUPS, N_MODALITY_GROUPS), dtype=np.float32)
    seen_local_ids = np.zeros(n_windows, dtype=bool)

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=False)
    n_batches: int = len(loader)
    start_time: float = time.time()

    for batch_index, (batch_X, _batch_Y, batch_META) in enumerate(loader, start=1):
        _sample_ind, m1, m2, m3, m4, m5 = batch_X
        if use_cuda:
            m1, m2, m3, m4, m5 = m1.cuda(), m2.cuda(), m3.cuda(), m4.cuda(), m5.cuda()

        with torch.no_grad():
            _output, last_hs, attn_weights = model(m1, m2, m3, m4, m5, return_attn=True)

        cross_summary = compute_cross_modal_summary(attn_weights)
        final_summary = compute_final_attention_summary(attn_weights)

        local_ids: np.ndarray = batch_META.detach().cpu().numpy().reshape(-1).astype(np.int64)

        last_hs_all[local_ids] = last_hs.detach().cpu().numpy()
        cross_summary_all[local_ids] = cross_summary.detach().cpu().numpy()
        final_summary_all[local_ids] = final_summary.detach().cpu().numpy()
        seen_local_ids[local_ids] = True

        if batch_index % 50 == 0 or batch_index == n_batches:
            elapsed_sec: float = time.time() - start_time
            print(
                f"  [{split_name}] batch {batch_index}/{n_batches} "
                f"({elapsed_sec:.1f}s transcurridos)"
            )

    if not seen_local_ids.all():
        missing_count: int = int((~seen_local_ids).sum())
        raise RuntimeError(
            f"Split '{split_name}': {missing_count} de {n_windows} ventanas "
            "nunca recibieron un local_id durante la extracción -- revisar "
            "el DataLoader/dataset, esto no debería pasar."
        )

    return {
        "local_id": np.arange(n_windows, dtype=np.int64),
        "last_hs": last_hs_all,
        "attn_cross_summary": cross_summary_all,
        "attn_final_summary": final_summary_all,
    }


def save_split_outputs(split_name: str, arrays: dict[str, np.ndarray]) -> Path:
    """Guarda los arrays de un split como un único .npz comprimido."""
    output_path: Path = config.REPRESENTATIONS_DIR / f"{split_name}_representations.npz"

    np.savez_compressed(
        output_path,
        local_id=arrays["local_id"],
        last_hs=arrays["last_hs"],
        attn_cross_summary=arrays["attn_cross_summary"],
        attn_final_summary=arrays["attn_final_summary"],
    )

    print(f"[OK] Split '{split_name}' guardado: {output_path} ({len(arrays['local_id'])} ventanas)")
    return output_path


def cross_check_against_manifest(split_counts: dict[str, int]) -> None:
    """
    Verificación blanda (no bloqueante) contra husformer_manifest.csv, si
    existe: compara cuántas ventanas tiene cada split ahí vs. lo extraído
    aquí. Solo imprime una advertencia si no coinciden -- un desajuste
    indicaría que el .pkl y el manifest quedaron de corridas distintas de
    build_husformer_dataset.py, útil para detectarlo temprano.
    """
    if not config.HUSFORMER_MANIFEST_FILE.exists():
        return

    import pandas as pd  # import local: pandas no es necesario para el resto del script

    manifest_df = pd.read_csv(config.HUSFORMER_MANIFEST_FILE)
    manifest_counts = manifest_df["split"].value_counts().to_dict()

    for split_name, extracted_count in split_counts.items():
        manifest_count = manifest_counts.get(split_name)
        if manifest_count is not None and manifest_count != extracted_count:
            print(
                f"[ADVERTENCIA] Split '{split_name}': el manifest tiene "
                f"{manifest_count} ventanas pero se extrajeron "
                f"{extracted_count} desde el .pkl -- probablemente el "
                "manifest y el .pkl vienen de corridas distintas de "
                "build_husformer_dataset.py."
            )


def save_metadata(
    checkpoint_path: Path,
    model: torch.nn.Module,
    split_outputs: dict[str, Path],
    split_counts: dict[str, int],
) -> None:
    """Guarda un JSON con la forma y el significado de lo extraído, para trazabilidad."""
    metadata: dict[str, Any] = {
        "checkpoint_used": str(checkpoint_path),
        "d_m": int(getattr(model, "d_m", 40)),
        "num_layers_cross_modal": 5,
        "num_layers_final": 5,
        "modality_order": ["modality_1", "modality_2", "modality_3", "modality_4", "modality_5"],
        "modality_labels": {
            "modality_1": "EEG (32 canales)",
            "modality_2": "EOG (4 canales)",
            "modality_3": "EMG (4 canales)",
            "modality_4": "GSR (1 canal)",
            "modality_5": "Resp + Plet + Temp (3 canales)",
        },
        "combined_seq_len": 640,
        "window_seq_len": 128,
        "attn_cross_summary_meaning": (
            "(N, 5, 5) = (ventana, modulo_query m{i}_all, grupo_modalidad_fuente). "
            "Promedio sobre capas + eje temporal + posiciones dentro del bloque fuente."
        ),
        "attn_final_summary_meaning": (
            "(N, 5, 5) = (ventana, grupo_modalidad_query, grupo_modalidad_key), "
            "auto-atencion final. Promedio sobre capas + posiciones dentro de cada bloque."
        ),
        "raw_attention_note": (
            "La atencion cruda completa (capa por capa, posicion por posicion) NO "
            "se guarda aqui -- se calcula al vuelo en el backend cuando el usuario "
            "inspecciona una ventana puntual (~25ms medido, ver test_return_attn.py "
            "y la seccion 'Estrategia de almacenamiento de atencion cross-modal' en "
            "estado_proyecto.md)."
        ),
        "splits": {
            split_name: {
                "n_windows": split_counts[split_name],
                "output_file": str(split_outputs[split_name].relative_to(config.DATASET_DIR)),
            }
            for split_name in split_outputs
        },
    }

    metadata_path: Path = config.REPRESENTATIONS_DIR / "extraction_metadata.json"

    with metadata_path.open("w", encoding="utf-8") as metadata_file:
        json.dump(metadata, metadata_file, indent=2, ensure_ascii=False)

    print(f"[OK] Metadata de extracción guardada: {metadata_path}")


def main() -> None:
    """Ejecuta la extracción completa: checkpoint entrenado -> last_hs + resumen de atención."""
    args: argparse.Namespace = parse_arguments()

    prepare_output_directory(clean=args.clean)

    checkpoint_path = Path(args.checkpoint)
    print(f"[INFO] Cargando modelo entrenado desde '{checkpoint_path}'...")
    model = load_trained_model(checkpoint_path)

    splits_to_process: tuple[str, ...] = SPLIT_NAMES if args.split == "all" else (args.split,)

    split_outputs: dict[str, Path] = {}
    split_counts: dict[str, int] = {}

    for split_name in splits_to_process:
        arrays = extract_split(split_name, model, batch_size=args.batch_size)
        output_path = save_split_outputs(split_name, arrays)
        split_outputs[split_name] = output_path
        split_counts[split_name] = len(arrays["local_id"])

    cross_check_against_manifest(split_counts)
    save_metadata(checkpoint_path, model, split_outputs, split_counts)

    print("\n[OK] Extracción completa.")


if __name__ == "__main__":
    main()


# ============================================================
# USO
# ============================================================
# Los 3 splits:
#   python -m backend.scripts.husformer.extract_representations
#
# Solo un split (por ejemplo, para probar rápido con 'test'):
#   python -m backend.scripts.husformer.extract_representations --split test
#
# Con un batch de inferencia distinto (bajar si aparece OutOfMemoryError):
#   python -m backend.scripts.husformer.extract_representations --batch_size 16
#
# Limpiando la salida anterior antes de re-extraer:
#   python -m backend.scripts.husformer.extract_representations --clean
