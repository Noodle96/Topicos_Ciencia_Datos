# in "script" folder:
#    python check_dataset.py

import os
import sys

PROJECT_ROOT: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
print(f"Project root: {PROJECT_ROOT}")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from data.adversarial_dataset import AdversarialNumpyDataset




def main() -> None:
    dataset: AdversarialNumpyDataset = AdversarialNumpyDataset(
        root_dir="../../data_procesada/TUSZ_processed_binary_individual_segments/segment_interval_4_sec/val"
    )

    print("Total samples:", len(dataset))
    print("Total patients (domains):", len(dataset.patient_to_domain))

    x, y_class, y_domain = dataset[16000]
    print(x.shape, y_class, y_domain)

    # recorrer todo el dataset y hacer etso: x, y_class, y_domain = dataset[0] print(x.shape, y_class, y_domain)
    # for i in range(len(dataset)):
    #     x, y_class, y_domain = dataset[i]
    #     print(x.shape, y_class, y_domain)
if __name__ == "__main__":
    main()
