# models/eegnet_transformer_adversarial.py

from __future__ import annotations

from typing import Tuple

import torch
import torch.nn as nn
from torch.autograd import Function

from models.eegnet_transformer import EEGTransformerNet


class _GradientReversalFunction(Function):
    """
    Gradient Reversal Layer (GRL) - implementación clásica tipo DANN.

    Forward:
        y = x  (identidad)

    Backward:
        dL/dx = -lambda * dL/dy
    """

    @staticmethod
    def forward(ctx, x: torch.Tensor, grl_lambda: float) -> torch.Tensor:
        ctx.grl_lambda = float(grl_lambda)
        # Retornamos una vista idéntica (sin modificar valores)
        return x.view_as(x)

    @staticmethod
    def backward(ctx, grad_output: torch.Tensor) -> Tuple[torch.Tensor, None]:
        grl_lambda: float = float(ctx.grl_lambda)
        grad_input: torch.Tensor = -grl_lambda * grad_output
        return grad_input, None


class GradientReversalLayer(nn.Module):
    """
    Capa GRL como nn.Module para usar dentro de modelos.
    """

    def __init__(self) -> None:
        super().__init__()

    def forward(self, x: torch.Tensor, grl_lambda: float) -> torch.Tensor:
        return _GradientReversalFunction.apply(x, grl_lambda)


class EEGNetTransformerAdversarial(nn.Module):
    """
    Modelo adversarial (DANN) basado en backbone EEGTransformerNet.

    Devuelve dos logits:
      - class_logits  : (B, num_classes)   para bckg vs seizure
      - domain_logits : (B, num_domains)   para paciente (dominio)

    Importante:
      - En el branch de dominio se aplica GRL (Gradient Reversal Layer).
      - La firma forward acepta grl_lambda para controlar la fuerza adversarial.
    """

    def __init__(
        self,
        backbone: EEGTransformerNet,
        num_classes: int,
        num_domains: int,
        dropout: float = 0.5,
    ) -> None:
        super().__init__()

        self.backbone: EEGTransformerNet = backbone
        self.embedding_dim: int = int(backbone.embedding_dim)

        # GRL
        self.grl: GradientReversalLayer = GradientReversalLayer()

        # Cabeza de clasificación (evento)
        self.class_head: nn.Module = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(self.embedding_dim, num_classes),
        )

        # Cabeza de dominio (paciente)
        self.domain_head: nn.Module = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(self.embedding_dim, num_domains),
        )

    def forward(
        self,
        x: torch.Tensor,
        grl_lambda: float = 1.0,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Args:
            x: EEG tensor (B, C, T) típicamente (B, 22, 1000)
            grl_lambda: fuerza adversarial. Si 0.0, GRL no invierte gradiente.

        Returns:
            class_logits: (B, num_classes)
            domain_logits: (B, num_domains)
        """
        # Features (B, embedding_dim)
        features: torch.Tensor = self.backbone.forward_features(x)

        # Logits de clase
        class_logits: torch.Tensor = self.class_head(features)

        # GRL en branch de dominio
        features_grl: torch.Tensor = self.grl(features, grl_lambda)
        domain_logits: torch.Tensor = self.domain_head(features_grl)

        return class_logits, domain_logits
