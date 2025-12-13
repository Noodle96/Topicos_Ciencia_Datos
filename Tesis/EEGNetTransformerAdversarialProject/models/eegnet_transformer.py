import math
import torch
import torch.nn as nn

from models.eegnet import EEGNet  # Adjust path if needed
from models.positional_encoding import PositionalEncoding  # Adjust path if needed
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
    ):
        """
        EEGNetTransformerNet integrates the EEGNet front-end with a Transformer encoder for classification.

        Args:
            nb_classes: number of output classes.
            sequence_length: length of input EEG signal.
            eeg_chans: number of EEG channels.
            F1: number of temporal filters.
            D: depth multiplier (F2 = F1 * D).
            eegnet_kernel_size: kernel size for EEGNet temporal convolution.
            dropout_eegnet: dropout rate used in EEGNet.
            eegnet_pooling_1: pooling size after first EEGNet block.
            eegnet_pooling_2: pooling size after third EEGNet block.
            MSA_num_heads: number of attention heads in the Transformer.
            flag_positional_encoding: whether to apply positional encoding.
            transformer_dim_feedforward: hidden size of the Transformer feedforward layer.
            num_transformer_layers: number of Transformer layers.
        """
        super(EEGTransformerNet, self).__init__()

        F2 = F1 * D
        self.sequence_length_transformer = (
            sequence_length // eegnet_pooling_1 // eegnet_pooling_2
        )

        # EEGNet frontend
        self.eegnet = EEGNet(
            eeg_chans=eeg_chans,
            F1=F1,
            eegnet_kernel_size=eegnet_kernel_size,
            D=D,
            eegnet_pooling_1=eegnet_pooling_1,
            eegnet_pooling_2=eegnet_pooling_2,
            dropout=dropout_eegnet,
        )

        # Linear projection at the end
        self.linear = nn.Linear(self.sequence_length_transformer, nb_classes)

        # Positional Encoding
        self.flag_positional_encoding = flag_positional_encoding
        self.pos_encoder = PositionalEncoding(
            self.sequence_length_transformer,
            dropout=0.3,
        )

        # Transformer Encoder
        self.transformer_encoder_layer = nn.TransformerEncoderLayer(
            d_model=self.sequence_length_transformer,
            nhead=MSA_num_heads,
            dim_feedforward=transformer_dim_feedforward,
        )
        self.transformer_encoder = nn.TransformerEncoder(
            self.transformer_encoder_layer,
            num_layers=num_transformer_layers,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Input shape: (batch_size, num_channels, seq_len) = (B, 22, L)

        x = torch.unsqueeze(x, 1)  # (B, 1, 22, L)
        x = self.eegnet(x)  # (B, F1*D, 1, L//pool1//pool2)

        x = torch.squeeze(x)  # (B, F1*D, L//pool1//pool2)
        x = x.permute(2, 0, 1)  # (seq_len, B, C)

        seq_len_transformer, batch_size_transformer, channels_transformer = x.shape
        device = x.device

        # Add a learnable [CLS]-like token at channel dimension
        x = torch.cat(
            (
                torch.zeros(
                    (seq_len_transformer, batch_size_transformer, 1),
                    requires_grad=True,
                ).to(device),
                x,
            ),
            dim=2,
        )

        x = x.permute(2, 1, 0)  # (C+1, B, seq_len)

        if debug_mode_flag:
            print("Shape of x before Transformer:", x.shape)

        # Positional encoding
        if self.flag_positional_encoding:
            x = x * math.sqrt(self.sequence_length_transformer)
            x = self.pos_encoder(x)
            if debug_mode_flag:
                print("Positional Encoding Done!")

        if debug_mode_flag:
            print("Shape of x after Transformer:", x.shape)

        # Transformer encoder
        x = self.transformer_encoder(x)  # (C+1, B, seq_len)

        # Take the first channel (CLS-like)
        x = x[0, :, :].reshape(batch_size_transformer, -1)  # (B, seq_len)

        if debug_mode_flag:
            print("Shape of x before linear layer:", x.shape)

        # Classification
        x = self.linear(x)  # (B, nb_classes)

        return x
