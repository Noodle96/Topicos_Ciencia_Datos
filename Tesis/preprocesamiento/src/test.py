# src/test.py
# Desde preprocesamiento folder:
#       python -m src.test
import numpy as np

from src.patient_selection import PatientSummary, extract_patient_and_reference_from_path

from src.preprocess_pipeline import (
    PreprocessParams,
    extract_patient_session_id,
    extract_reference_type_from_path,
    ensure_output_dirs,
    bandpass_and_notch_filter,
    save_segments_append,
    process_one_edf,
    run_preprocessing_for_split
)

def main() -> None:
    print("begin test1")
    patient = PatientSummary(
        patient_id="aaaaaauj",
        seizure_seconds=360,
        edf_count=3,
        edf_paths=[
            "/data/edf/01.edf",
            "/data/edf/02.edf",
            "/data/edf/03.edf",
        ]
    )
    print(f"\t{patient}")
    print("end test1\n\n")

    print("begin test2")
    # path = "/home/russell/ssd/code/Topicos_Ciencia_Datos/Tesis/dataset/tuh_eeg_seizure/v2.0.3/edf/train/aaaaaaav/s001_2006/02_tcp_le/aaaaaaav_s001_t000.edf"
    path = "/home/russell/ssd/code/Topicos_Ciencia_Datos/Tesis/dataset/tuh_eeg_seizure/v2.0.3/edf/dev/aaaaalhp/s004_2013/01_tcp_ar/aaaaalhp_s004_t005.edf"
    patient_id, reference_type = extract_patient_and_reference_from_path(path)
    print(f"\tpatient_id: {patient_id}")
    print(f"\treference_type: {reference_type}")
    print("end test2")


def test_preprocess_pipeline() -> None:

    params: PreprocessParams = PreprocessParams(
        lowcut=0.5,
        highcut=50.0,
        fs=256,
        resampleFS=128,
        segment_interval=30,
        seizure_types=["focal", "generalized"],
        seizure_overlapping_ratio=[0.5, 0.5],
        skip_reference_types={"reference1", "reference2"}
    )

    print("[TEST] print testX")
    print("[TEST] end testX\n\n")

    print("[TEST] print test1")
    print(f"\tparams: {params}")
    print("[TEST] end test1\n\n")

    print("[TEST] print test2")
    path = "/home/russell/ssd/code/Topicos_Ciencia_Datos/Tesis/dataset/tuh_eeg_seizure/v2.0.3/edf/dev/aaaaalhp/s004_2013/01_tcp_ar/aaaaalhp_s004_t005.edf"
    referenceTest: str = extract_reference_type_from_path(path)
    session_id: str = extract_patient_session_id(path)
    # patient_session: str = path.split("dev/")[1].split("/")[-1][:-4]
    # print("\tpatient_session:", patient_session) # patient_session: aaaaалhp_s004_t005

    print(f"\treference_type: {referenceTest}") # reference_type: 01_tcp_ar
    print(f"\tsession_id: {session_id}") # session_id: aaaaалhp_s004_t005
    print("[TEST] end test2\n\n")

    print("[TEST] print test3")
    print("[TEST] end test3\n\n")
    

if __name__ == "__main__":
    # main()
    test_preprocess_pipeline()
