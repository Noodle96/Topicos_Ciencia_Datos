small_config = {
    "nb_classes": 2,
    "sequence_length": 1000,
    "eeg_chans": 22,
    "F1": 16,
    "D": 2,
    "eegnet_kernel_size": 32,
    "dropout_eegnet": 0.3,
    "eegnet_pooling_1": 5,
    "eegnet_pooling_2": 5,
    "MSA_num_heads": 2,  # 🔻 reducido de 8
    "flag_positional_encoding": True,
    "transformer_dim_feedforward": 256,  # 🔻 reducido de 2048
    "num_transformer_layers": 1,  # 🔻 reducido de 6
    "batch_size": 16,  # 🔻 muy importante
    "learning_rate": 1e-4,  # 🔻 recomendado para estabilidad
    "epochs": 100,
    "patience": 10,  # early stopping
}
