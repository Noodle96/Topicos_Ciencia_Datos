from typing import List, Tuple
import os

import numpy as np
from torch.utils.data import Dataset, DataLoader


class NumpyDataset(Dataset):
    """
    Dataset para cargar segmentos EEG guardados como archivos .npy.

    Cada clase ('bckg', 'seiz') tiene su propia subcarpeta.
    Cada archivo .npy puede contener múltiples ventanas (shape = [N, 22, 1000]).

    Args:
        root_dir (str): Ruta a la carpeta que contiene subdirectorios por clase.
    """

    def __init__(self, root_dir: str):
        self.root_dir: str = root_dir
        self.classes: List[str] = sorted(os.listdir(root_dir))  # ['bckg', 'seiz']
        self.data: List[Tuple[np.ndarray, int]] = []

        for class_index, class_name in enumerate(self.classes):
            class_path: str = os.path.join(root_dir, class_name)
            file_list: List[str] = sorted(os.listdir(class_path))

            for file_name in file_list:
                file_path: str = os.path.join(class_path, file_name)
                array: np.ndarray = np.load(file_path)  # array.shape = (N, 22, 1000)

                for i in range(array.shape[0]):
                    # una ventana, un label
                    self.data.append((array[i], class_index))

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index: int) -> Tuple[np.ndarray, int]:
        window, label = self.data[index]
        return window, label


def get_dataloaders(
    data_root: str,
    batch_size: int = 16,
) -> Tuple[DataLoader, DataLoader, DataLoader]:
    """
    Crea los dataloaders para train, val y test usando NumpyDataset.

    Args:
        data_root (str): Ruta base con subcarpetas train/, val/, test/.
        batch_size (int): Tamaño de lote recomendado según la GPU.

    Returns:
        Tuple[DataLoader, DataLoader, DataLoader]:
            dataloaders para train, val y test.
    """
    train_dataset: NumpyDataset = NumpyDataset(os.path.join(data_root, "train"))
    val_dataset: NumpyDataset = NumpyDataset(os.path.join(data_root, "val"))
    test_dataset: NumpyDataset = NumpyDataset(os.path.join(data_root, "test"))

    train_loader: DataLoader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=0,
    )
    val_loader: DataLoader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )
    test_loader: DataLoader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=0,
    )

    return train_loader, val_loader, test_loader
