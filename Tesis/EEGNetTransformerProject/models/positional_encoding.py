# models/positional_encoding.py

import math
import torch
import torch.nn as nn
from torch import Tensor


class PositionalEncoding(nn.Module):
    """
    PositionalEncoding: Codificación posicional senoidal para secuencias en Transformer.

    Args:
        d_model (int): Dimensión del embedding.
        dropout (float): Tasa de dropout aplicada tras la suma de la codificación posicional.
        max_len (int): Longitud máxima de la secuencia a codificar.
    """

    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000) -> None:
        # super(PositionalEncoding, self).__init__()
        super().__init__()

        self.dropout = nn.Dropout(p=dropout)

        # ----------------------------
        # Construcción de codificación posicional senoidal
        # ----------------------------
        position = torch.arange(max_len).unsqueeze(1)          # [max_len, 1]
        div_term = torch.exp(
            torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model)
        )                                                      # [d_model//2]

        pe = torch.zeros(max_len, 1, d_model)                  # [max_len, 1, d_model]
        pe[:, 0, 0::2] = torch.sin(position * div_term)        # Dimensiones pares
        pe[:, 0, 1::2] = torch.cos(position * div_term)        # Dimensiones impares

        # Registrar como buffer → no se entrena
        self.register_buffer("pe", pe)

    def forward(self, x: Tensor) -> Tensor:
        """
        Agrega codificación posicional a la entrada.

        Args:
            x (Tensor): Tensor de forma (seq_len, batch_size, d_model)

        Returns:
            Tensor: Entrada con codificación posicional aplicada.
        """
        x = x + self.pe[: x.size(0)]
        return self.dropout(x)
