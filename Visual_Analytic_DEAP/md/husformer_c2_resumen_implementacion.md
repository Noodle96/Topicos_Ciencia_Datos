# Resumen de implementación — Vista C / sub-panel C2 (señal real + atención juxtapuestas)

Documento vivo. **Tercer diseño de C2 el mismo día (2026-07-22)** -- ver `husformer_c1_resumen_implementacion.md` Sección 5 para el historial completo de los tres diseños de Vista C. Los dos anteriores de C2 (tabla numérica cruda, línea de atención sobre todo el trial) fueron descartados por Russell antes de implementarse -- solo se llegó a implementar y luego descartar el de Small Multiples de VAD (`husformer_c2_vad_chart.js`, código muerto).

## 1. Por qué este diseño

Russell pidió que Vista C dependiera de una acción sobre B2 (la señal cruda), no de la selección de A1/A2. Sobre esa base, se descartaron dos ideas antes de llegar a esta:
- **Tabla numérica del valor real en el instante:** rechazada por Russell -- "no me parece que usemos ese espacio para algo simple como mostrar un número".
- **Línea de atención de una modalidad a lo largo de TODO el trial:** rechazada por redundancia reconocida con B1 (que ya muestra la dominancia de las 5 modalidades sobre el trial completo).

## 2. Qué hace C2

Por cada modalidad actualmente activa en B2 (deduplicada -- si hay dos grupos de la misma modalidad, ej. EEG Región + EEG Hemisferio, sus canales se promedian juntos en una sola tarjeta), dos mini-gráficos de línea apilados, JUXTAPUESTOS (no superpuestos en un eje compartido), sobre una ventana de ±3 segundos alrededor del punto que se está hovereando en B2:

1. **Señal real, sin normalizar** -- el promedio de los canales reales de esa modalidad, en sus unidades originales (no el z-score que muestra B2).
2. **% de dominancia de atención** de esa misma modalidad, mismo dato que ya usa B1 (reutilizado, no recalculado).

Ambos mini-gráficos comparten el mismo eje X (tiempo) y tienen una línea guía vertical sincronizada en la posición exacta del hover -- para que sea visualmente inmediato notar si un pico/evento en la señal real (gráfico de arriba) coincide en el tiempo con un pico de atención (gráfico de abajo).

**Por qué NO un gráfico de doble eje (superimpose) en vez de dos apilados:** mismo criterio ya aplicado en el diseño original de B2 (ver `husformer_b3_resumen_implementacion.md`) -- superponer dos magnitudes de unidades completamente distintas (µV/µS de la señal vs. % de dominancia) en un solo eje Y compartido sugeriría visualmente una relación de escala que no existe. Dos gráficos juxtapuestos, alineados en X, dan la misma capacidad de comparar "¿coinciden los picos?" sin esa trampa.

**Sin backend nuevo.** Reutiliza `latestB2RawResponse` (señal cruda ya cargada por B2 para sus canales activos, sin normalizar -- se re-extrae y promedia con las mismas funciones que usa B2, ahora exportadas desde `husformer_b3_chart.js`: `extractDuringPhaseSamples`, `averageChannels`) y `latestB1Data.windows` (dominancia % ya cargada por B1). `renderC2` es puramente síncrono, no dispara ningún fetch.

### Marks and Channels (formato "Control Evaluación Continua III")

¿Qué canales visuales se utilizan?
- El canal posición horizontal (en ambos mini-gráficos de una tarjeta) codifica el atributo tiempo, dentro de la ventana de ±3s alrededor del hover (continuo, mismo dominio en ambos gráficos de la tarjeta -- eje compartido a propósito, ver justificación arriba).
- El canal posición vertical del gráfico superior codifica el atributo valor real (sin normalizar) de la señal de esa modalidad (cuantitativo, unidades propias de cada modalidad).
- El canal posición vertical del gráfico inferior codifica el atributo % de dominancia de atención de esa modalidad (cuantitativo, 0-100%, mismo dato que B1).
- El canal color (uno fijo por modalidad, share encoding con B1/B2) identifica la modalidad de la tarjeta.

