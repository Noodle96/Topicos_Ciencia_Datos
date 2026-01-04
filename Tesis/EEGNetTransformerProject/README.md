# EEGNetTransformerProject (Baseline)

## 1. Introducción

Este proyecto implementa un **baseline** para la detección automática de crisis
epilépticas a partir de señales EEG multicanal, utilizando una arquitectura
híbrida basada en **EEGNet + Transformer**.

El objetivo principal de este baseline es establecer un punto de referencia sólido,
reproducible y bien controlado que permita una comparación justa con un enfoque
posterior basado en **aprendizaje adversarial**, orientado a mejorar la
generalización inter-paciente.

---

## 2. Objetivo del Proyecto

El objetivo del proyecto es entrenar y evaluar un clasificador binario capaz de
detectar eventos de crisis epilépticas en señales EEG:

- **bckg**: actividad de fondo
- **seizure**: evento de crisis epiléptica

Este baseline permitirá:

- Establecer métricas de referencia
- Analizar errores de clasificación
- Evaluar el impacto de la variabilidad inter-paciente
- Comparar directamente con un modelo adversarial en etapas posteriores

---

## 3. Dataset

Se utiliza el **TUH EEG Seizure Corpus (TUSZ) v2.0.3**.

Los datos han sido **preprocesados previamente** y almacenados como ventanas EEG
individuales en formato `.npy`. El preprocesamiento es compartido tanto por el
baseline como por el enfoque adversarial.

---

## 4. Preprocesamiento de Datos

El preprocesamiento se realiza **fuera de este proyecto**, en un pipeline
independiente ubicado en la raíz de la tesis. Este pipeline genera los datos que
consume directamente este proyecto.

### Características del preprocesamiento

- Ventanas EEG de **4 segundos**
- Frecuencia de muestreo: **250 Hz**
- **22 canales EEG**
- Clasificación binaria (`bckg` / `seizure`)
- Selección controlada de pacientes para limitar el uso de memoria
- Conversión explícita a `float32` para reducir el consumo de RAM
- Almacenamiento en archivos `.npy` por paciente/sesión

Este desacoplamiento garantiza:

- Reproducibilidad
- Ausencia de *data leakage*
- Comparaciones justas entre modelos

---

## 5. Estructura de los Datos Preprocesados

```text
data_procesada/
└── TUSZ_processed_binary_individual_segments/
    └── segment_interval_4_sec/
        ├── train/
        │   ├── bckg/
        │   └── seizure/
        ├── val/
        │   ├── bckg/
        │   └── seizure/
        └── test/
            ├── bckg/
            └── seizure/
```

Cada archivo `.npy` contiene múltiples ventanas EEG con forma:

```text
(N, 22, 1000)
```

## 6. Estructura del Proyecto

```bash
EEGNetTransformerProject/
├── config/
│   ├── settings.py
│   └── train_config.py
├── data/
│   └── dataloader.py
├── models/
│   ├── eegnet.py
│   ├── positional_encoding.py
│   └── eegnet_transformer.py
├── training/
│   ├── trainer.py
│   └── early_stopping.py
├── evaluation/
│   ├── metrics.py
│   └── plots.py
├── notebooks/
│   └── baseline_analysis.ipynb
├── results/
│   ├── baseline/
│       ├── loss_data/
│       ├── metrics/
│       └── model/
│           └── EEGTransformerNet.pth
│   ├── test_metrics/
├── train.py
└── evaluate.py
```
Descripción de carpetas

- config/: configuración global y de entrenamiento
- data/: datasets y dataloaders
- models/: arquitectura EEGNet + Transformer
- training/: lógica de entrenamiento y validación
- evaluation/: métricas y utilidades de evaluación
- notebooks/: análisis y visualización de resultados
- results/: modelos entrenados y métricas guardadas

---

## 7. Modelo Baseline

El modelo implementa una arquitectura híbrida:

1. **EEGNet**

    - Extrae características espaciales y temporales locales

2. **Transformer Encoder**

    - Modela dependencias temporales de largo alcance

La salida del modelo es una predicción binaria:

- `0`: bckg
- `1`: seizure

**Configuración principal**

