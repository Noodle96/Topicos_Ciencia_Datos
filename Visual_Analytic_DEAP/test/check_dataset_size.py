n_participantes = 32
n_trials = 40
ventanas_por_trial = 60          # ventanas de 1s a 128Hz
bytes_por_muestra = 4            # float32

canales_por_modalidad = {
    "EEG": 32,
    "EOG": 4,
    "EMG": 4,
    "GSR": 1,
    "Resp+Plet+Temp": 3,
}

n_ventanas = n_participantes * n_trials * ventanas_por_trial
bytes_por_ventana = sum(canales_por_modalidad.values()) * 128 * bytes_por_muestra
total_bytes = n_ventanas * bytes_por_ventana

print(f"Ventanas totales: {n_ventanas:,}")
print(f"Bytes por ventana (todas las modalidades): {bytes_por_ventana:,}")
print(f"Tamaño total estimado: {total_bytes / 1e9:.3f} GB")