> **Nota (2026-07-17):** B2 comparte panel de pantalla con B1 desde esta fecha (selector "Vista: Heatmap / Líneas" dentro de `#panel-b1`, ver sección 2.4 más abajo) — pero mantiene su propio documento a propósito (decisión de Russell): cada idioma visual tiene su propia justificación de diseño, y mezclarlas en un solo archivo las haría más difíciles de citar por separado en la exposición. Este documento sigue vivo y se sigue actualizando.

# Resumen de implementación — T4 (Vista B / sub-panel B2)

Documento vivo, creado 2026-07-17, corregido el mismo día (ver nota de corrección). Objetivo: documentar en el momento (no al final) qué hace el sistema respecto a cada tarea, con las decisiones de diseño y su justificación, como insumo directo para la exposición y la redacción del paper.

**⚠️ Corrección (2026-07-17):** el texto de T4 estaba sin confirmar cuando se escribió este documento por primera vez. Confirmado contra el `.tex` real de Russell: **T4** es *"Identificar segmentos temporales donde una modalidad domina la representación fusionada."* Categoría: Query — Identify. Goals: **G2, G4**. La Sección 5 de Russell asigna B1→T3 (overview/exploración) y **B2→T4** (identificación precisa) de forma limpia y explícita — ya no hace falta la nota de categorización "honesta, no forzada" que tenía antes esta sección (quedaba redundante; B2 SÍ sirve a T4 directamente, confirmado por el propio texto de Justificación de Russell: *"B2 atiende a T4... separando visualmente la contribución de cada una de las cinco modalidades"*).

## 1. Qué es la tarea y por qué importa

Vista B ("Atención Temporal del Trial") atiende T3, T4 y T5 con sus tres sub-paneles. B2 comparte con B1 el mismo dato agregado (% de dominancia de modalidad por ventana), pero atiende una tarea distinta y complementaria: B1 (ver `husformer_b1_resumen_implementacion.md`) sirve a T3 (explorar/escanear sin objetivo puntual), B2 sirve a T4 (identificar con precisión qué modalidad domina y cuándo, una vez que el overview de B1 sugirió dónde mirar).

## 2. Cómo el sistema atiende esta tarea hoy — Vista B, sub-panel B2

### 2.1 Qué hace B2

Series superpuestas: 5 líneas (una por modalidad, color categórico fijo), eje X = tiempo del trial (segundos), eje Y = % de dominancia. Mismo trial que B1 (drill-down desde el último trial clickeado en Vista A) y **mismo dato exacto que B1** — no se pide nada nuevo al backend.

### 2.2 Pipeline de datos — sin fetch propio

B2 reutiliza directamente `latestB1Data` (la respuesta de `/api/husformer/trial-attention` que ya carga B1) — `husformer_main.js` renderiza B2 al final de `renderB1()`, sin un `loadAndRenderB2` independiente. Justificación: sería redundante pedirle al backend el mismo cálculo dos veces solo porque dos paneles distintos lo visualizan de forma distinta.

### 2.3 Decisiones de diseño y su justificación

**Líneas superpuestas, no apiladas ni small multiples.** Javed, J., Elmqvist, N., & Fekete, J.-D. (2010) encontraron empíricamente que, para tareas de **comparación local** (leer con precisión qué serie está más arriba/abajo de cuál EN UN INSTANTE puntual, o dónde se cruzan dos series), las líneas superpuestas superan a layouts alternativos. B1 ya cubre la lectura de *overview* (escanear las 60 ventanas de un vistazo, detectar zonas "calientes" — más alineado a T3/Explore); B2 cubre la lectura de precisión puntual.

**Mapeo de canales INVERTIDO respecto a B1 — más ajustado al principio de expresividad.** En B1, el % de dominancia (magnitud) se codifica como COLOR (canal de magnitud más débil) y la modalidad (categórica) se codifica como POSICIÓN de fila (canal de identidad fuerte, pero forzado a una matriz compacta). En B2 es al revés: el % de dominancia va en la POSICIÓN VERTICAL (Munzner Cap. 5: la posición es, en general, el canal de magnitud más preciso que existe) y la modalidad va en el HUE (canal de identidad correcto para un atributo categórico). Justificación directa: Munzner Cap. 5, "Principio de expresividad: los datos ordenados deben mostrarse con canales de magnitud; los categóricos con canales de identidad — violarlo es un error común de principiante". B1 y B2 son deliberadamente complementarios en este trade-off: B2 lee mejor la magnitud exacta, a costa de la densidad/compacidad que sí tiene el heatmap de B1 con sus 60 columnas.

**Eje X continuo (`scaleLinear` sobre `window_start_sec`), no discreto como en B1.** A diferencia del eje de FILAS de B1 (categórico, por eso ahí NO se usan líneas — ver justificación de Zacks & Tversky en `husformer_b1_resumen_implementacion.md`), el eje de tiempo de B2 es genuinamente continuo y ordenado — ahí sí es correcto conectar puntos consecutivos con una línea.

**5 colores categóricos saturados y nombrables** (azul, rojo, verde, naranja, púrpura) — Munzner Cap. 10 (10.3.1: colores saturados y nombrables como base para codificación categórica por hue). **Redundancia por patrón de trazo** (`stroke-dasharray` distinto por modalidad, además del color) — Munzner Cap. 10 (10.3.4, Colorblind-Safe Colormap Design: no apoyarse solo en hue para codificación categórica) — así dos modalidades siguen siendo distinguibles aunque dos hues se confundan bajo algún tipo de daltonismo.

