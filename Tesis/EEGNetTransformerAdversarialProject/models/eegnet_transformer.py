import math
import torch
import torch.nn as nn

from models.eegnet import EEGNet
from models.positional_encoding import PositionalEncoding
from config.settings import debug_mode_flag


class EEGTransformerNet(nn.Module):
    def __init__(
        self,
        nb_classes: int,
        sequence_length: int,
        eeg_chans: int = 22,
        F1: int = 16,
        D: int = 2,
        eegnet_kernel_size: int = 32,
        dropout_eegnet: float = 0.3,
        eegnet_pooling_1: int = 5,
        eegnet_pooling_2: int = 5,
        MSA_num_heads: int = 8,
        flag_positional_encoding: bool = True,
        transformer_dim_feedforward: int = 2048,
        num_transformer_layers: int = 6,
    ) -> None:
        super().__init__()

        # ======================================================
        # Dimensiones
        # ======================================================
        self.sequence_length_transformer: int = (
            sequence_length // eegnet_pooling_1 // eegnet_pooling_2
        )

        # Esta es la dimensión del embedding final (CLS)
        self.embedding_dim: int = self.sequence_length_transformer

        # ======================================================
        # EEGNet frontend
        # ======================================================
        self.eegnet = EEGNet(
            eeg_chans=eeg_chans,
            F1=F1,
            eegnet_kernel_size=eegnet_kernel_size,
            D=D,
            eegnet_pooling_1=eegnet_pooling_1,
            eegnet_pooling_2=eegnet_pooling_2,
            dropout=dropout_eegnet,
        )

        # ======================================================
        # Positional Encoding
        # ======================================================
        self.flag_positional_encoding: bool = flag_positional_encoding
        self.pos_encoder = PositionalEncoding(
            d_model=self.sequence_length_transformer,
            dropout=0.3,
        )

        # ======================================================
        # Transformer Encoder
        # ======================================================
        self.transformer_encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.sequence_length_transformer,
            nhead=MSA_num_heads,
            dim_feedforward=transformer_dim_feedforward,
        )
        self.transformer_encoder = nn.TransformerEncoder(
            self.transformer_encoder_layer,
            num_layers=num_transformer_layers,
        )

        # ======================================================
        # Clasificador final (baseline)
        # ======================================================
        self.classifier = nn.Linear(
            self.embedding_dim,
            nb_classes,
        )

    # ==========================================================
    # NUEVO: forward_features
    # ==========================================================
    def forward_features(self, x: torch.Tensor) -> torch.Tensor:
        """
        Extrae el embedding (features) antes de la capa de clasificación.

        Args:
            x: Tensor EEG (B, C, T)

        Returns:
            features: Tensor (B, embedding_dim)
        """
        # (B, C, T) → (B, 1, C, T)
        x = torch.unsqueeze(x, 1)

        # EEGNet
        x = self.eegnet(x)  # (B, F2, 1, L')

        # (B, F2, L')
        x = torch.squeeze(x)
        x = x.permute(2, 0, 1)  # (L', B, F2)

        seq_len, batch_size, _ = x.shape
        device = x.device

        # CLS token
        cls_token = torch.zeros(
            (seq_len, batch_size, 1),
            device=device,
            requires_grad=True,
        )
        x = torch.cat((cls_token, x), dim=2)

        # (C+1, B, L')
        x = x.permute(2, 1, 0)

        if self.flag_positional_encoding:
            x = x * math.sqrt(self.sequence_length_transformer)
            x = self.pos_encoder(x)

        # Transformer
        x = self.transformer_encoder(x)

        # CLS embedding
        features = x[0, :, :]  # (B, embedding_dim)

        if debug_mode_flag:
            print("[DEBUG] features shape:", features.shape)

        return features

    # ==========================================================
    # forward (baseline intacto)
    # ==========================================================
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward estándar del baseline (clasificación).
        """
        features = self.forward_features(x)
        logits = self.classifier(features)
        return logits
