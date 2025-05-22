from typing import List, Tuple, Dict, Union
import os
import mne
import numpy as np
from scipy.signal import butter, filtfilt, resample, iirnotch, lfilter
from scipy.fft import rfft, rfftfreq
import matplotlib.pyplot as plt


def get_all_TUSZ_2023_session_paths(
    rootPath: str
) -> Tuple[List[str], List[str], Dict[str, int]]:
    """Recorre la carpeta raíz 'rootPath' y devuelve información de sesiones.
    Args:
        rootPath (str): Ruta al directorio que contiene subcarpetas por paciente.
    Returns:
        Tuple[List[str], List[str], Dict[str, int]]:
            - session_paths: Lista de rutas completas a cada archivo .edf.
            - all_patients: Lista de nombres de pacientes encontrados.
            - reference_type_count: Diccionario que mapea cada tipo de referencia
              a la cantidad de veces que aparece.
    """
    session_paths: List[str] = []
    all_patients: List[str] = os.listdir(rootPath)
    reference_type_count: Dict[str, int] = {}

    for patient in all_patients:
        patient: str
        patient_dir: str = os.path.join(rootPath, patient)
        patient_sessions: List[str] = os.listdir(patient_dir)
        for patient_session in patient_sessions:
            patient_session: str
            session_dir: str = os.path.join(patient_dir, patient_session)
            reference_types: List[str] = os.listdir(session_dir)
            for reference_type in reference_types:
                reference_type: str
                reference_type_count[reference_type] = reference_type_count.get(reference_type, 0) + 1
                ref_dir: str = os.path.join(session_dir, reference_type)
                files: List[str] = os.listdir(ref_dir)
                for file in files:
                    file: str
                    if file.endswith(".edf"):
                        full_path: str = os.path.join(ref_dir, file)
                        session_paths.append(full_path)

    return session_paths, all_patients, reference_type_count


def get_channels_from_raw(
    raw: mne.io.BaseRaw
) -> Tuple[bool, Union[int, np.ndarray]]:
    """Extrae la diferencia de dos montajes de canales EEG de una señal cruda.

    Este método carga dos subconjuntos de canales (montajes) definidos en listas
    preestablecidas, obtiene sus datos y devuelve la diferencia señal por señal.
    Si ocurre un error al leer los canales, informa el fallo.

    Args:
        raw (mne.io.BaseRaw): Objeto de MNE que contiene la señal EEG en crudo.

    Returns:
        Tuple[bool, Union[int, np.ndarray]]:
            - flag_wrong (bool): Indica True si ocurrió un error, False en caso contrario.
            - result (int o np.ndarray):
                - 0 si hubo un error al leer canales.
                - Matriz de numpy con la diferencia entre los dos montajes de canales.
    """
    montage_list_1: List[str] = [
        "EEG FP1-REF", "EEG F7-REF", "EEG T3-REF", "EEG T5-REF",
        "EEG FP2-REF", "EEG F8-REF", "EEG T4-REF", "EEG T6-REF",
        "EEG T3-REF", "EEG C3-REF", "EEG CZ-REF", "EEG C4-REF",
        "EEG FP1-REF", "EEG F3-REF", "EEG C3-REF", "EEG P3-REF",
        "EEG FP2-REF", "EEG F4-REF", "EEG C4-REF", "EEG P4-REF"
    ]
    montage_list_2: List[str] = [
        "EEG F7-REF", "EEG T3-REF", "EEG T5-REF", "EEG O1-REF",
        "EEG F8-REF", "EEG T4-REF", "EEG T6-REF", "EEG O2-REF",
        "EEG C3-REF", "EEG CZ-REF", "EEG C4-REF", "EEG T4-REF",
        "EEG F3-REF", "EEG C3-REF", "EEG P3-REF", "EEG O1-REF",
        "EEG F4-REF", "EEG C4-REF", "EEG P4-REF", "EEG O2-REF"
    ]

    montage_indices_1: List[int] = [raw.ch_names.index(ch) for ch in montage_list_1]
    montage_indices_2: List[int] = [raw.ch_names.index(ch) for ch in montage_list_2]

    try:
        signals_1: np.ndarray = raw.get_data(picks=montage_indices_1)
        signals_2: np.ndarray = raw.get_data(picks=montage_indices_2)
    except Exception:
        print("Something is wrong when reading channels of the raw EEG signal")
        flag_wrong: bool = True
        return flag_wrong, 0
    else:
        flag_wrong: bool = False

    result: np.ndarray = signals_1 - signals_2
    return flag_wrong, result


def butter_bandpass(
    lowcut: float,
    highcut: float,
    fs: float,
    order: int = 3
) -> Tuple[np.ndarray, np.ndarray]:
    nyq: float = 0.5 * fs
    low: float = lowcut / nyq
    high: float = highcut / nyq
    b: np.ndarray
    a: np.ndarray
    b, a = butter(order, [low, high], btype="band")
    return b, a


def butter_bandpass_filter(
    data: np.ndarray,
    lowcut: float,
    highcut: float,
    fs: float,
    order: int = 3
) -> np.ndarray:
    b: np.ndarray
    a: np.ndarray
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y: np.ndarray = filtfilt(b, a, data)
    return y


