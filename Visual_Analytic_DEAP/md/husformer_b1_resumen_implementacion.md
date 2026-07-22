# Resumen de implementación — T3 (Vista B / sub-panel B1)

Documento vivo, creado 2026-07-17, corregido el mismo día (ver nota de corrección). Objetivo: documentar en el momento (no al final) qué hace el sistema respecto a cada tarea, con las decisiones de diseño y su justificación, como insumo directo para la exposición y la redacción del paper. Este documento es probablemente el más importante de los cuatro para la exposición: registra un hallazgo metodológico real (sesgo estructural por máscara causal) detectado, diagnosticado y corregido durante la implementación — contenido genuino de metodología/limitaciones, no solo de UI.

**⚠️ Corrección (2026-07-17):** este documento decía originalmente "T4" como tarea principal de B1, con el texto exacto sin confirmar. Al cruzar contra el `.tex` real de Russell, la Sección 5 asigna explícitamente **B1→T3** y **B2→T4** (mapeo limpio, uno a uno) — corregido acá. B1 sí sigue relacionado con T4 indirectamente (el heatmap muestra el mismo dato que hace posible identificar dominancia), pero su tarea PRINCIPAL, confirmada por el texto de Justificación de Russell, es T3.

## 1. Qué es T3 y por qué importa

**T3:** *"Explorar la evolución temporal de los pesos de atención cross-modal dentro de un trial."* Categoría: Search — Explore (⚠️ 2026-07-17: la tabla del `.tex` decía "Query: Explore", se corrigió a "Query: Search" — sigue mal, el formato correcto es **"Search: Explore"**: Search es la categoría de nivel superior en Brehmer & Munzner 2013, paralela a Query, no un subtipo de ella; Explore es el subtipo de Search. Pendiente de corregir en el `.tex`). Goals: **G2**, G4.

**T4** (relacionada, atendida por B2 — ver `husformer_b2_resumen_implementacion.md`): *"Identificar segmentos temporales donde una modalidad domina la representación fusionada."* Categoría: Query — Identify. Goals: G2, G4.

**G2:** *"Comprender la dinámica temporal de la atención cross-modal dentro de un trial."* — tanto T3 como T4 sirven directamente a G2.

Vista B ("Atención Temporal del Trial") atiende T3, T4 y T5 con tres sub-paneles (B1/B2/B3). **B1 (este documento) es el punto de entrada de Vista B** — "overview first" (Shneiderman, ya citado en la Sección 5 de Russell): B1 atiende a T3 (explorar/escanear sin un objetivo puntual todavía), mientras B2 atiende a T4 (identificar con precisión qué modalidad domina y cuándo, una vez que el overview de B1 sugirió dónde mirar).

**Nota sobre B3 (contexto, no implementado aún):** durante el diseño se detectó una inconsistencia entre T5 (relacionar picos de atención con la señal original) y la descripción original de B3 (un panel de hover/detalle instantáneo) — no coincidían. Se confirmó con Russell redefinir B3 como una vista coordinada de señal cruda + atención superpuestas a lo largo de TODO el trial, que sí matchea el texto literal de T5 y además coincide casi textualmente con OE3 de la Introducción. Pendiente de implementar.

## 2. Cómo el sistema atiende T3 hoy — Vista B, sub-panel B1

### 2.1 Qué hace B1

Heatmap: 5 filas fijas (modalidad) × ~60 columnas (ventanas de 1s del trial activo), color = % de dominancia de esa modalidad en esa ventana. Es un **drill-down de UN trial a la vez** — el último trial clickeado en A1/A2 (independiente de la selección múltiple que usa A3; no se resetea al limpiar esa selección — decisión confirmada con Russell, 2026-07-15).

### Marks and Channels (formato "Control Evaluación Continua III")

Mismo formato del control (Munzner Cap. 5), aplicado a B1 — estructura de matriz (Cap. 7.5.2), igual que A3 pero con ejes distintos.

