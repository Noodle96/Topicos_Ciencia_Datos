# in "script" folder:
#    python check_dataloader.py

import os
import sys

PROJECT_ROOT: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)
print(f"Project root: {PROJECT_ROOT}")
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from data.dataloader_adversarial import (
    get_adversarial_train_val_loaders,
    get_adversarial_test_loader,
)




def main() -> None:
    data_root: str = (
        "../../data_procesada/TUSZ_processed_binary_individual_segments/segment_interval_4_sec"
    )

    train_loader, val_loader = get_adversarial_train_val_loaders(
        data_root=data_root,
        batch_size=16,
        shuffle_train=True,
    )

    # test_loader = get_adversarial_test_loader(
    #     data_root=data_root,
    #     batch_size=16,
    # )

    print("Train loader batches:", len(train_loader))
    print("Val loader batches:", len(val_loader))
    # print("Test loader batches:", len(test_loader))

    # Obtener un batch de train
    for x, y_class, y_domain in train_loader:
        print("Train batch:")
        print("x shape:", x.shape)
        print("y_class shape:", y_class.shape)
        print("y_domain shape:", y_domain.shape)
        break

    # Obtener un batch de val
    for x, y_class, y_domain in val_loader:
        print("Val batch:")
        print("x shape:", x.shape)
        print("y_class shape:", y_class.shape)
        print("y_domain shape:", y_domain.shape)
        break

    # Obtener un batch de test
    # for x, y_class, y_domain in test_loader:
    #     print("Test batch:")
    #     print("x shape:", x.shape)
    #     print("y_class shape:", y_class.shape)
    #     print("y_domain shape:", y_domain.shape)
    #     break
   
if __name__ == "__main__":
    main()
