# data/adversarial_dataset.py

from typing import Dict, List, Tuple
import os

import numpy as np
import torch
from torch.utils.data import Dataset


class AdversarialNumpyDataset(Dataset):
    """
    Dataset adversarial para EEG que devuelve:
        (x, y_class, y_domain)

    - x        : np.ndarray / Tensor de forma (22, 1000)
    - y_class : int (0=bckg, 1=seizure)
    - y_domain: int (patient_id codificado, mapping por split)

    El mapping patient_id -> domain_id se construye automáticamente
    al inicializar el Dataset (Opción A).
    """

    def __init__(self, root_dir: str) -> None:
        """
        Args:
            root_dir (str):
                Ruta a un split específico:
                - .../train
                - .../val
                - .../test
        """
        self.root_dir: str = root_dir
        self.classes: List[str] = sorted(os.listdir(root_dir))  # ['bckg', 'seizure']

        # Almacenamos todas las muestras aquí
        # Cada elemento: (x, y_class, y_domain)
        self.samples: List[Tuple[np.ndarray, int, int]] = []

        # Mapping patient_id -> domain_id (por split)
        self.patient_to_domain: Dict[str, int] = {}

        self._build_dataset()

    def _build_dataset(self) -> None:
        """
        Recorre el directorio del split y construye:
        - samples
        - patient_to_domain
        """
        current_domain_id: int = 0

        for class_index, class_name in enumerate(self.classes):
            class_path: str = os.path.join(self.root_dir, class_name)

            if not os.path.isdir(class_path):
                continue

            file_list: List[str] = sorted(os.listdir(class_path))

            for file_name in file_list:
                if not file_name.endswith(".npy"):
                    continue

                file_path: str = os.path.join(class_path, file_name)

                # Extraer patient_id desde el nombre del archivo
                # Ejemplo: aaaaatds_s003_t010.npy -> aaaaatds
                patient_id: str = file_name.split("_")[0]

                # Asignar domain_id si es la primera vez que vemos este paciente
                if patient_id not in self.patient_to_domain:
                    self.patient_to_domain[patient_id] = current_domain_id
                    current_domain_id += 1

                domain_id: int = self.patient_to_domain[patient_id]

                # Cargar el archivo .npy
                # Shape esperado: (N, 22, 1000)
                windows: np.ndarray = np.load(file_path)

                for i in range(windows.shape[0]):
                    x: np.ndarray = windows[i]
                    y_class: int = class_index
                    y_domain: int = domain_id

                    self.samples.append((x, y_class, y_domain))

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, int, int]:
        x_np, y_class, y_domain = self.samples[index]

        # Convertimos a Tensor aquí (float32)
        x: torch.Tensor = torch.from_numpy(x_np).float()

        return x, y_class, y_domain