¿Qué canales visuales se utilizan?
- El canal posición vertical (fila) codifica el atributo identidad de la modalidad (categórico, 5 valores fijos: EEG/EOG/EMG/GSR/Resp+Plet+Temp).
- El canal posición horizontal (columna) codifica el atributo ventana de tiempo dentro del trial (ordinal, `window_index`/`window_start_sec`).
- El canal color (escala secuencial Plasma) codifica el atributo % de dominancia de esa modalidad en esa ventana (cuantitativo, dominio ajustado al mín/máx real del trial activo).

¿Qué marcas se utilizan?
- Una marca del tipo área (celda rectangular de la matriz) representa el ítem (modalidad, ventana) — la combinación de una modalidad y una ventana de 1s específicas dentro del trial activo.

### 2.2 Pipeline de datos

`backend/services/husformer_attention_service.py` → `load_husformer_trial_attention(participant_id, trial)`: carga el manifest, filtra y ordena las ventanas del trial por `window_index`, indexa `attn_final_summary` (matriz 5×5 por ventana: fila=modalidad query, columna=modalidad key) del split correspondiente vía `local_id`, y promedia sobre el eje QUERY (filas) para obtener un vector de 5 valores por ventana — "cuánta atención recibe en promedio cada modalidad de TODAS las que preguntan" (confirmado con Russell con ejemplo numérico: promediar por columna = "quién es atendido", no por fila = "quién pregunta"). Se calcula al vuelo por request, igual que el clustering de A2 — sin precómputo ni caché en disco.

### 2.3 Hallazgo crítico y su resolución — el sesgo de la máscara causal

Este es el desarrollo más importante del sub-panel, documentado en detalle porque cambió una decisión de arquitectura del MODELO, no solo de la visualización.

**Síntoma reportado por Russell:** inspeccionando la API cruda (`/api/husformer/trial-attention`), los valores eran casi idénticos entre trials distintos (variaban recién desde el 6to-7mo dígito decimal), y dentro de un mismo trial las 60 ventanas mostraban prácticamente el mismo color en B1 — siempre EEG > EOG > EMG ≈ GSR > Resp+Plet+Temp, sin excepción, para cualquier trial.

**Diagnóstico (`diagnostico_attn_final.py`, script standalone independiente de Flask):** la matriz de `std` por celda (5×5), calculada sobre TODAS las ventanas de cada split, resultó exactamente TRIANGULAR INFERIOR — el triángulo superior era 0.0 exacto en absolutamente todas las ventanas, de los 3 splits.

**Causa raíz, confirmada leyendo el código del modelo:**
- `husformer_deap_va/src/models.py` pasa `attn_mask=self.attn_mask` tanto a `trans_final` (auto-atención final) como a los 5 módulos cross-modales.
- `husformer_deap_va/main.py` línea 38 define `--attn_mask` con `action='store_false'` → el **default es `True`** ("use attention mask... default: true"). Confirmado también en `Husformer/` (el clon original, sin modificar) — no es un bug introducido en la adaptación a DEAP, es el default heredado de los propios autores de Husformer (y, más atrás, de MulT).
- `modules/transformer.py` (`buffered_future_mask`) implementa con ese flag una máscara CAUSAL clásica (triangular, -inf antes del softmax) sobre las 640 posiciones concatenadas (5 modalidades × 128 posiciones cada una, en orden fijo EEG→EOG→EMG→GSR→Resp+Plet+Temp).
- Con causal masking, el bloque de EEG (primero en la concatenación) SOLO puede atenderse a sí mismo; el bloque de Resp+Plet+Temp (último) puede atender a los 5 — un sesgo puramente ESTRUCTURAL, determinado por el orden arbitrario de concatenación, no por contenido aprendido. Explica por sí solo el patrón "EEG domina siempre".
- Causa concurrente: el modelo solo se había entrenado **1 época** (de 40 recomendadas) — dentro de lo que la máscara sí permitía, la atención estaba casi uniforme (cerca de inicialización aleatoria, sin señal aprendida real).