- Canales EEG: **22**
- Longitud de secuencia: **1000**
- Cabezas de atención: **2**
- Capas Transformer: **1**
- Dimensión feedforward reducida para GPU de **6GB VRAM**

---

## 8. Entrenamiento

El entrenamiento se realiza exclusivamente con los conjuntos:
- train
- val

Características:

- Optimizador: **Adam**
- Función de pérdida: **CrossEntropyLoss**
- Batch size ajustado a la VRAM disponible
- Registro de pérdidas por época
- Guardado del modelo entrenado

> ⚠️ El conjunto test no se carga en memoria durante el entrenamiento para evitar fuga de información y problemas de uso de RAM

---

## 9. Evaluación

La evaluación se realiza en dos etapas claramente separadas:
- Validación (val) durante el entrenamiento
- Evaluación final (test) una vez finalizado el entrenamiento

Se calculan y almacenan:
- Matriz de confusión
- Precision, Recall y F1-score
- Classification report
- Predicciones y etiquetas reales

> Los resultados se guardan en disco y se analizan posteriormente en notebooks.

--- 



## 10. Instalación y Ejecución

Esta sección describe cómo configurar el entorno y ejecutar el entrenamiento y la evaluación del modelo baseline.

### 10.1 Creación del entorno virtual

Se recomienda utilizar un entorno virtual para aislar las dependencias del
proyecto.

```bash
python3 -m venv eeg-environment
source eeg-environment/bin/activate
```

### 10.2 Instalación de dependencias

Una vez activado el entorno virtual, instalar todas las dependencias necesarias:
```bash
pip install -r requirements.txt
```

Este proyecto fue desarrollado y probado usando **CUDA 11.8**.  
Por lo tanto, PyTorch debe instalarse manualmente con las versiones compatibles:

```bash
pip install torch==2.7.1+cu118 \
            torchvision==0.22.1+cu118 \
            torchaudio==2.7.1+cu118 \
            --index-url https://download.pytorch.org/whl/cu118
```

## 10.3 Entrenamiento del modelo baseline

Para entrenar el modelo EEGNet + Transformer usando los datos preprocesados:

```bash
python train.py
```

Durante el entrenamiento se guardan automáticamente:
- Pérdidas de entrenamiento y validación
- Modelo entrenado (`.pth`)
- Métricas finales sobre el conjunto de validación
- Los resultados se almacenan en la carpeta `results/`.

### 10.4 Evaluación sobre el conjunto TEST

Una vez finalizado el entrenamiento, la evaluación sobre el conjunto de test (separado completamente del entrenamiento) se realiza con:
```bash
python evaluate.py
```

Este paso:
- Carga el modelo entrenado
- Evalúa únicamente sobre el conjunto **TEST**
- Guarda métricas y resultados para análisis posterior en notebooks

### 10.5 Análisis de resultados

El análisis detallado de:
- Curvas de pérdida
- Matrices de confusión
- Métricas de clasificación

se realiza mediante notebooks ubicados en la carpeta:

```bash
notebooks/
```

## 11. Resultados y Análisis

Los resultados se almacenan de forma reproducible:
- `results/baseline/losses/train_losses.npy`
- `results/baseline/losses/val_losses.npy`
- `results/baseline/metrics/val_classification_report.txt`
- `results/baseline/metrics/val_confusion.npy`
- `results/baseline/metrics/val_y_pred.npy`
- `results/baseline/metrics/val_y_true.npy`
- `results/baseline/model/EEGTransformerNet.pth`

> El análisis visual y estadístico se realiza en notebooks dedicados.

---

## 12. Reproducibilidad

Este proyecto garantiza reproducibilidad mediante:
- Separación estricta de **train / val / test**
- Preprocesamiento fijo y compartido
- Configuración centralizada
- Guardado explícito de modelos y métricas

---

## 13. Próximos Pasos

Este baseline servirá como punto de comparación para un segundo proyecto basado
en **aprendizaje adversarial (DANN)**, cuyo objetivo es:
- Aprender representaciones invariantes al paciente
- Reducir el sobreajuste inter-paciente
- Mejorar la generalización a sujetos no vistos
