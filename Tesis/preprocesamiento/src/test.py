# src/test.py
# Desde preprocesamiento folder:
#       python -m src.test
from src.patient_selection import PatientSummary, extract_patient_and_reference_from_path

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
    path = "/home/russell/ssd/code/Topicos_Ciencia_Datos/Tesis/dataset/tuh_eeg_seizure/v2.0.3/ef/dev/aaaaalhp/s004_2013/01_tcp_ar/aaaaalhp_s004_t005.edf"
    patient_id, reference_type = extract_patient_and_reference_from_path(path)
    print(f"\tpatient_id: {patient_id}")
    print(f"\treference_type: {reference_type}")
    print("end test2")
if __name__ == "__main__":
    main()