**Decisión tomada:** reentrenar el modelo completo (40 épocas) con `--attn_mask` pasado explícitamente como flag (invierte el default a `False`, desactivando la máscara causal). Justificación: las 5 modalidades fisiológicas concatenadas NO tienen una relación de orden temporal real entre sí (el orden m1..m5 es arbitrario) — aplicar causal masking introduce un sesgo estructural que compromete directamente la validez de cualquier análisis de interpretabilidad de atención basado en `attn_final_summary`/`attn_cross_summary` (T4, T5, y más adelante T7/G3). Es una desviación EXPLÍCITA y documentada del default de Husformer/MulT, justificada por la naturaleza no-secuencial de la fusión multimodal de este proyecto (a diferencia del texto/audio alineado temporalmente para el que MulT fue diseñado originalmente).

**Resultado del reentrenamiento** (`husformer_deap_va/output/hus_metrics.csv`, 40 épocas, ~9.6h, `batch_size=24`): overfitting severo. `train_loss` desciende monótonamente (0.107→0.056); `valid_loss` toca su mínimo en la ÉPOCA 3 (0.106) y sube después hasta 0.58 en la época 40 (~5.5× peor). `valid_mult_acc` (accuracy de 3 clases, línea base aleatoria ≈33%) llega a ~48% en la época 3 pero termina en 32.8% en la época 40 — indistinguible del azar. El scheduler `ReduceLROnPlateau` (patience=20) confirma esto desde adentro: bajó el learning rate en la época 24, exactamente 20 épocas sin mejora desde el mejor punto (época 3). El checkpoint efectivamente guardado (`hus.pt`) corresponde a la época 3 (mejor `valid_loss`), no a la época 40 — mecanismo de "guardar solo si mejora" ya presente en `train.py`, equivalente a un early-stopping automático correcto.

**Verificación posterior** (re-extracción de representaciones con el nuevo checkpoint + re-corrida de `diagnostico_attn_final.py`): la matriz de atención ya NO tiene ceros estructurales (máscara desactivada, confirmado — el triángulo superior ahora tiene variación real). Hay variación real entre ventanas de un mismo trial (coeficiente de variación antes ~0.001-0.003%, ahora ~0.02-0.9%) y entre trials distintos (medias que antes coincidían hasta el 6to-7mo dígito, ahora difieren desde el 3er-4to). El ranking "qué modalidad domina" YA NO es fijo — antes siempre EEG>EOG>EMG≈GSR>Resp; ahora varía según el trial (GSR o EMG dominan en distintos casos observados).

**Caveat honesto para no sobre-interpretar:** la variación sigue siendo modesta en términos absolutos, consistente con el desempeño débil del checkpoint usado (correlación de validación ~0.09 en el mejor caso, accuracy cerca del azar). B1 (y B2/B3 cuando existan) muestran patrones reales pero sutiles — vale la pena declarar esto como limitación en el paper, no ocultarlo.

### 2.4 Diseño visual de B1 — decisiones y justificación

**Estructura de matriz (filas=modalidad fija, columnas=tiempo, celda=color).** Munzner Cap. 7 (7.3: "dos claves y un valor = heatmaps"; 7.5.2 Matrix Alignment: una clave por filas, otra por columnas, celda = región del ítem).

**Heatmap, no líneas (eso es B2, con el mismo dato agregado).** El eje de filas es categórico (identidad de modalidad, sin orden natural) — Zacks & Tversky (1999), citados en el resumen de Munzner Cap. 7 de este proyecto, advierten contra graficar un eje categórico como si tuviera una tendencia continua tipo línea (implicaría una "transición" entre EEG y EOG que no existe).

