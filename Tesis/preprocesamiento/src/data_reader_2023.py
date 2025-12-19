from typing import List, Tuple, Dict, Union, Any
import os

import mne
import numpy as np
from scipy.signal import butter, filtfilt, resample, iirnotch, lfilter
from scipy.fft import rfft, rfftfreq
import matplotlib.pyplot as plt
import pyedflib
import csv


def get_all_TUSZ_2023_session_paths(
    rootPath: str,
) -> Tuple[List[str], List[str], Dict[str, int]]:
    """
    Recorre la carpeta raíz 'rootPath' y devuelve información de sesiones.

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
                # if reference_type != "01_tcp_ar":
                #     continue
                reference_type_count[reference_type] = (
                    reference_type_count.get(reference_type, 0) + 1
                )

                ref_dir: str = os.path.join(session_dir, reference_type)
                files: List[str] = os.listdir(ref_dir)

                for file in files:
                    file: str
                    if file.endswith(".edf"):
                        full_path: str = os.path.join(ref_dir, file)
                        session_paths.append(full_path)

    return session_paths, all_patients, reference_type_count


def get_channels_from_raw(
    raw: mne.io.BaseRaw,
) -> Tuple[bool, Union[int, np.ndarray]]:
    """
    Extrae la diferencia de dos montajes de canales EEG de una señal cruda.

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
    montage_list_1 = [
        "EEG FP1-REF",
        "EEG F7-REF",
        "EEG T3-REF",
        "EEG T5-REF",
        "EEG FP2-REF",
        "EEG F8-REF",
        "EEG T4-REF",
        "EEG T6-REF",
        "EEG A1-REF",
        "EEG T3-REF",
        "EEG C3-REF",
        "EEG CZ-REF",
        "EEG C4-REF",
        "EEG T4-REF",
        "EEG FP1-REF",
        "EEG F3-REF",
        "EEG C3-REF",
        "EEG P3-REF",
        "EEG FP2-REF",
        "EEG F4-REF",
        "EEG C4-REF",
        "EEG P4-REF",
    ]

    montage_list_2 = [
        "EEG F7-REF",
        "EEG T3-REF",
        "EEG T5-REF",
        "EEG O1-REF",
        "EEG F8-REF",
        "EEG T4-REF",
        "EEG T6-REF",
        "EEG O2-REF",
        "EEG T3-REF",
        "EEG C3-REF",
        "EEG CZ-REF",
        "EEG C4-REF",
        "EEG T4-REF",
        "EEG A2-REF",
        "EEG F3-REF",
        "EEG C3-REF",
        "EEG P3-REF",
        "EEG O1-REF",
        "EEG F4-REF",
        "EEG C4-REF",
        "EEG P4-REF",
        "EEG O2-REF",
    ]

    # montage_list_1: List[str] = [
    #     "EEG FP1-REF", "EEG F7-REF", "EEG T3-REF", "EEG T5-REF",
    #     "EEG FP2-REF", "EEG F8-REF", "EEG T4-REF", "EEG T6-REF",
    #     "EEG T3-REF", "EEG C3-REF", "EEG CZ-REF", "EEG C4-REF",
    #     "EEG FP1-REF", "EEG F3-REF", "EEG C3-REF", "EEG P3-REF",
    #     "EEG FP2-REF", "EEG F4-REF", "EEG C4-REF", "EEG P4-REF",
    # ]
    #
    # montage_list_2: List[str] = [
    #     "EEG F7-REF", "EEG T3-REF", "EEG T5-REF", "EEG O1-REF",
    #     "EEG F8-REF", "EEG T4-REF", "EEG T6-REF", "EEG O2-REF",
    #     "EEG C3-REF", "EEG CZ-REF", "EEG C4-REF", "EEG T4-REF",
    #     "EEG F3-REF", "EEG C3-REF", "EEG P3-REF", "EEG O1-REF",
    #     "EEG F4-REF", "EEG C4-REF", "EEG P4-REF", "EEG O2-REF",
    # ]

    # chan_names = raw.ch_names
    # print(f"Nombres de canal : {len(chan_names)} canales")
    # for idx, name in enumerate(chan_names):
    #     print(f" {idx:3d}: {name}")

    montage_indices_1: List[int] = [raw.ch_names.index(ch) for ch in montage_list_1]
    montage_indices_2: List[int] = [raw.ch_names.index(ch) for ch in montage_list_2]

    # print("montage_indices_1:", montage_indices_1)
    # print("montage_indices_2:", montage_indices_2)

    # print("info basica")
    # n_channels = raw.info["nchan"]
    # sfreq = raw.info["sfreq"]
    # duration_s = raw.n_times / sfreq
    # print(f"Frecuencia muestreo: {sfreq:.1f} Hz")
    # print("raw.n_times: ", raw.n_times)
    # print(f"Duración : {duration_s:.1f} s")

    try:
        signals_1: np.ndarray = raw.get_data(picks=montage_indices_1)
        # print("signals_1 shape:", signals_1.shape)
        # signals_1 shape: (20, 362250)
        signals_2: np.ndarray = raw.get_data(picks=montage_indices_2)
    except Exception:
        print(
            "[Exception] Something is wrong when reading channels of the raw EEG signal"
        )
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
    order: int = 3,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calcula los coeficientes del filtro pasa banda de Butterworth.

    Este filtro atenúa las frecuencias fuera del rango [lowcut, highcut] y preserva
    las componentes dentro de ese rango.

    Args:
        lowcut (float): Frecuencia de corte inferior (Hz).
        highcut (float): Frecuencia de corte superior (Hz).
        fs (float): Frecuencia de muestreo de la señal (Hz).
        order (int, opcional): Orden del filtro. Por defecto es 3.

    Returns:
        Tuple[np.ndarray, np.ndarray]: Coeficientes del filtro (b, a) que pueden
        ser usados por funciones como filtfilt para aplicar el filtro.
    """
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
    order: int = 3,
) -> np.ndarray:
    """
    Aplica un filtro pasa banda de Butterworth a una señal EEG.

    Utiliza los coeficientes generados por la función butter_bandpass y filtra
    la señal para retener solamente las frecuencias en el rango [lowcut, highcut].

    Args:
        data (np.ndarray): Señal de entrada que será filtrada.
        lowcut (float): Frecuencia de corte inferior (Hz).
        highcut (float): Frecuencia de corte superior (Hz).
        fs (float): Frecuencia de muestreo de la señal (Hz).
        order (int, opcional): Orden del filtro. Por defecto es 3.

    Returns:
        np.ndarray: Señal filtrada con el filtro pasa banda aplicado.
    """
    b: np.ndarray
    a: np.ndarray
    b, a = butter_bandpass(lowcut, highcut, fs, order=order)
    y: np.ndarray = filtfilt(b, a, data)
    return y


def slice_signals_into_binary_segments(
    signals: List[np.ndarray],  # Matriz (n_canales, n_muestras)
    thisFS: int,  # Frecuencia de muestreo (Hz) => 250 Hz
    labels: List[
        Tuple[int, int, str]
    ],  # Intervalos con clase: [(inicio, fin, etiqueta)]
    segment_interval: float,  # Duración del segmento en segundos => ej. 4.0 seg
    seizure_types: List[str],  # ['bckg', 'seizure']
    seizure_overlapping_ratio: List[float],  # [0.0, 0.75]
) -> List[List[List[np.ndarray]]]:
    """
    Segmenta señales EEG en ventanas fijas y las clasifica como
    fondo ("bckg") o crisis ("seizure").

    Esta función recorre los intervalos anotados (por ejemplo, de tipo 'bckg'
    o 'seizure') y divide cada intervalo en múltiples ventanas deslizantes
    (sliding windows) de longitud fija. Aplica verificación de ruido y longitud,
    y organiza los segmentos válidos según su tipo.

    La estructura del retorno es jerárquica de 3 niveles:

        segments: List[List[List[np.ndarray]]]
        ├── Nivel 1: una lista por clase (por ejemplo: ['bckg', 'seizure'])
        │
        ├── Nivel 2: para cada clase, una lista por intervalo anotado en el archivo
        │
        └── Nivel 3: para cada intervalo, una lista de ventanas válidas
            (una por segmento temporal)

    Cada ventana es un np.ndarray de forma (n_canales, n_muestras_segmento)

    Args:
        signals (np.ndarray): Señales EEG con forma (n_canales, n_muestras).
        thisFS (int): Frecuencia de muestreo de las señales (Hz).
        labels (List[Tuple[int, int, str]]): Lista de etiquetas con intervalos
            en segundos y clase asociada.
            Ejemplo: [(12, 25, 'bckg'), (25, 40, 'seizure')].
        segment_interval (float): Duración de cada ventana en segundos
            (ej. 4.0).
        seizure_types (List[str]): Lista de clases binarias.
            Usualmente: ['bckg', 'seizure'].
        seizure_overlapping_ratio (List[float]): Lista con el grado de
            solapamiento (entre 0 y 1) para cada tipo de clase.
            Ejemplo: [0.0, 0.75].

    Returns:
        List[List[List[np.ndarray]]]: Segmentos EEG organizados por
        clase → intervalo → ventanas válidas.
    """
    segments: List[List[List[np.ndarray]]] = [[] for _ in seizure_types]

    # print("[DEBUG] begin all")  # RUSSELL
    for this_label in labels:
        # print("\t[DEBUG] begin this_label:", this_label)  # RUSSELL
        this_label: Tuple[int, int, str]
        start: int
        end: int
        label: str
        start, end, label = this_label

        label_index: int = 0 if label == "bckg" else 1
        seg: List[np.ndarray] = []

        step: int = int(
            segment_interval * (1 - seizure_overlapping_ratio[label_index]) * thisFS
        )
        # step[0] = 4*(1-0) * 250 = 1000
        # step[1] = 4*(1-0.75) * 250 = 250
        # print("\t[DEBUG] step:", step)  # RUSSELL

        for i in range(start * thisFS, end * thisFS, step):
            # print(f"\t\t[DEBUG] step: [{i}, {i + int(segment_interval * thisFS)}]")  # RUSSELL
            i: int
            if i + segment_interval * thisFS > end * thisFS:
                break

            one_window: List[np.ndarray] = []
            # si no esta incompleto o con ruido one_window tendra un len de 22
            # y cada i tendra (1000,) para bckg
            # y (mmm,) para seizure
            noise_flag: bool = False
            incomplete_flag: bool = False

            for chan in signals:
                chan: np.ndarray
                window: np.ndarray = chan[i : i + int(segment_interval * thisFS)]

                # print("window.shape[0]:", window.shape[0])
                if window.shape[0] < int(segment_interval * thisFS):
                    incomplete_flag = True
                    break

                # print("before np.max(np.abs(window)):", np.max(np.abs(window)))
                if np.max(np.abs(window)) > 500e-6:
                    # print("noise detected in window, max value:", np.max(np.abs(window)))
                    noise_flag = True
                    break

                # print("\t\t\t[DEBUG] shape of window:", window.shape)  # RUSSELL
                # [DEBUG] shape of window: (1000,) para bckg
                # [DEBUG] shape of window: (mmm,) para seizure
                one_window.append(window)

            # print("\t\t[DEBUG] shape of one_window:", len(one_window), one_window[0].shape if one_window else None)  # RUSSELL
            # shape of one_window: 22 (1000,) para bckg
            # shape of one_window: 22 (nnnn,) para seizure

            if not (incomplete_flag or noise_flag) and one_window:
                seg.append(np.stack(one_window))
                # print("\t\t[DEBUG] no hubo problema, asi, seg[0].shape", seg[0].shape)  # RUSSELL
                # [DEBUG] no hubo problema, asi, seg[0].shape (22, 1000)

        # print("\t[DEBUG] end for loop for this_label:", this_label)  # RUSSELL
        # print("\t[DEBUG] shape of seg:", len(seg), seg[0].shape if seg else None)  # RUSSELL

        # for e in range(len(seg)):  # RUSSELL
        #     print(f"\t\t[DEBUG] shape of seg[{e}]:", seg[e].shape)  # RUSSELL

        if seg:
            segments[label_index].append(seg)
            # print("\t[DEBUG] after append(seg) len(segments[label_index] ): ", len(segments[label_index]))  # RUSSELL

    # print("[DEBUG] end all")  # RUSSELL
    # print("[DEBUG] shape of segments:", len(segments),
    #       [len(seg) for seg in segments],
    #       [seg[0].shape if seg else None for seg in segments])

    return segments


# 0000000000500,000 => 500
# 0000000,000500000 => 0.0005 => convert a microvoltios => 5e-4
# one example:
# 2.150271918946624e-05
# 000000.00002150271918946624 => 0.00002150271918946624


def slice_signals_into_multiclass_segments(
    signals: np.ndarray,
    thisFS: int,
    labels: List[Tuple[int, int, str]],
    segment_interval: float,
    seizure_types: List[str],
    seizure_overlapping_ratio: List[float],
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

        step: int = int(
            segment_interval * (1 - seizure_overlapping_ratio[label_index]) * thisFS
        )

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
    sample_rate: float,
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
    thisFS: int,
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
        plt.plot(
            t,
            signals[channel_index, :maximum_samples],
            label="Noisy signal",
        )
        plt.plot(
            t,
            filtered_signals[channel_index][:maximum_samples],
            label="Filtered signal",
        )

    plt.grid(True)
    plt.axis("tight")
    plt.legend(loc="upper left")
    plt.savefig("filtered_signal_plot.png")


def resample_data_in_each_channel(
    signals: List[np.ndarray],
    thisFS: int,
    resampleFS: int,
) -> List[np.ndarray]:
    """
    Remuestrea cada señal de canal EEG a una nueva frecuencia deseada.

    Esta función toma una lista de señales (una por canal), y aplica resampling
    individualmente a cada una, adaptando su número de muestras según la nueva
    frecuencia de muestreo.

    Args:
        signals (List[np.ndarray]): Lista de señales (una por canal),
            cada una como array 1D.
        thisFS (int): Frecuencia de muestreo original (Hz).
        resampleFS (int): Nueva frecuencia de muestreo deseada (Hz).

    Returns:
        List[np.ndarray]: Lista de señales remuestreadas, en el mismo orden
        que la entrada.
    """
    sigResampled: List[np.ndarray] = []

    for sig in signals:
        sig: np.ndarray
        length: int = sig.shape[0] if isinstance(sig, np.ndarray) else len(sig)
        num: int = int(length / thisFS * resampleFS)
        y: np.ndarray = resample(sig, num)
        sigResampled.append(y)

    return sigResampled


def summarize_raw(raw: mne.io.BaseRaw) -> Dict[str, Any]:
    """
    Muestra información esencial y genera gráficas de una señal EEG en formato
    MNE Raw.

    Args:
        raw (mne.io.BaseRaw): Objeto Raw con la señal EEG ya precargada en RAM.

    Returns:
        Dict[str, Any]: Diccionario con métricas y estadísticas básicas.
    """
    # 1. Información general
    n_channels = raw.info["nchan"]
    sfreq = raw.info["sfreq"]
    duration_s = raw.n_times / sfreq
    chan_types = raw.get_channel_types()
    chan_names = raw.ch_names

    print(f"Número de canales : {n_channels}")
    print(f"Frecuencia muestreo: {sfreq:.1f} Hz")
    print(f"Duración : {duration_s:.1f} s")
    print(f"Tipos de canal : {np.unique(chan_types)}")
    # print(f"Nombres de canal : {chan_names[:10]}{' …' if len(chan_names)>10 else ''}")

    # mostrar todos los canales en lineas diferentes enumerados
    print(f"Nombres de canal : {len(chan_names)} canales")
    for idx, name in enumerate(chan_names):
        print(f" {idx + 1:3d}: {name}")

    # 2. Estadísticas básicas por canal
    data = raw.get_data()  # (n_channels, n_times)
    means = np.mean(data, axis=1)
    stds = np.std(data, axis=1)

    print("\nEstadísticas (primeros 5 canales):")
    for idx in range(min(5, n_channels)):
        print(
            f" {chan_names[idx]:<10} – µ={means[idx]:.9f}, σ={stds[idx]:.9f}",
        )

    # 3. Gráfica: fragmento de señal (primeros 5 s y 5 canales)
    t_ms = np.arange(data.shape[1]) / sfreq
    fig, ax = plt.subplots(figsize=(10, 4))

    for idx in range(min(5, n_channels)):
        ax.plot(
            t_ms[: int(5 * sfreq)],
            data[idx, : int(5 * sfreq)] + idx * stds[idx] * 5,
            label=chan_names[idx],
        )

    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Amplitud (offset por canal)")
    ax.set_title("Primeros 5 s de los primeros 5 canales")
    ax.legend(loc="upper right", fontsize="small")
    plt.tight_layout()
    plt.show()

    # 4. Gráfica: PSD promedio
    fig2, ax2 = plt.subplots(figsize=(8, 4))
    raw.plot_psd(average=True, fmin=0.5, fmax=40.0, ax=ax2, show=True)
    ax2.set_title("Densidad espectral de potencia (0.5–40 Hz)")
    plt.tight_layout()
    plt.show()

    # 5. Devolver resumen
    summary: Dict[str, Any] = {
        "n_channels": n_channels,
        "sfreq": sfreq,
        "duration_s": duration_s,
        "channel_types": chan_types,
        "channel_names": chan_names,
        "means": means,
        "stds": stds,
    }
    return summary


def sumaAlCuadrado(a: int, b: int) -> int:
    """
    Suma dos números enteros.

    Args:
        a (int): Primer número.
        b (int): Segundo número.

    Returns:
        int: La suma de a y b.
    """
    return a + b


def cubo(a: int) -> int:
    """
    Calcula el cubo de un número entero.

    Args:
        a (int): Número a elevar al cubo.

    Returns:
        int: El cubo de a.
    """
    return a**3 + 1


def get_channel_frequencies_from_edf(edf_path: str) -> List[Tuple[str, float]]:
    """
    Extrae la frecuencia de muestreo de cada canal individual en un archivo EDF.

    Esta función es útil cuando se desea inspeccionar si los canales tienen
    diferentes frecuencias de muestreo (algo que MNE no expone directamente).

    Args:
        edf_path (str): Ruta al archivo .edf a inspeccionar.

    Returns:
        List[Tuple[str, float]]: Lista de tuplas con el nombre del canal y
        su frecuencia de muestreo.
    """
    f = pyedflib.EdfReader(edf_path)
    num_channels: int = f.signals_in_file
    channel_freqs: List[Tuple[str, float]] = []

    for i in range(num_channels):
        label: str = f.getLabel(i)
        freq: float = f.getSampleFrequency(i)
        channel_freqs.append((label, freq))

    f.close()
    return channel_freqs


def get_labels_complete_from_csv_bi_clasificacion_binaria(
    data_path: str,
) -> List[Tuple[int, int, str]]:
    """
    Lee un archivo .csv_bi y devuelve una lista completa de intervalos
    (inicio, fin, clase) en segundos enteros, cubriendo toda la señal
    con 'seizure' y 'bckg', sin huecos.

    Args:
        data_path (str): Ruta al archivo .csv_bi

    Returns:
        List[Tuple[int, int, str]]: Intervalos completos (start, stop, label)
    """
    raw_intervals: List[Tuple[int, int, str]] = []
    duration_sec: int = -1

    label_csv: str = data_path[:-4] + ".csv_bi"

    # print("data_path:", data_path)
    # print("label_csv:", label_csv)

    with open(label_csv, "r") as f:
        header_lines = []
        content_lines = []

        for line in f:
            if line.startswith("#"):
                header_lines.append(line.strip())
            else:
                content_lines.append(line)

    # print("Header lines:", header_lines)
    # print("Content lines:", content_lines)

    # Extraer duración
    for line in header_lines:
        if line.lower().startswith("# duration"):
            parts = line.split("=")
            duration_sec = int(float(parts[1].strip().split()[0]))
            # print("\tparts:", parts)
            # print("\tduration_sec:", duration_sec)
            break

    if duration_sec == -1:
        raise ValueError("Duración no encontrada en el encabezado del archivo.")

    # Leer intervalos (solo seiz y bckg)
    reader = csv.DictReader(content_lines)
    # print("data_path", data_path)
    for row in reader:
        # print("\trow:", row)
        label = row["label"].lower()
        if label not in {"seiz", "seizure", "bckg", "background"}:
            continue

        start = int(float(row["start_time"]))
        end = int(float(row["stop_time"]))

        if end > start:
            norm_label = "seiz" if label in {"seiz", "seizure"} else "bckg"
            raw_intervals.append((start, end, norm_label))

    # Ordenar por inicio
    raw_intervals.sort()

    # Completar huecos
    labels: List[Tuple[int, int, str]] = []
    t_start = 0

    for start, end, label in raw_intervals:
        if t_start < start:
            labels.append((t_start, start, "bckg"))

        labels.append((start, end, label))
        t_start = max(t_start, end)

    if t_start < duration_sec:
        labels.append((t_start, duration_sec, "bckg"))

    return labels
