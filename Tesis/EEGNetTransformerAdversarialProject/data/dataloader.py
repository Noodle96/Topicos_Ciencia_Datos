from typing import List, Tuple
import os

import numpy as np
from torch.utils.data import Dataset, DataLoader
from config.settings import debug_mode_flag

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
        self.classes: List[str] = sorted(os.listdir(root_dir))  # ['bckg', 'seizure']
        self.data: List[Tuple[np.ndarray, int]] = []
        if(debug_mode_flag):
            print("\n\n[DEBUG] testing config.settings debug_mode_flag:", debug_mode_flag) # [DEBUG] testing config.settings debug_mode_flag: True
            print(f"[DEBUG] Loading data from: {root_dir}")  #[DEBUG] Loading data from: ../data_procesada/TUSZ_processed_binary_individual_segments/segment_interval_4_sec/train
            print(f"[DEBUG] Found classes: {self.classes}") #[DEBUG] Found classes: ['bckg', 'seizure']

        for class_index, class_name in enumerate(self.classes):
            class_path: str = os.path.join(root_dir, class_name)
            file_list: List[str] = sorted(os.listdir(class_path))
            if debug_mode_flag:
                print(f"[DEBUG] Loading class '{class_name}' from: {class_path} with {len(file_list)} files.") # [DEBUG] Loading class 'bckg/seizure' from: ../data_procesada/TUSZ_processed_binary_individual_segments/segment_interval_4_sec/train/bckg with 510 files.
                # print(f"[DEBUG] file_list: {file_list}")
                print(f"\n[DEBUG] iterate file list")
            for file_name in file_list:
                file_path: str = os.path.join(class_path, file_name)
                array: np.ndarray = np.load(file_path)  # array.shape = (N, 22, 1000)
                if debug_mode_flag:
                    print(f"\t[DEBUG] Loading file: {file_path}") 
                    print(f"\t[DEBUG] array.shape: {array.shape}")

                for i in range(array.shape[0]):
                    # una ventana, un label
                    self.data.append((array[i], class_index))

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, index: int) -> Tuple[np.ndarray, int]:
        window, label = self.data[index]
        return window, label

def get_train_val_loaders(
    data_root: str,
    batch_size: int = 16,
) -> Tuple[DataLoader, DataLoader]:
    """
    Crea DataLoaders únicamente para entrenamiento y validación.

    IMPORTANTE:
    - SOLO carga a RAM los datos de train/ y val/
    - No toca test/, evitando consumo innecesario de memoria

    Args:
        data_root (str): Ruta base con subcarpetas train/ y val/
        batch_size (int): Tamaño de batch

    Returns:
        Tuple[DataLoader, DataLoader]: (train_loader, val_loader)
    """
    train_dataset: NumpyDataset = NumpyDataset(os.path.join(data_root, "train"))
    val_dataset: NumpyDataset = NumpyDataset(os.path.join(data_root, "val"))

    if debug_mode_flag:
        print(f"[DATALOADER] Train samples: {len(train_dataset)}")
        print(f"[DATALOADER] Val samples  : {len(val_dataset)}")

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

    return train_loader, val_loader

def get_test_loader( data_root: str, batch_size: int = 16) -> DataLoader:
    """
    Crea DataLoader únicamente para test.

    IMPORTANTE:
    - Se debe llamar SOLO al final del entrenamiento
    - Permite liberar memoria de train/val antes de cargar test

    Args:
        data_root (str): Ruta base con subcarpeta test/
        batch_size (int): Tamaño de batch

    Returns:
        DataLoader: test_loader
    """
    test_dataset: NumpyDataset = NumpyDataset( os.path.join(data_root, "test") )

    if debug_mode_flag:
        print(f"[DATALOADER] Test samples: {len(test_dataset)}")

    test_loader: DataLoader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False, num_workers=0 )

    return test_loader