**Colormap SECUENCIAL viridis, no divergente ni arcoíris.** Munzner Cap. 10 (10.3.1: taxonomía sequential vs. diverging — la dominancia de modalidad es una magnitud sin signo, sin punto de divergencia significativo, a diferencia de Valencia en A1; 10.3.2: recomienda explícitamente "colormaps de luminancia monótonamente creciente combinados con múltiples hues" para evitar el problema de los colormaps arcoíris — exactamente el diseño de viridis, además colorblind-safe).

**Dato mostrado: % de dominancia dentro de la ventana, no el peso crudo (~1/640).** Decisión tomada el 2026-07-17 tras reporte de Russell: dos celdas de color visiblemente distinto mostraban el mismo número redondeado en el tooltip ("0.002" ambas). Derivación EXACTA, no un reescalado arbitrario: la suma de los 5 valores de dominancia de UNA ventana es matemáticamente constante = 1/128 (consecuencia directa de que softmax normaliza cada fila real sobre las 640 posiciones) — dividir cada valor por esa suma da la participación relativa REAL de cada modalidad dentro de su ventana (0-100%, suma siempre 100%, línea base uniforme = 20% por modalidad). Justificado en Munzner Cap. 3 ("Derive": producir un atributo nuevo por transformación de uno existente) y Aigner Cap. 4 (4.2.2: tareas de COMPARACIÓN — T4 compara 5 modalidades entre sí — requieren que todas las variables comparadas compartan una escala unificada).

**Escala de color DINÁMICA por trial (dominio = mín/máx real del trial, no fijo [0,100]).** Aigner Cap. 4 (4.2.2, Telea 2007 + técnica de "expansión del rango de valores", Schulze-Wollgast et al. 2005; Tominski et al. 2008): incluso en porcentaje, los 5 valores de una ventana rondan ~20% con variación moderada — un dominio fijo [0,100] comprimiría casi toda la variación real en una franja angosta de la escala.

**Hover: resalta la ventana (columna) completa de las 5 modalidades con CONTORNO, atenúa las demás.** Munzner Cap. 11 (11.4.2 Highlighting): distingue el idiom de INTERACCIÓN (hover) del idiom de CODIFICACIÓN del resaltado, y advierte que cambiar el color de RELLENO para resaltar oculta la codificación de color ya existente — acá el color ya codifica el % de dominancia (el dato bajo inspección), así que el resaltado usa contorno/stroke, no relleno. Complementado con Cap. 12.5.3 (Dynamic Layers, ejemplo Cerebral): una capa de primer plano saturada/prominente contra un fondo de baja saturación (acá, opacidad reducida), construida al vuelo sobre el elemento bajo el cursor — mismo patrón aplicado a la columna hovereada vs. el resto del heatmap.

**Sin zoom/pan/selección propia.** B1 es una vista de resumen ("overview first") de UN trial, con tooltip como único mecanismo de detalle-bajo-demanda (Shneiderman, "details on demand") — a diferencia de A1/A2, que sí necesitan zoom/pan por mostrar 1280 puntos simultáneamente.

### 2.5 Ajustes de UI — 2026-07-17 (segunda ronda, a pedido de Russell)

**Colormap: Plasma en vez de Viridis.** Russell pidió algo "más llamativo". Se cambió `ATTENTION_COLOR_INTERPOLATOR` a `d3.interpolatePlasma` — misma familia de colormaps perceptualmente uniformes (matplotlib/BIDS) que Viridis, sigue cumpliendo la recomendación de Munzner 10.3.2 (luminancia monótonamente creciente + múltiples hues, colorblind-safe), pero con paleta cálida (morado-rosa-naranja-amarillo) en vez de la fría de Viridis. Se descartó explícitamente una paleta tipo arcoíris/jet por la advertencia del mismo capítulo.

