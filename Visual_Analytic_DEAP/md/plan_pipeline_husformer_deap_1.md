# Plan: de los .bdf crudos de DEAP al entrenamiento de Husformer

## Veredicto rápido de factibilidad

Tu máquina (Intel UHD 630 integrada + **NVIDIA GTX 1660 Ti Mobile, 6GB GDDR6, Turing, compute capability 7.5**) es más que suficiente. Husformer, tal como está implementado en el repo (`d_m = 30`, embeddings pequeños, 3-5 capas de transformer), es un modelo **chico**: nada que ver con un LLM ni con un transformer de visión. Con tu GPU esto entrena en minutos u horas, no en días. El cuello de botella de este proyecto no es cómputo, es **ingeniería de datos**: adaptar tu pipeline actual al formato exacto que Husformer espera. Ese es el foco real de este plan.

**Confirmado (2026-07-04):** 15GB RAM total, 7.5GB disponibles en este momento — de sobra para un dataset de ~1.7GB. `PyTorch` todavía no está instalado en `env_va_deap` (ver checklist, sección 7).

---

## 1. Estado actual (ya construido y funcionando)

Revisé tu código en `backend/` y `Husformer/`. Esto es lo que ya tienes:

**Etapa A — De `.bdf` crudo a señal limpia por trial** (`backend/scripts/preprocess_trials.py` y `preprocess_representation_inputs.py`, ambos funcionando):
- Lee los 32 archivos `.bdf` originales (512 Hz).
- Detecta automáticamente el canal Status y reconstruye los 120 eventos (3→4→5) por participante, con manejo especial para S28 (reconstrucción vía `participant_ratings.xls` cuando el canal Status falla).
- Selecciona 44 canales: 32 EEG (orden Geneva 10-20) + 4 EOG (EXG1-4) + 4 EMG (EXG5-8) + 4 autonómicas (GSR1, Resp, Plet, Temp).
- Aplica ICA para remover artefactos oculares (EOG → EEG) — esto ya es más riguroso que el pipeline de demostración del propio repo Husformer, que no hace ICA.
- Filtra EEG en banda 4-45 Hz.
- Remuestrea todo a 128 Hz.
- Extrae la fase "During" (60s de estímulo) por trial.
- Guarda `dataset/processed/representation_inputs/sXX/trial_XX_input.npz` con `signals (44, 7680)`, `times`, `channels`, más metadata (valencia, activación, dominancia, liking).

**Etapa B — Features manuales (para baseline/visualización, no para Husformer)** (`backend/scripts/representations/*.py`, funcionando):
- `eeg_features.py`, `physiological_features.py`: extraen features tipo DEAP clásico (log-power por banda vía Welch, etc.).
- `generate_manual_deap_features.py` + `normalize_manual_deap_features.py`: arman y normalizan `X_features_standardized.npy`.
- `generate_latent_projections.py`: proyecta esos features (no las representaciones de Husformer) a 2D con PCA/UMAP/t-SNE.

Importante: **la Etapa B es un baseline con features hechos a mano, no las representaciones aprendidas por Husformer.** Tu "Vista de Espacio Latente" del paper necesita las representaciones que salen del modelo (`last_hs`), no esto. Esto confirma que el hueco real está exactamente donde intuías.

**Etapa C — Repositorio Husformer clonado** (`Husformer/`, sin adaptar todavía):
- Arquitectura completa disponible (`modules/transformer.py`, `modules/multihead_attention.py`).
- 3 variantes de modelo según número de modalidades: `src/3`, `src/4`, `src/5` (+ `main-3.py`, `main-4.py`, `main-5.py`).
- Scripts de conversión de datos originales del paper (`make_data/Pre-DEAP.py`, `Raw-DEAP.py`) — sirven como **referencia del formato esperado**, pero están escritos para el `.mat` oficial de DEAP preprocesado o para exports CSV crudos, no para tus `.npz`. No se pueden usar directamente.

---

## 2. Lo que falta (el hueco real)

No existe todavía ningún script que conecte la Etapa A (tus `.npz` limpios) con Husformer. Falta:

