# models/eegnet.py

import torch
import torch.nn as nn

from config.settings import debug_mode_flag


class EEGNet(nn.Module):
    """
    EEGNet: Convolutional network for temporal and spatial EEG feature extraction.

    Args:
        F1 (int): Number of temporal filters.
        eegnet_kernel_size (int): Size of temporal filter.
        D (int): Depth multiplier for spatial convolution.
        eeg_chans (int): Number of EEG input channels.
        eegnet_separable_kernel_size (int): Size of separable convolution filter.
        eegnet_pooling_1 (int): Pooling size after spatial conv.
        eegnet_pooling_2 (int): Pooling size after depthwise conv.
        dropout (float): Dropout rate.
    """

    def __init__(
        self,
        F1: int = 16,
        eegnet_kernel_size: int = 32,
        D: int = 2,
        eeg_chans: int = 22,
        eegnet_separable_kernel_size: int = 16,
        eegnet_pooling_1: int = 8,
        eegnet_pooling_2: int = 4,
        dropout: float = 0.5,
    ) -> None:
        super(EEGNet, self).__init__()

        F2 = F1 * D
        self.dropout = nn.Dropout(dropout)

        # ===========================
        # Bloque 1: Convolución temporal
        # ===========================
        self.block1 = nn.Conv2d(
            1,
            F1,
            (1, eegnet_kernel_size),
            padding="same",
            bias=False,
        )
        self.bn1 = nn.BatchNorm2d(F1)

        # ===========================
        # Bloque 2: Convolución espacial
        # ===========================
        self.block2 = nn.Conv2d(
            F1,
            F2,
            (eeg_chans, 1),
            padding="valid",
            bias=False,
        )
        self.bn2 = nn.BatchNorm2d(F2)
        self.elu = nn.ELU()
        self.avg_pool1 = nn.AvgPool2d((1, eegnet_pooling_1))

        # ===========================
        # Bloque 3: Convolución separable (depthwise + pointwise)
        # ===========================
        self.block3 = nn.Conv2d(
            F2,
            F2,
            (1, eegnet_separable_kernel_size),
            padding="same",
            bias=False,
        )
        self.bn3 = nn.BatchNorm2d(F2)
        self.avg_pool2 = nn.AvgPool2d((1, eegnet_pooling_2))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass of EEGNet.

        Args:
            x: Tensor de entrada de forma (B, 1, C, L)
               B = batch_size
               C = número de canales EEG
               L = longitud de la señal

        Returns:
            Tensor procesado de forma (B, F2, 1, L_out)
        """

        # ---- Block 1 ----
        x = self.block1(x)
        if debug_mode_flag:
            print("Shape of x after block1 of EEGNet:", x.shape)

        x = self.bn1(x)

        # ---- Block 2 ----
        x = self.block2(x)
        if debug_mode_flag:
            print("Shape of x after block2 of EEGNet:", x.shape)

        x = self.bn2(x)
        x = self.elu(x)
        x = self.avg_pool1(x)
        x = self.dropout(x)

        if debug_mode_flag:
            print("Shape of x before block3 of EEGNet:", x.shape)

        # ---- Block 3 ----
        x = self.block3(x)
        if debug_mode_flag:
            print("Shape of x after block3 of EEGNet:", x.shape)

        x = self.bn3(x)
        x = self.elu(x)
        x = self.avg_pool2(x)
        x = self.dropout(x)

        if debug_mode_flag:
            print("Shape of x by the end of EEGNet:", x.shape)

        return x