**Tooltip consolidado (5 modalidades en un solo cuadro) en vez de 5 ventanitas separadas.** Discutido con dos opciones sobre la mesa; se eligió el tooltip único. Justificación: Munzner Cap. 6 (6.5.3, Change Blindness — "somos sorprendentemente ciegos a cambios fuera del foco de nuestra atención") argumenta en contra de repartir la información en 5 puntos distintos de la pantalla, que obligarían a varias saccades oculares; un solo tooltip anclado al cursor, listando las 5 modalidades de esa ventana con la hovereada resaltada, mantiene todo en un único foco visual. Implementado agrupando `cellData` por `windowIndex` (`d3.group`) y armando las 5 filas dentro del mismo `tooltip.html(...)`.

### 2.6 Comparte panel con B2 desde el 2026-07-17

B1 (heatmap) y B2 (líneas superpuestas) mostraban el mismo dato con dos idiomas visuales distintos, ocupando dos espacios separados del CMV — se fusionaron en un solo panel (`#panel-b1`) con un selector "Vista: Heatmap / Líneas". **B1 y B2 mantienen documentos separados a propósito** (decisión de Russell, 2026-07-17: cada idioma visual tiene sus propias justificaciones de diseño, mezclarlas en un solo documento las haría más difíciles de citar por separado en la exposición) — ver `husformer_b2_resumen_implementacion.md` para el detalle de líneas/hover/puntos por ventana. Acá solo el resumen de lo que afecta a B1 específicamente:

**El selector es de botones excluyentes, no checkbox.** Heatmap y Líneas no son capas que se combinan, son dos formas ALTERNATIVAS de ver el mismo dato — un checkbox sugeriría lo primero. Se reutilizó el mismo lenguaje visual que el selector de proyección de A1/A2 (dos botones, el activo resaltado en azul — "specification by selection", Tominski 2011).

**Implementación:** un solo contenedor (`#b1-chart`) recibe el render de `renderHusformerB1Chart` o `renderHusformerB2Chart` según `currentB1ViewMode` — ya no hay un `#b2-chart` ni un `ResizeObserver` separado para B2. Las dos leyendas (la de color dinámico de B1 y la categórica fija de B2) coexisten en el DOM y se alternan por CSS (`.husformer-b1-legend-hidden`) según el modo activo.

**Espacio liberado, entregado a B3.** La grilla de Vista B pasó de 3 columnas iguales a 2 columnas (`.cmv-vista[data-vista="B"]` en `layout.css`) — el panel fusionado (B1/B2) se queda más angosto, B3 recibe la mayor parte, anticipando que iba a necesitar más ancho (selector de señales + zoom) — confirmado correcto una vez implementado. Proporción inicial `1fr 2fr`, luego ajustada a `0.8fr 2.2fr` y finalmente a `1.1fr 2.5fr` (Russell la afinó directamente en `layout.css`, valor final a mano).

**Bug corregido (2026-07-17, reportado por Russell):** el label de trial activo (`.husformer-b1-trial-label`) y el selector Heatmap/Líneas quedaron en la MISMA esquina (`top:6px; right:8px`) al agregar el selector, superpuestos — el selector tapaba el nombre del trial en el modo Líneas. Corregido moviendo el label al centro superior del panel (`left:50%; transform:translateX(-50%)`), la única zona libre (el chip "B1" ocupa la esquina izquierda, el selector la derecha).

**Decisión de alcance para B3 (implementada, ver `husformer_b3_resumen_implementacion.md` para el detalle completo, incluida su evolución de diseño):** B3 muestra siempre TODO el trial (no un segundo aislado) — hover en una ventana puntual de B1/B2 marca esa posición dentro de la vista completa de B3 (y viceversa, sincronización bidireccional agregada después), no cambia a una vista de 1 segundo solo. Ver un único segundo con el máximo detalle queda reservado para la futura Vista C (instante puntual, matriz 5×5 completa) — cada vista mantiene su escala propia: A = trial completo, B = serie temporal del trial, C = una ventana puntual.