**Dominio Y dinámico (mismo principio que el dominio de color de B1).** Aigner Cap. 4 (4.2.2, expansión del rango de valores): los 5 valores rondan ~20% con variación moderada — un dominio fijo [0,100] aplastaría las 5 líneas contra el centro del panel, sin distinguirse entre sí.

**Hover: guía vertical + tooltip consolidado (mismo patrón que B1).** Se ubica la ventana más cercana al cursor en X (`d3.bisector`), se dibuja una línea vertical guía en esa posición, y se muestra UN tooltip con las 5 modalidades listadas (con un punto de color por modalidad para conectar visualmente con la línea correspondiente) — mismo razonamiento que el tooltip consolidado de B1 (Munzner Cap. 6.5.3, Change Blindness): mantener el detalle en un solo punto de foco, no repartido.

### 2.4 Fusión con B1 en un solo panel — 2026-07-17

B1 (heatmap) y B2 mostraban el mismo dato en dos idiomas visuales distintos, ocupando dos espacios separados del CMV — se fusionaron en un solo panel (`#panel-b1`), con un selector "Vista: Heatmap / Líneas" (dos botones excluyentes, mismo lenguaje visual que el selector de proyección de A1/A2 — ver el detalle completo del selector y el redimensionado de la grilla de Vista B en `husformer_b1_resumen_implementacion.md`, sección 2.6). B2 ya no tiene su propio contenedor (`#b2-chart` fue eliminado) ni su propio `ResizeObserver` — `renderHusformerB2Chart` ahora se invoca sobre `#b1-chart` cuando `currentB1ViewMode === "lines"`.

**Puntos por ventana agregados (dentro de este mismo cambio).** A pedido de Russell, cada línea ahora marca sus 60 muestras reales con un punto (círculo relleno) — pensado originalmente como "un puntito verde" para poder ubicar una ventana en B2 igual que en B1. Se usó el color DE CADA LÍNEA en vez de un verde uniforme: EMG ya es verde en esta paleta categórica (`MODALITY_COLORS`), un punto verde fijo se hubiera confundido con esa línea específica y, sobre las otras 4 líneas, hubiera competido con su color real en vez de identificarlas. Efecto secundario positivo: deja explícito que cada serie son 60 muestras DISCRETAS (una por ventana de 1s), no una señal continua interpolada — un mark de punto en cada dato real, distinto del mark de línea que solo conecta (Munzner Cap. 5, Marks and Channels). Los puntos tienen `pointer-events: none` — la interacción de hover sigue viviendo en el rectángulo transparente que cubre todo el plot (`d3.bisector` sobre el punto más cercano en X), los puntos son solo refuerzo visual, no un segundo target de hover independiente.

**Pendiente identificado (2026-07-17, pregunta de Russell aún sin resolver):** hoy clickear un punto de B2 (o una celda de B1) NO HACE NADA — solo hay hover/mousemove, nunca se implementó un handler de click. Queda como decisión abierta: ¿el click debería, desde ya, dejar una marca persistente de "ventana seleccionada" (mismo patrón que `lastClickedTrial` en Vista A), pensando en que ese sea el trigger de la futura Vista C? Ver la misma nota en `husformer_b1_resumen_implementacion.md`.

### 2.5 Resaltado sincronizado con B3 — 2026-07-17

El hover de B2 (cuando está activo, `currentB1ViewMode === "lines"`) y el hover de B3 ahora se resaltan mutuamente. `renderHusformerB2Chart` ya no retorna `undefined` -- devuelve `{ highlightWindow(windowIndex), clearHighlight() }` (usa `showGuideAtWindow`/`clearGuide`, la misma lógica que ya dibujaba la guía vertical del hover interno, sin reconstruir el SVG). El mousemove interno, además de mostrar su propio tooltip, dispara `onHoverWindowChange(window_index | null)` hacia `husformer_main.js`, que lo conecta con el handle activo de B3. Detalle completo (incluida la distinción respecto al brush hacia Vista C) en `husformer_b3_resumen_implementacion.md`, sección 2.9.

## 3. Qué NO está resuelto todavía

- **Sincronización de hover ya implementada con B3** (sección 2.5) — lo que queda pendiente es sincronizar también el ZOOM de B3 con B1/B2 (hoy el zoom de B3 es independiente, ver Share Navigation: Synchronize, Munzner Cap. 12.3.3, en `husformer_b3_resumen_implementacion.md`).
- **Sin click/selección de ventana** (ver nota en 2.4) — solo hover.
- **B3 (señal cruda + atención) no implementado** — pendiente.

## 4. Mapa técnico rápido

**Backend:** ninguno nuevo — reutiliza `backend/services/husformer_attention_service.py` / `backend/routes/husformer_attention_routes.py`, ya documentados en `husformer_b1_resumen_implementacion.md`.

**Frontend:** `frontend/js/charts/husformer_b2_chart.js` (render D3, líneas + hover + puntos por ventana), `frontend/js/husformer_main.js` (`renderB1` decide entre `renderHusformerB1Chart`/`renderHusformerB2Chart` según `currentB1ViewMode`, `setupB1ViewToggle`), `frontend/index.html` (`#panel-b1` — B2 ya no tiene panel propio, el selector y ambas leyendas viven adentro de ese mismo panel), `frontend/css/layout.css` (`.husformer-b2-*`, reutiliza `.husformer-b1-tooltip-row` para el layout de filas del tooltip, `.husformer-b1-legend-hidden` para alternar leyendas).