1. **Un script nuevo** que tome `representation_inputs/sXX/trial_XX_input.npz` y genere el `Husformer.pkl` que espera `src/X/dataset.py`.
2. **Entrenar** con `main-X.py` (renombrado a `main.py`, según indica el propio README de Husformer).
3. **Extraer** `last_hs` (representación fusionada) y los pesos de atención cross-modal — esto último requiere modificar el modelo, porque **el repo los descarta actualmente** (ver bug #2 abajo).

---

## 3. Flujo completo paso a paso

```
.bdf crudo (32 archivos, 512 Hz)
        │
        ▼
[YA HECHO] preprocess_trials.py / preprocess_representation_inputs.py
        │   (ICA + filtro 4-45Hz EEG + resample 128Hz + selección 44 canales)
        ▼
representation_inputs/sXX/trial_XX_input.npz   (44 canales × 7680 muestras, 60s)
        │
        ▼
[FALTA — NUEVO SCRIPT] backend/scripts/build_husformer_dataset.py
        │   1. Cargar todos los .npz (32 participantes × 40 trials)
        │   2. Ventanear cada trial en ventanas de 1s (128 muestras),
        │      igual que hace el Husformer original → 60 ventanas/trial
        │   3. Separar canales por modalidad (ver decisión de diseño #1)
        │   4. Generar etiqueta por ventana desde valencia/activación
        │      (ver decisión de diseño #2)
        │   5. Split train/val/test
        │   6. Guardar como Husformer.pkl con claves 'modality_1'..'modality_5'
        ▼
Husformer/data/Husformer.pkl
        │
        ▼
[FALTA — solo mover archivos] mover src/5/*.py → src/, main-5.py → main.py
        ▼
python main.py   (entrenamiento, usa tu GTX 1660 Ti automáticamente si CUDA está bien instalado)
        │
        ▼
[FALTA — modificar modelo] extraer last_hs + pesos de atención (ver bug #2)
        ▼
Representaciones latentes + atención cross-modal → para tus vistas VA
(Vista de Espacio Latente, Vista de Representación Fusionada y Atención Cross-Modal)
```

---

## 4. Decisiones de diseño que tienes que tomar (no las asumo por ti)

**Decisión 1 — Cómo repartir tus 44 canales en modalidades.**
El repo trae variantes para 3, 4 o 5 modalidades. Tus canales ya están agrupados en 4 familias naturales (EEG=32, EOG=4, EMG=4, Autonómicas=4 [GSR1, Resp, Plet, Temp]). Opciones:
- **4 modalidades** (usa `src/4`, `main-4.py`): EEG, EOG, EMG, Autonómicas-juntas. Más simple, y calza con tus 4 grupos naturales.
- **5 modalidades** (usa `src/5`, `main-5.py`): EEG, EOG, EMG, GSR (solo), Resp+Plet+Temp. Separa GSR porque es la señal autonómica más informativa para valencia/activación en la literatura DEAP — podría dar una vista de atención cross-modal más granular para tu paper (justo lo que buscabas al mirar EmoCo/E-ffective).

Mi recomendación: **5 modalidades**, porque tu Sección 5 del paper ("Vista de Representación Fusionada y Atención Cross-Modal") se beneficia de ver GSR como su propia modalidad en el diagrama de atención — es más informativo para el caso de uso de VA. Pero es tu decisión.

**✅ RESUELTO (2026-07-04): 5 modalidades** — EEG (32ch), EOG (4ch), EMG (4ch), GSR (1ch), Resp+Plet+Temp (3ch). Usar `src/5` y `main-5.py`.

**Decisión 2 — Esquema de etiquetas.**
El código original de Husformer para DEAP usa 3 clases desde valencia (bajo 1-3, medio 4-6, alto 7-9). Alternativas:
- Igual que el paper (3 clases, valencia).
- Clasificación binaria alto/bajo con corte en 5 (más común en literatura DEAP).
- Regresión continua sobre valencia y/o activación (cambia `output_dim` y la función de pérdida).

Como tu objetivo es *interpretar representaciones*, no necesariamente maximizar accuracy de clasificación, cualquier esquema razonable funciona — pero debes fijar uno antes de generar el `.pkl`.

**Sobre tu pregunta: ¿solo valencia, o también activación (arousal) y dominancia?**

Aclaración importante: la etiqueta de entrenamiento y las dimensiones que exploras en la visualización **no tienen que ser la misma cosa**. La etiqueta solo se usa para *supervisar* qué aprende el modelo (moldea el espacio latente); pero en tu VA system puedes colorear/filtrar el espacio latente por **cualquier** dimensión de `participant_ratings` (valencia, activación, dominancia, liking) sin necesidad de haber entrenado el modelo para predecir esa dimensión específica — ya la tienes en la metadata de cada trial.

Tu OE1 dice explícitamente "agrupamientos relacionados con las dimensiones afectivas de valencia **y activación**", así que sí necesitas activación en algún lado. Recomendación concreta:

- **Entrenamiento (supervisión):** un solo run con **valencia** como etiqueta (igual que el código original de Husformer/DEAP, 3 clases) — esto es lo más simple y lo que ya está codificado en `focalloss` (el vector alpha de 3 elementos del README asume 3 clases).
- **Opcional, si el tiempo alcanza:** un segundo run entrenando con **activación** como etiqueta en vez de valencia, dejando todo lo demás igual. Esto te da DOS espacios latentes distintos (uno moldeado por valencia, otro por activación) que puedes comparar — es un punto de discusión interesante para tu Sección 8 (Discusión): ¿el modelo organiza la representación distinto según qué dimensión afectiva supervisa?
- **Dominancia y liking:** no entrenes un modelo aparte para estos. Úsalos únicamente como *encoding visual* (color, tamaño de punto, filtro) en la Vista de Espacio Latente y en la Vista de Perfil del Participante — ya están en tu metadata (`get_trial_metadata` ya extrae `dominance` y `liking`), no requieren re-entrenamiento.

**Decisión 3 — Split train/val/test.**
El código original de Husformer para DEAP mezcla TODAS las ventanas de todos los participantes con shuffle aleatorio a nivel de ventana. Riesgo: ventanas consecutivas del mismo trial son casi idénticas y comparten etiqueta → si quedan repartidas entre train/test hay fuga de datos y las métricas quedan infladas.

**✅ RESUELTO (2026-07-04): split por participante.** Ningún participante aparece en más de un split. Propuesta concreta: **26 participantes train / 3 val / 3 test** (de los 32 totales). Esto es más exigente para el modelo que el shuffle plano (evaluación honesta de generalización entre sujetos), pero es lo correcto dado que el objetivo del paper es interpretar representaciones, no maximizar accuracy.

---

## 9. Checklist de entradas/salidas de `build_husformer_dataset.py`

Antes de escribir el script, el contrato paso a paso (qué entra, qué sale, en cada etapa):

**Paso 0 — Carga y validación**
- Entrada: `dataset/processed/representation_inputs/sXX/trial_XX_input.npz` (1280 archivos: 32 participantes × 40 trials), cada uno con `signals (44, 7680)` float64, `channels` (nombres), `sfreq`, `participant_id`, `trial`, `experiment_id`. Metadata afectiva (valencia/activación/dominancia/liking) se re-obtiene de `participant_ratings.xls` igual que hacen los scripts existentes (o del `representation_metadata.csv` global ya generado).
- Salida: lista en memoria de 1280 trials validados (mismo número de canales y muestras en todos; loggear y abortar si alguno no cumple `(44, 7680)`).

**Paso 1 — Ventaneo**
- Entrada: `signals (44, 7680)` por trial.
- Salida: 60 ventanas de `(44, 128)` por trial (1s cada una) → **76,800 ventanas totales**. Cada ventana hereda: `participant_id`, `trial`, `window_index` (0-59), `window_start_sec`, y las 4 etiquetas afectivas del trial padre (todas las ventanas de un mismo trial comparten la misma etiqueta, igual que en el Husformer original).

**Paso 2 — Separación en 5 modalidades**
- Entrada: ventana `(44, 128)` + el array `channels` (nombres reales, no una posición fija — para no romper si el orden difiere entre participantes).
- Salida por ventana: `modality_1` EEG `(32,128)`, `modality_2` EOG `(4,128)`, `modality_3` EMG `(4,128)`, `modality_4` GSR `(1,128)`, `modality_5` Resp+Plet+Temp `(3,128)`. Todo en `float32` (no `float64` — ver nota de tamaño de archivo).

**Paso 3 — Etiqueta**
- Entrada: valencia continua (1-9) del trial padre de cada ventana.
- Salida: `label` discreta de 3 clases (bajo 1-3→`-1`, medio 4-6→`1`, alto 7-9→`2`, igual que el Husformer original) por ventana.

**Paso 4 — Split train/val/test (por participante)**
- Entrada: 76,800 ventanas con sus 5 modalidades + label + metadata.
- Salida: 3 subconjuntos disjuntos por `participant_id` — **26 participantes → train, 3 → val, 3 → test** (ningún participante se repite entre splits).

**Paso 5 — Armado de estructura final y cast a float32**
- Entrada: 3 splits con ventanas.
- Salida: diccionario `{'train': {...}, 'valid': {...}, 'test': {...}}`, cada uno con claves `modality_1`...`modality_5` (shape `(N, canales, 128)`), `label` (shape `(N,1,1)`), `id` (shape `(N,1,1)`, índice arbitrario 0..N-1 — esto es lo que `dataset.py` espera, **con guion bajo**, ver Bug 1).

**Paso 6 — Guardado del `.pkl` de entrenamiento**
- Entrada: diccionario final.
- Salida: `Husformer/data/Husformer.pkl` (formato que consume `src/5/dataset.py` directamente).

**Paso 7 — Manifest de trazabilidad (NUEVO, no viene del repo original — necesario para el sistema VA)**
El `id` dentro del `.pkl` es un índice arbitrario (0..N-1) sin significado — el modelo no necesita saber a qué participante/trial pertenece cada ventana, pero **tu sistema VA sí**, para poder mostrar "esta representación latente corresponde al participante S07, trial 12, segundo 34". Sin esto, después del entrenamiento no hay forma de reconectar `last_hs`/atención con el contexto original.
- Entrada: la misma lista de 76,800 ventanas del Paso 1-4.
- Salida: `dataset/processed/representation_inputs/husformer_manifest.csv`, con columnas: `global_window_id, participant_id, trial, window_index, window_start_sec, valence, arousal, dominance, liking, split (train/valid/test)`. Este manifest es lo que vas a unir (`join`) más adelante con `last_hs`/atención extraídos del modelo ya entrenado, para poblar tus vistas VA.

Esto te da el mínimo esfuerzo de entrenamiento (1-2 runs, no 4) sin sacrificar poder explorar las 4 dimensiones en la interfaz visual.

**Decisión 3 — Ventaneo.**
El repo original usa ventanas de 1 segundo (128 muestras a 128Hz). Podrías usar ventanas más largas (p. ej. 2-4s) ya que tu señal viene más limpia (con ICA) que la del demo original — ventanas más largas = menos ventanas totales pero cada una más informativa. Si no tienes una razón fuerte para cambiarlo, mantener 1s por fidelidad al diseño original de Husformer es lo más simple.

---

## 5. Bugs/inconsistencias del repo que hay que corregir (no son tuyos, vienen del repo original)

**Bug 1 — Nombres de claves inconsistentes.**
`Husformer/src/5/dataset.py` lee `dataset[split_type]['modality_1']` (con guion bajo), pero `Husformer/make_data/Pre-DEAP.py` guarda `train['modality1']` (sin guion bajo). Si copias el patrón de `Pre-DEAP.py` para tu script nuevo, tu `.pkl` no va a cargar — vas a tener un `KeyError` silencioso confuso. Cuando escribas `build_husformer_dataset.py`, usa las claves **con guion bajo** (`modality_1`, `modality_2`, etc., y `label`, `id`) porque esas son las que `dataset.py` realmente espera.

**Bug 2 — Los pesos de atención se descartan.**
En `modules/transformer.py`, línea 146 y 150:
```python
x, _ = self.self_attn(query=x, key=x, value=x, attn_mask=mask)
```
El `_` descarta los pesos de atención que devuelve `MultiheadAttention`. Esto significa que **ahora mismo Husformer no expone la atención cross-modal en ningún lado** — solo devuelve `(output, last_hs)` desde `HUSFORMERModel.forward()`. Para tu "Vista de Representación Fusionada y Atención Cross-Modal" vas a necesitar:
1. Modificar `TransformerEncoderLayer.forward()` para retornar también los pesos de atención (el segundo valor que hoy se descarta).
2. Propagar ese valor hacia arriba en `TransformerEncoder.forward()`.
3. Modificar `HUSFORMERModel.forward()` (en `src/5/models.py`) para retornar también los pesos de atención de `trans_m1_all`...`trans_m5_all` (las 5 cross-modal attentions hacia `proj_all`) — esos son exactamente los pesos que necesitas visualizar: cuánto atiende cada modalidad a las demás.

Esto es una modificación de código real, no solo configuración — vale la pena planearla como una tarea propia en tu checklist.

---

## 6. Checklist de implementación

- [x] Confirmar RAM total (`free -h`) → **15GB total, 7.5GB disponibles.** Sin problema.
- [ ] **Instalar PyTorch con CUDA en `env_va_deap`** (ver sección 7 — pendiente, ahora mismo `torch` no está instalado).
- [x] Decidir Decisión 1 → **5 modalidades.**
- [x] Decidir Decisión 2 → **valencia como etiqueta principal**, activación opcional como segundo run, dominancia/liking solo como encoding visual.
- [ ] Escribir `backend/scripts/build_husformer_dataset.py` (carga `.npz` → ventaneo → split → `Husformer.pkl` con claves correctas).
- [ ] Copiar `src/5/*.py` (o `src/4`) a `Husformer/src/`, copiar `main-5.py` (o `main-4.py`) como `Husformer/main.py`.
- [ ] Entrenamiento de prueba con 1-2 participantes primero (no los 32) para validar que el pipeline completo corre sin errores antes de lanzar el dataset completo.
- [ ] Entrenamiento completo con los 32 participantes.
- [ ] Aplicar el fix del Bug 2 (exponer atención cross-modal) y volver a extraer representaciones + atención para las vistas VA.
- [ ] Guardar `last_hs` + atención por trial/ventana en un formato que tu frontend/backend de visualización pueda consumir (define este formato cuando lleguemos a esa etapa).

---

## 7. Instalar PyTorch con CUDA (pendiente — `torch` no está instalado en `env_va_deap`)

Antes de instalar, revisa qué versión de CUDA soporta tu driver actual:

```bash
nvidia-smi
```

Mira la esquina superior derecha del cuadro: dice algo como `CUDA Version: 12.x`. Ese es el **máximo** que tu driver soporta (no significa que tengas que instalar exactamente esa versión, PyTorch trae su propio runtime CUDA empaquetado). Con tu GTX 1660 Ti (Turing, sm_75) cualquier build reciente de PyTorch funciona.

Con el venv activado (`source env_va_deap/bin/activate`):

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

Si `nvidia-smi` muestra una versión de CUDA vieja (menor a 12.0), usa en su lugar:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu118
```

Después verifica:

```bash
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Debería imprimir `True` y `NVIDIA GeForce GTX 1660 Ti`. Si `torch.cuda.is_available()` da `False` después de instalar, probablemente el driver de NVIDIA no está bien instalado a nivel de sistema operativo (no es un problema de PyTorch) — en ese caso avísame y lo revisamos.

---

## 8. Verificar el tamaño real del dataset (no confiar solo en la estimación)

Mi estimación (~1.7GB) es matemática, sobre datos que aún no existen como `.pkl` (todavía no se ha construido). Lo que sí existe ahora son tus `.npz` de `representation_inputs`. Para ver su tamaño real en disco:

```bash
du -sh dataset/processed/representation_inputs
```

Ojo: esto no es exactamente comparable al `Husformer.pkl` final (los `.npz` usan `savez_compressed`, el `.pkl` de Husformer no comprime), así que puede diferir. Para calcular el tamaño exacto que tendrá el `.pkl` final con la decisión de 5 modalidades ya tomada, corre esto (no necesita que el `.pkl` exista todavía, es solo aritmética sobre las formas de los tensores):

```python
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
```

Guarda esto como `check_dataset_size.py` y corre `python check_dataset_size.py` para ver el número exacto en tu propia máquina (con tus propios supuestos, si cambias el ventaneo o la partición de canales, edita el diccionario).