**Pendiente identificado (2026-07-17, pregunta de Russell aún sin resolver):** hoy clickear una celda de B1 (o un punto de B2) NO HACE NADA — solo hay hover, nunca se implementó un handler de click. Queda como decisión abierta: ¿el click debería, desde ya, dejar una marca persistente de "ventana seleccionada" (mismo patrón que `lastClickedTrial` en Vista A), pensando en que ese sea el trigger de Vista C más adelante? Ver la misma nota en `husformer_b2_resumen_implementacion.md`.

### 2.7 Resaltado sincronizado con B3 — 2026-07-17

B3 ya está implementado (ver `husformer_b3_resumen_implementacion.md`, incluye toda la justificación completa de esto) y ahora el hover de B1/B2 y el hover de B3 se resaltan mutuamente (bidireccional, confirmado con Russell). Del lado de B1/B2: `renderHusformerB1Chart`/`renderHusformerB2Chart` ya no retornan `undefined` -- devuelven `{ highlightWindow(windowIndex), clearHighlight() }`, reutilizando exactamente la misma lógica visual del hover interno (mismo `applyColumnHighlight`/`clearColumnHighlight` en B1; mismo `showGuideAtWindow`/`clearGuide` en B2), sin reconstruir el SVG. El mouseover/mouseout interno de cada uno, además de su propio resaltado, dispara `onHoverWindowChange(windowIndex | null)` -- `husformer_main.js` lo conecta con el handle activo de B3.

## 3. Qué NO está resuelto todavía

- **Sin comparación lado a lado de dos ventanas específicas** — eso corresponde a T7/C2 (Vista C, no implementada).
- **Sin indicador visual de confiabilidad del patrón mostrado**, dado el desempeño modesto del modelo — posible mejora futura (ej. algún tipo de codificación de incertidumbre).
- **Sin guía vertical compartida entre el modo Heatmap y el modo Líneas** — como ahora es el MISMO panel (uno u otro, no los dos a la vez), esto dejó de ser un problema de sincronización entre paneles distintos; sigue pendiente, eso sí, sincronizar el hover cuando B3 exista (marcar la misma ventana en B1/B2 y en B3 simultáneamente).

## 4. Mapa técnico rápido

**Backend:** `backend/services/husformer_attention_service.py` (`load_husformer_trial_attention`), `backend/routes/husformer_attention_routes.py` (`GET /api/husformer/trial-attention?participant_id=X&trial=Y`), registrado en `backend/app.py` bajo `/api/husformer`. Compartido por los dos modos (Heatmap/Líneas) — un solo fetch por trial.

**Frontend:** `frontend/js/charts/husformer_b1_chart.js` (modo Heatmap, colormap Plasma, hover de columna), `frontend/js/charts/husformer_b2_chart.js` (modo Líneas, hover con guía vertical + puntos por ventana), `frontend/js/husformer_main.js` (`lastClickedTrial`, `currentB1ViewMode`, `loadAndRenderB1`, `renderB1`, `renderB1Context`, `setupB1ViewToggle`), `frontend/js/api.js` (`fetchHusformerTrialAttention`), `frontend/index.html` (`#panel-b1`, único panel — ya no existe `#panel-b2`), `frontend/css/layout.css` (`.husformer-b1-*`, `.husformer-b2-*`, `.cmv-vista[data-vista="B"]` a 2 columnas).

**Diagnóstico independiente (raíz del proyecto, no forma parte del pipeline de producción):** `diagnostico_attn_final.py` — standalone, sin dependencia de Flask, usado para aislar el bug de la máscara causal y luego para verificar la corrección tras el reentrenamiento.

**Modelo:** `husformer_deap_va/main.py` (flag `--attn_mask` para desactivar la máscara causal), `husformer_deap_va/output/hus_metrics.csv` (curva de entrenamiento completa, 40 épocas), `husformer_deap_va/output/hus.pt` (checkpoint guardado, época 3 — mejor `valid_loss`).
