# data/dataloader_adversarial.py

from typing import Tuple
import os

from torch.utils.data import DataLoader

from data.adversarial_dataset import AdversarialNumpyDataset


def get_adversarial_train_val_loaders(
    data_root: str,
    batch_size: int,
    shuffle_train: bool = True,
) -> Tuple[DataLoader, DataLoader]:
    """
    Crea DataLoaders adversariales para TRAIN y VAL.

    Cada batch devuelve:
        x        : Tensor [B, 22, 1000]
        y_class  : Tensor [B]
        y_domain : Tensor [B]

    Importante:
    - SOLO se cargan train y val (no test).
    - Controla el uso de RAM.
    """

    train_dataset = AdversarialNumpyDataset(
        root_dir=os.path.join(data_root, "train"),
    )

    val_dataset = AdversarialNumpyDataset(
        root_dir=os.path.join(data_root, "val"),
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=shuffle_train,
        num_workers=0,
        pin_memory=True,
    )

    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=True,
    )

    return train_loader, val_loader


def get_adversarial_test_loader(
    data_root: str,
    batch_size: int,
) -> DataLoader:
    """
    Crea DataLoader adversarial SOLO para TEST.

    Se usa únicamente después del entrenamiento.
    """

    test_dataset = AdversarialNumpyDataset(
        root_dir=os.path.join(data_root, "test"),
    )

    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
        pin_memory=True,
    )

    return test_loader