¿Qué marcas se utilizan?
- Una marca del tipo línea representa el ítem serie de valores reales de una modalidad, en la ventana corta.
- Una marca del tipo línea (segundo gráfico) representa el ítem serie de % de dominancia de esa misma modalidad, en la misma ventana.

### Abstracción de Datos (formato "Control Evaluación Continua III", Paso 3)

- **Attribute 1** — Name: modalidad activa en B2. Type: categórico. Cardinality: hasta 5 (deduplicadas de los grupos/canales activos, tope original de B2 es 6 grupos, pero varios grupos pueden colapsar a la misma modalidad). Range: N/A.
- **Attribute 2** — Name: tiempo dentro de la ventana de detalle. Type: ordenado/temporal, continuo. Cardinality: variable (downsampling ya aplicado por B2). Range: `[hover - 3s, hover + 3s]` aprox.
- **Attribute 3** — Name: valor real de la señal. Type: cuantitativo, crudo (a diferencia de B2, NO se aplica z-score). Cardinality: continuo. Range: unidades propias de cada modalidad, sin normalizar.
- **Attribute 4** — Name: % de dominancia de atención. Type: cuantitativo, derivado (mismo dato de B1 -- Cap. 3 "Derive"). Cardinality: continuo. Range: 0-100%.

### Coordinación entre vistas (formato "Control Evaluación Continua III")

**B2 → C2 → E) Vista general/detalle, Multiforme.** Mismo tipo de relación que B2 → C1 (ver ese documento) -- mismo disparador (`handleB2WindowHover`), misma ventana de interés.

**B1 → C2 (dato reutilizado, sin relación de coordinación nueva).** La serie de % de dominancia que muestra el gráfico inferior de cada tarjeta es exactamente el mismo dato ya cargado para B1 -- no es una relación de vistas coordinadas en sentido estricto (no hay señal de ida y vuelta), es reutilización de datos ya en memoria.

**C1 ↔ C2.** Ver `husformer_c1_resumen_implementacion.md` Sección 2.

## 3. Qué NO está resuelto todavía

- **±3 segundos es un valor fijo, sin control de usuario** -- no hay forma de ampliar o achicar la ventana de detalle desde la UI.
- **Sin indicador numérico de "cuánto" coinciden los picos** -- la comparación es puramente visual (ojo humano juzgando si dos líneas pican al mismo tiempo), sin ninguna métrica de correlación calculada.
- **Deduplicar por modalidad puede ocultar diferencias entre sub-grupos** -- si EEG Región y EEG Hemisferio están ambos activos en B2 con perfiles distintos, C2 los promedia juntos en una sola tarjeta "EEG", perdiendo esa distinción (que B2 sí mantiene, con dos líneas separadas).

## 4. Mapa técnico rápido

**Backend:** ninguno -- reutiliza los mismos endpoints que ya usan B1 (`/api/husformer/trial-attention`) y B2 (`/api/trial-signals`).

**Frontend:** `frontend/js/charts/husformer_c2_signal_attention_overlay_chart.js` (`renderHusformerC2SignalAttentionChart` -- reutiliza `extractDuringPhaseSamples`/`averageChannels`, ahora exportadas desde `husformer_b3_chart.js`), `frontend/js/husformer_main.js` (`renderC2`, `observeC2Container` -- sin `loadAndRender*` propio, puramente síncrono; disparado desde `handleB2WindowHover`, limpiado en `loadAndRenderB2` al cambiar de trial), `frontend/index.html` (`#panel-c2`, `#c2-chart`), `frontend/css/layout.css` (`.husformer-c2-card`, `.husformer-c2-mini-label`, `.husformer-c2-scroll-row` -- las reglas `.husformer-c2-bar-*` del diseño de VAD descartado quedan como código muerto).
