# test_torch_cuda.py

import torch


def main() -> None:
    print("Torch version:", torch.__version__)
    print("CUDA available?:", torch.cuda.is_available())

    if torch.cuda.is_available():
        device_index: int = torch.cuda.current_device()
        device_name: str = torch.cuda.get_device_name(device_index)
        device_count: int = torch.cuda.device_count()

        print("CUDA device count:", device_count)
        print("Current device index:", device_index)
        print("Current device name:", device_name)
        print("\n")
        print(torch.cuda.get_device_name(0))
    else:
        print("Running on CPU only.")


if __name__ == "__main__":
    main()