def slice_signals_into_binary_segments(
    signals: np.ndarray,
    thisFS: int,
    labels: List[Tuple[int, int, str]],
    segment_interval: float,
    seizure_types: List[str],
    seizure_overlapping_ratio: List[float]
) -> List[List[np.ndarray]]:
    segments: List[List[np.ndarray]] = [[] for _ in seizure_types]

    for this_label in labels:
        this_label: Tuple[int, int, str]
        start: int
        end: int
        label: str
        start, end, label = this_label
        label_index: int = 0 if label == "bckg" else 1
        seg: List[np.ndarray] = []
        step: int = int(segment_interval * (1 - seizure_overlapping_ratio[label_index]) * thisFS)

        for i in range(start * thisFS, end * thisFS, step):
            i: int
            if i + segment_interval * thisFS > end * thisFS:
                break
            one_window: List[np.ndarray] = []
            noise_flag: bool = False
            incomplete_flag: bool = False

            for chan in signals:
                chan: np.ndarray
                window: np.ndarray = chan[i : i + int(segment_interval * thisFS)]
                if window.shape[0] < int(segment_interval * thisFS):
                    incomplete_flag = True
                    break
                if np.max(np.abs(window)) > 500e-6:
                    noise_flag = True
                    break
                one_window.append(window)

            if not (incomplete_flag or noise_flag) and one_window:
                seg.append(np.stack(one_window))

        segments[label_index].append(seg)

    return segments


def slice_signals_into_multiclass_segments(
    signals: np.ndarray,
    thisFS: int,
    labels: List[Tuple[int, int, str]],
    segment_interval: float,
    seizure_types: List[str],
    seizure_overlapping_ratio: List[float]
) -> List[List[np.ndarray]]:
    segments: List[List[np.ndarray]] = [[] for _ in seizure_types]

    for this_label in labels:
        this_label: Tuple[int, int, str]
        start, end, label = this_label
        label: str
        if label not in seizure_types:
            print("Seizure type not included:", label)
            continue
        label_index: int = seizure_types.index(label)
        seg: List[np.ndarray] = []
        step: int = int(segment_interval * (1 - seizure_overlapping_ratio[label_index]) * thisFS)

        for i in range(start * thisFS, end * thisFS, step):
            i: int
            if i + segment_interval * thisFS > end * thisFS:
                break
            one_window: List[np.ndarray] = []
            noise_flag: bool = False
            incomplete_flag: bool = False

            for chan in signals:
                chan: np.ndarray
                window: np.ndarray = chan[i : i + int(segment_interval * thisFS)]
                if window.shape[0] < int(segment_interval * thisFS):
                    incomplete_flag = True
                    break
                if np.max(np.abs(window)) > 500e-6:
                    noise_flag = True
                    break
                one_window.append(window)

            if not (incomplete_flag or noise_flag) and one_window:
                seg.append(np.stack(one_window))

        segments[label_index].append(seg)

    return segments


def plot_signal_in_frequency(
    signal: np.ndarray,
    filtered_signal: np.ndarray,
    sample_rate: float
) -> None:
    signal: np.ndarray
    filtered_signal: np.ndarray
    sample_rate: float

    fft_orig: np.ndarray = rfft(signal)
    fft_filtered: np.ndarray = rfft(filtered_signal)
    freqs: np.ndarray = rfftfreq(signal.shape[0], 1 / sample_rate)

    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.plot(freqs, np.abs(fft_orig))
    plt.title("Original Signal")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")

    plt.subplot(1, 2, 2)
    plt.plot(freqs, np.abs(fft_filtered))
    plt.title("Filtered Signal")
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")

    plt.tight_layout()
    plt.show()


def make_a_filtered_plot_for_comparison(
    signals: np.ndarray,
    filtered_signals: Union[np.ndarray, List[np.ndarray]],
    thisFS: int
) -> None:
    signals: np.ndarray
    filtered_signals: Union[np.ndarray, List[np.ndarray]]
    thisFS: int

    plt.figure()
    plt.clf()
    maximum_samples: int = 200
    channel_index: int = 5
    if maximum_samples == -1:
        t: np.ndarray = np.linspace(0, signals.shape[1] / thisFS, signals.shape[1])
        plt.plot(t, signals[channel_index, :], label="Noisy signal")
        plt.plot(t, filtered_signals[channel_index], label="Filtered signal")
    else:
        t: np.ndarray = np.linspace(0, maximum_samples / thisFS, maximum_samples)
        plt.plot(t, signals[channel_index, :maximum_samples], label="Noisy signal")
        plt.plot(t, filtered_signals[channel_index][:maximum_samples], label="Filtered signal")

    plt.grid(True)
    plt.axis("tight")
    plt.legend(loc="upper left")
    plt.savefig("filtered_signal_plot.png")


def resample_data_in_each_channel(
    signals: List[np.ndarray],
    thisFS: int,
    resampleFS: int
) -> List[np.ndarray]:
    signals: List[np.ndarray]
    thisFS: int
    resampleFS: int

    sigResampled: List[np.ndarray] = []
    for sig in signals:
        sig: np.ndarray
        length: int = sig.shape[0] if isinstance(sig, np.ndarray) else len(sig)
        num: int = int(length / thisFS * resampleFS)
        y: np.ndarray = resample(sig, num)
        sigResampled.append(y)

    return sigResampled
