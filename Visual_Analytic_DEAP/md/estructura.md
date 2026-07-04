backend/scripts/husformer/
├── __init__.py
├── config.py                    # Constantes: qué canales van en cada modalidad, tamaño de ventana,
│                                 # qué participantes van a train/val/test, rutas de entrada/salida.
├── windowing.py                 # Paso 1: ventanea la señal de un trial completo (44,7680) → N ventanas (44,128).
├── channel_modalities.py        # Paso 2: separa una ventana (44,128) en las 5 modalidades según config.py.
├── labeling.py                  # Paso 3: convierte valencia continua → etiqueta discreta de 3 clases.
├── participant_split.py         # Paso 4: decide a qué split (train/valid/test) pertenece cada participante.
├── manifest.py                  # Paso 7: arma y guarda el CSV de trazabilidad (ventana → contexto original).
├── dataset_builder.py           # Pasos 0+5+6: orquesta carga de todos los .npz, arma el diccionario final
│                                 # con las 5 modalidades + label + id, y lo guarda como Husformer.pkl.
└── build_husformer_dataset.py   # ORQUESTADOR ejecutable — se corre con:
                                  #   python -m backend.scripts.husformer.build_husformer_dataset