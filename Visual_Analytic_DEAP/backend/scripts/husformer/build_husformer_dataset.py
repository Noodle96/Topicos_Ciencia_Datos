from __future__ import annotations

import argparse

from . import config
from .dataset_builder import build_full_dataset, save_pkl
from .manifest import save_manifest
from .participant_split import validate_full_participant_coverage


def parse_arguments() -> argparse.Namespace:
    """Define los argumentos de línea de comandos del orquestador."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser(
        description=(
            "Construye Husformer.pkl y su manifest de trazabilidad a partir de "
            "los .npz de dataset/processed/representation_inputs/. "
            "Pipeline completo, paso a paso: "
            "(0) carga y valida metadata global [dataset_builder.py]; "
            "(1) ventanea cada trial en ventanas de 1s [windowing.py]; "
            "(2) separa cada ventana en 5 modalidades [channel_modalities.py]; "
            "(3) convierte valencia -> etiqueta de 3 clases [labeling.py]; "
            "(4) asigna cada ventana a train/valid/test por participante "
            "[participant_split.py]; "
            "(5-6) arma la estructura final y guarda Husformer.pkl "
            "[dataset_builder.py]; "
            "(7) guarda el manifest de trazabilidad [manifest.py]."
        )
    )

    parser.add_argument(
        "--participants",
        type=str,
        default="all",
        help=(
            "Participantes a procesar. Ejemplo: all, 1, 1,3,11 "
            "(para una prueba rápida, incluir al menos un participante de "
            "cada split: ver config.PARTICIPANT_SPLIT)."
        ),
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Elimina Husformer.pkl y el manifest existentes antes de reconstruir.",
    )

    return parser.parse_args()


def parse_participants(value: str) -> list[int] | None:
    """Convierte el argumento --participants a una lista de IDs, o None si es 'all'."""
    if value == "all":
        return None

    return [int(item.strip()) for item in value.split(",") if item.strip()]


def main() -> None:
    """Ejecuta el pipeline completo: .npz de representation_inputs -> Husformer.pkl + manifest."""
    args: argparse.Namespace = parse_arguments()
    participants_to_process: list[int] | None = parse_participants(args.participants)

    if args.clean:
        for path in (config.HUSFORMER_PKL_FILE, config.HUSFORMER_MANIFEST_FILE):
            if path.exists():
                path.unlink()
                print(f"[INFO] Eliminado: {path}")

    print("[INFO] Validando cobertura de splits por participante...")
    validate_full_participant_coverage()
    print("[OK] Los 32 participantes tienen split asignado, sin duplicados.")

    print("[INFO] Construyendo dataset (esto puede tardar varios minutos con los 32 participantes)...")
    dataset_dict, manifest_rows = build_full_dataset(
        participants_to_process=participants_to_process,
    )

    print("[INFO] Guardando Husformer.pkl...")
    save_pkl(dataset_dict, config.HUSFORMER_PKL_FILE)

    print("[INFO] Guardando manifest de trazabilidad...")
    save_manifest(manifest_rows, config.HUSFORMER_MANIFEST_FILE)

    print("[OK] Pipeline completo.")


if __name__ == "__main__":
    main()


# ============================================================
# USO
# ============================================================
# Prueba rápida con un participante de cada split (train/valid/test):
#   python -m backend.scripts.husformer.build_husformer_dataset --participants 1,3,11 --clean
#
# Construcción completa (32 participantes):
#   python -m backend.scripts.husformer.build_husformer_dataset --clean
