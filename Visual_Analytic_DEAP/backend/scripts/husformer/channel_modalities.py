from __future__ import annotations

import numpy as np


def split_window_into_modalities(
    window: np.ndarray,
    channel_names: list[str],
    channel_groups: dict[str, list[str]],
) -> dict[str, np.ndarray]:
    """
    Separa una ventana (n_canales, n_muestras) en las modalidades de Husformer.

    Busca los canales de cada modalidad POR NOMBRE (no por posición fija), para
    no depender de que el orden de canales sea idéntico entre participantes.

    IMPORTANTE sobre el orden de ejes de salida: Husformer (dataset.py +
    models.py) espera cada tensor de modalidad en formato
    (n_ventanas, n_muestras, n_canales) — es decir, TIEMPO primero, CANALES al
    final. Esto se confirmó revisando cómo models.py hace
    `m1.transpose(1, 2)` antes de pasarlo a `nn.Conv1d(orig_d_m1, ...)`: para
    que esa transposición entregue (batch, canales, muestras) a Conv1d, el
    tensor original debe ser (batch, muestras, canales). Por eso esta función
    retorna cada modalidad ya transpuesta a (n_muestras, n_canales_modalidad),
    aunque 'window' llega en formato MNE habitual (canales, muestras). No usar
    make_data/Pre-DEAP.py como referencia para esto: ese script reshapea de
    forma inconsistente (el propio reshape de su pkl_make no cuadra en
    tamaño con los datos que recibe) y no es una fuente confiable del
    formato real esperado por dataset.py/models.py.

    Parámetros:
    - window: ventana de una sola señal, shape (n_canales_totales, n_muestras).
    - channel_names: nombres de canal en el mismo orden que las filas de 'window'.
    - channel_groups: diccionario modalidad -> lista de nombres de canal
      esperados para esa modalidad (ver config.MODALITY_CHANNEL_GROUPS).

    Retorna un diccionario modalidad -> array (n_muestras, n_canales_modalidad),
    en float32.

    Lanza ValueError si algún canal esperado no está presente en channel_names,
    para detectar de forma explícita inconsistencias de canales entre trials.
    """
    channel_index_by_name: dict[str, int] = {
        channel_name: index for index, channel_name in enumerate(channel_names)
    }

    modalities: dict[str, np.ndarray] = {}

    for modality_name, expected_channels in channel_groups.items():
        missing_channels: list[str] = [
            channel for channel in expected_channels
            if channel not in channel_index_by_name
        ]

        if missing_channels:
            raise ValueError(
                f"Modalidad '{modality_name}': faltan los canales "
                f"{missing_channels} en esta ventana."
            )

        channel_indices: list[int] = [
            channel_index_by_name[channel] for channel in expected_channels
        ]

        # window[channel_indices, :] -> (n_canales_modalidad, n_muestras)
        # .T                          -> (n_muestras, n_canales_modalidad)
        modalities[modality_name] = window[channel_indices, :].T.astype(np.float32)

    return modalities
