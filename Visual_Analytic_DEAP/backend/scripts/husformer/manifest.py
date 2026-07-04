from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def save_manifest(manifest_rows: list[dict[str, Any]], output_path: Path) -> None:
    """
    Guarda el manifest de trazabilidad como CSV.

    Cada fila conecta una ventana con su contexto original: participante,
    trial, instante de inicio de la ventana, las 4 dimensiones afectivas de
    participant_ratings, y a qué split pertenece.

    Incluye tanto 'global_window_id' (contador único a través de TODOS los
    splits, útil para depuración) como 'local_id' (el índice 0..N-1 dentro de
    su propio split). 'local_id' es el que hay que usar para reconectar una
    fila de este manifest con el campo 'id' dentro de Husformer.pkl: filtra
    este CSV por 'split' y usa 'local_id' como índice directo — así es como
    el sistema VA va a unir las representaciones/atención extraídas del
    modelo con su contexto original (participante, trial, instante).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest_dataframe: pd.DataFrame = pd.DataFrame(manifest_rows)
    manifest_dataframe.to_csv(output_path, index=False)

    print(f"[OK] Manifest guardado en: {output_path} ({len(manifest_dataframe)} filas)")
