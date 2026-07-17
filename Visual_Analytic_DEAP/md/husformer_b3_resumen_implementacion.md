# Resumen de implementación — T5 (Vista B / sub-panel B3)

Documento vivo, creado 2026-07-17. Objetivo: documentar en el momento (no al final) qué hace el sistema respecto a cada tarea, con las decisiones de diseño y su justificación, como insumo directo para la exposición y la redacción del paper.

## 1. Qué es T5 y por qué importa

**T5:** *"Relacionar picos o cambios abruptos en la atención con eventos visibles en la señal original."* Categoría: Query — Compare. Goals: **G2**, G4.

B3 es el tercer y último sub-panel de Vista B — a diferencia de B1 (T3, overview) y B2 (T4, identificación precisa), que trabajan sobre el dato DERIVADO (% de dominancia), B3 es el único que muestra la señal fisiológica REAL. Corresponde también a **OE3** de la Introducción: *"Permitir la comparación entre la señal fisiológica original y la atención asignada por el modelo, para facilitar la detección de coincidencias o discrepancias con el conocimiento del dominio."*

**Nota histórica:** B3 tuvo una descripción original distinta (un panel de detalle que se activaba con hover/click en un instante puntual) que no encajaba con el texto literal de T5 ni con OE3 — ver la corrección completa en `husformer_b1_resumen_implementacion.md`, sección 2.6. La versión implementada acá es la redefinida: señal cruda + atención coordinadas a lo largo de TODO el trial, no un instante aislado.

## 2. Cómo el sistema atiende T5 hoy — Vista B, sub-panel B3

### 2.1 Qué hace B3

Dos paneles apilados, compartiendo el trial activo (mismo `lastClickedTrial` que B1/B2): arriba, la señal fisiológica cruda de UN canal seleccionable (selector agrupado por modalidad, 44 canales); abajo, el panel de atención de las 5 modalidades — **literalmente el mismo componente que el modo Líneas de B1/B2 (`renderHusformerB2Chart`), reutilizado sin modificar**, alimentado con el mismo `latestB1Data` que ya está cargado.

### 2.2 Pipeline de datos

**Backend: ninguno nuevo.** La señal cruda reutiliza `GET /api/trial-signals?participant=X&trial=Y&channels=Y` (`backend/services/signal_service.py`), el mismo endpoint que ya usan H1/Tarea1 — ya lee el `.bdf` real, con `sfreq` y downsampling incluidos (máx. 1200 puntos por canal). La atención reutiliza el fetch que ya hace B1 (`fetchHusformerTrialAttention`) — cero requests nuevos para eso.

**Hallazgo de alineación temporal (2026-07-17, verificado ANTES de implementar, no asumido) — importante para la validez de T5.** `/api/trial-signals` devuelve tiempos relativos al REGISTRO COMPLETO del participante (incluye fases Before/During/After del protocolo DEAP). En cambio, `window_start_sec` de `attn_final_summary` (el dato de B1/B2/atención) es relativo SOLO al inicio de la fase **During** — confirmado leyendo `preprocess_representation_inputs.py`: *"Extraer 60 segundos de During desde el archivo BDF original"*. Sin corregir este desfase, la señal cruda de B3 habría quedado desplazada respecto a la atención — un error que habría invalidado silenciosamente el propósito entero del panel (relacionar picos de atención con eventos de la señal, si ambos ejes de tiempo no significan lo mismo, cualquier "coincidencia" visual sería espuria). Se corrige restando el `start` de la fase `"During"` (que `/api/trial-signals` ya devuelve en su campo `phases`) a cada timestamp de la señal cruda, y recortando al rango `[0, ~60s]` — mismo rango que usan B1/B2. Implementado en `extractDuringPhaseSamples()`, `husformer_b3_chart.js`.

### 2.3 Decisiones de diseño y su justificación

**Apilado (juxtapose), no superpuesto en un gráfico de doble eje.** Justificación precisa, Munzner Cap. 12 (12.5.2), hallazgo empírico de Javed et al. (2010): *"superponer es mejor para comparaciones dentro de un span visual LOCAL (ej. encontrar el máximo en un punto temporal específico); juxtaponer es mejor para tareas GLOBALES DISPERSAS, especialmente cuando aumenta el número de series."* T5 pide escanear TODO el trial buscando coincidencias entre picos de atención y eventos de la señal — una tarea global dispersa, no un chequeo puntual — así que juxtaponer es lo que corresponde. Argumento adicional, Cap. 12.2: superimponer capas tiene un límite duro (2 capas muy viable, 3 posible con cuidado); el panel de atención YA tiene 5 líneas (B2 reutilizado) — agregar la señal cruda como 6ta capa superpuesta habría sido inviable. Munzner Cap. 12.2 también conecta directamente esta decisión con "Eyes Beat Memory" (Cap. 6.5): dos vistas simultáneamente visibles son más fáciles de comparar que una vista contra la memoria de trabajo — exactamente el argumento ya usado para justificar que B3 muestre TODO el trial en vez de un instante aislado bajo demanda.

**Selector de canal agrupado por modalidad (optgroup), no un selector de dos pasos.** Decisión de Russell (2026-07-17, confirmada entre dos opciones presentadas): un solo `<select>` con los 44 canales agrupados visualmente (EEG/EOG/EMG/GSR/Resp+Plet+Temp vía `<optgroup>`), en vez de un selector de modalidad primero y canal después. Un solo control, más simple.

**Canal por defecto: Fz (no GSR1).** Decisión de Russell: un canal EEG representativo en vez del único canal sin ambigüedad (GSR1). Trade-off consciente: reintroduce el desajuste canal/modalidad (ver nota abajo) desde la primera impresión del panel, pero Fz es más relevante fisiológicamente para varios investigadores del dominio (canal frontal medio, común en estudios de asimetría frontal EEG y valencia).

**Aviso explícito de desajuste de granularidad.** La atención se calcula por MODALIDAD completa (`attn_final_summary`, agregado sobre los 32 canales de EEG, por ejemplo), no por canal individual — mostrar el canal "Fz" junto a "la atención de EEG" podría sugerir una precisión que no existe. Se agregó una nota fija en la UI (`.husformer-b3-note`), no solo en este documento, porque es una limitación que el usuario necesita ver en el momento de leer el panel, no solo en la documentación.

**Zoom sincronizado: pendiente, no en esta primera versión.** El mecanismo formal para esto es "Share Navigation: Synchronize" (Munzner Cap. 12.3.3) — mover el punto de vista en un panel se sincroniza con el otro. Se dejó fuera del alcance de esta primera versión a propósito, para no sumar la complejidad de fusionar dos zooms sobre dos SVGs separados de una sola vez — los dos paneles muestran el trial completo (0 a ~60s) sin zoom por ahora.

## 3. Qué NO está resuelto todavía

- **Sin zoom/pan, ni sincronizado ni individual** — ver nota arriba (Share Navigation: Synchronize, Cap. 12.3.3, queda como el mecanismo objetivo para una próxima iteración).
- **Sin hover sincronizado entre el panel de señal y el panel de atención** — cada uno tiene su propia guía vertical/tooltip, independientes entre sí.
- **Los márgenes de los dos SVGs (señal y atención) están alineados "a ojo", no matemáticamente** — como son dos `<svg>` separados (no una sola pieza compartida), el eje X de arriba y el de abajo pueden no coincidir en píxeles exactos, aunque representen el mismo rango de tiempo.
- **Sin drill-down hacia Vista C todavía** — la Sección 5 de Russell especifica que la interacción hacia C debería ser un BRUSH (selección de un RANGO de ventanas en B1/B2), no un click puntual — dato importante para cuando se implemente esa conexión, no resuelto ahora.

## 4. Mapa técnico rápido

**Backend:** ninguno nuevo — reutiliza `backend/services/signal_service.py` / `backend/routes/signal_routes.py` (`GET /api/trial-signals`) para la señal cruda, y `husformer_attention_service.py`/`husformer_attention_routes.py` (ya documentados) para la atención.

**Frontend:** `frontend/js/charts/husformer_b3_chart.js` (`renderHusformerB3SignalChart`, incluye `extractDuringPhaseSamples` para la corrección de alineación temporal), `frontend/js/husformer_main.js` (`currentB3Channel`, `latestB3SignalData`, `loadAndRenderB3`, `renderB3`, `setupB3ChannelControl`, dos `ResizeObserver` — uno por sub-panel), `frontend/js/api.js` (reutiliza `fetchTrialSignals`, ya existente para H1/Tarea1), `frontend/index.html` (`#panel-b3`, selector de canal, aviso de granularidad, `#b3-signal-chart` + `#b3-attention-chart`), `frontend/css/layout.css` (`.husformer-b3-*`).
