# Resumen de implementación — T5 (Vista B / sub-panel B3)

Documento vivo, creado 2026-07-17. Objetivo: documentar en el momento (no al final) qué hace el sistema respecto a cada tarea, con las decisiones de diseño y su justificación, como insumo directo para la exposición y la redacción del paper.

## 1. Qué es T5 y por qué importa

**T5:** *"Relacionar picos o cambios abruptos en la atención con eventos visibles en la señal original."* Categoría: Query — Compare. Goals: **G2**, G4.

B3 es el tercer y último sub-panel de Vista B — a diferencia de B1 (T3, overview) y B2 (T4, identificación precisa), que trabajan sobre el dato DERIVADO (% de dominancia), B3 es el único que muestra la señal fisiológica REAL. Corresponde también a **OE3** de la Introducción: *"Permitir la comparación entre la señal fisiológica original y la atención asignada por el modelo, para facilitar la detección de coincidencias o discrepancias con el conocimiento del dominio."*

**Nota histórica:** B3 tuvo una descripción original distinta (un panel de detalle que se activaba con hover/click en un instante puntual) que no encajaba con el texto literal de T5 ni con OE3 — ver la corrección completa en `husformer_b1_resumen_implementacion.md`, sección 2.6. La versión implementada acá es la redefinida: señal cruda + atención coordinadas a lo largo de TODO el trial, no un instante aislado.

## 2. Cómo el sistema atiende T5 hoy — Vista B, sub-panel B3

### 2.1 Qué hace B3 (versión actual, post-rediseño — ver sección 2.4)

Comparación de **varias señales fisiológicas crudas normalizadas, superpuestas**, del trial activo (mismo `lastClickedTrial` que B1/B2). El usuario elige de un selector agrupado por modalidad (con EEG desglosado en dos esquemas: región anatómica y hemisferio, no sus 32 canales sueltos) hasta 6 señales a la vez; cada una se promedia (si el grupo tiene más de un canal), se corrige al eje temporal de "During", y se normaliza (z-score) antes de graficarse. Ya NO muestra el panel de atención de B1/B2 duplicado — ver la corrección en 2.4.

### 2.2 Pipeline de datos

**Backend: ninguno nuevo.** La señal cruda reutiliza `GET /api/trial-signals?participant=X&trial=Y&channels=Y` (`backend/services/signal_service.py`), el mismo endpoint que ya usan H1/Tarea1 — ya lee el `.bdf` real, con `sfreq` y downsampling incluidos (máx. 1200 puntos por canal). La atención reutiliza el fetch que ya hace B1 (`fetchHusformerTrialAttention`) — cero requests nuevos para eso.

**Hallazgo de alineación temporal (2026-07-17, verificado ANTES de implementar, no asumido) — importante para la validez de T5.** `/api/trial-signals` devuelve tiempos relativos al REGISTRO COMPLETO del participante (incluye fases Before/During/After del protocolo DEAP). En cambio, `window_start_sec` de `attn_final_summary` (el dato de B1/B2/atención) es relativo SOLO al inicio de la fase **During** — confirmado leyendo `preprocess_representation_inputs.py`: *"Extraer 60 segundos de During desde el archivo BDF original"*. Sin corregir este desfase, la señal cruda de B3 habría quedado desplazada respecto a la atención — un error que habría invalidado silenciosamente el propósito entero del panel (relacionar picos de atención con eventos de la señal, si ambos ejes de tiempo no significan lo mismo, cualquier "coincidencia" visual sería espuria). Se corrige restando el `start` de la fase `"During"` (que `/api/trial-signals` ya devuelve en su campo `phases`) a cada timestamp de la señal cruda, y recortando al rango `[0, ~60s]` — mismo rango que usan B1/B2. Implementado en `extractDuringPhaseSamples()`, `husformer_b3_chart.js`.

### 2.3 Decisiones de diseño de la primera versión (histórico, ver 2.4 para lo vigente)

La primera versión de B3 apilaba señal cruda arriba y el panel de atención de B1/B2 (reutilizado) abajo, justificado con juxtapose vs. superimpose (Javed et al. 2010, Munzner Cap. 12.5.2) y "Eyes Beat Memory" (Cap. 6.5). Esa parte del razonamiento (por qué NO usar un gráfico de doble eje para comparar unidades distintas) se mantiene vigente y se retoma en 2.4 para las señales entre sí. El selector de esa primera versión era un único canal (`<select>` con 44 opciones agrupadas por modalidad vía `optgroup`, default Fz) — reemplazado en 2.4.

### 2.4 Rediseño crítico — 2026-07-17: se quita la atención duplicada, selección múltiple normalizada

**Corrección importante de diseño, iniciada por una pregunta de Russell.** Russell cuestionó correctamente por qué B3 dedicaba la mitad de su espacio a repetir el panel de atención de B1/B2, si B1/B2 ya está siempre visible al lado, en la misma fila del CMV. Evaluado con sentido crítico (no solo verificando que la cita de "Eyes Beat Memory" aplicara): la cita sí aplica, pero YA ESTABA satisfecha por la sola presencia simultánea de B1/B2 y B3 en pantalla — duplicar el mismo dato con el mismo idiom DENTRO de B3 no agregaba nada, solo consumía el espacio de pantalla que Munzner (Cap. 12.2) señala como el recurso escaso que hay que cuidar al juxtaponer vistas. Se sacó el panel de atención de B3 por completo; B3 usa ahora todo su espacio para comparar señales crudas entre sí.

**Selector de canal → selector de GRUPOS, con selección múltiple.** En vez de un canal a la vez, ahora se eligen hasta `MAX_SIMULTANEOUS_SIGNALS = 6` señales simultáneas (Munzner Cap. 10: límite práctico de 6-12 bins categóricos discriminables; Cap. 12.5.2, Javed et al. 2010: superponer líneas "funciona bien con pocos ítems, una docena es manejable, pero no escala a cientos" — y T5 es una tarea de precisión que se beneficia de MENOS líneas, no de más).

**EEG ya no lista sus 32 canales — se agrupa por región Y por hemisferio (ambos esquemas disponibles a la vez):**
- *Región anatómica* (5 grupos): Frontal (9 canales), Central (7), Temporal (2: T7/T8), Parietal (9), Occipital (5).
- *Hemisferio* (3 grupos): Izquierdo (14, impares), Derecho (14, pares), Línea media (4, sufijo "z").
- Cada grupo se **promedia en vivo** sobre sus canales reales al momento de graficarse — no hay agregación precomputada, así que cambiar la definición de un grupo en el futuro no requiere reprocesar nada. Mapeo completo en `frontend/js/husformer_b3_channel_groups.js`.
- EOG (4), EMG (4), GSR (1) y Resp+Plet+Temp (3) se mantienen como canales individuales — son pocos, no tienen el problema de escala que sí tiene EEG.

**Normalización z-score obligatoria.** Sin esto, superponer µV de EEG con µS de GSR en el mismo eje Y no significa nada — cada señal se normaliza (media 0, desvío 1) antes de graficarse, independientemente de las demás.

**Color compartido con el panel de atención de B1/B2 (share encoding, Munzner Cap. 12.3.1).** Las señales de B3 usan la MISMA paleta base por modalidad que ya usan las líneas de atención de B2 (azul=EEG, rojo=EOG, verde=EMG, naranja=GSR, púrpura=Resp+Plet+Temp) — así una línea azul en B3 se conecta visualmente con "la línea azul de EEG" en B1/B2, sin necesitar una leyenda nueva. Si se seleccionan varios grupos de la MISMA modalidad (ej. Frontal + Occipital, ambos EEG), se distinguen variando luminancia/saturación dentro de esa misma familia de color (`getSignalColor`, alterna `.darker()`/`.brighter()`), no con un hue completamente distinto — para que sigan leyéndose como "la misma modalidad, dos partes".

**Fetch combinado, no uno por grupo.** Cuando cambia la selección, se pide en un solo request la UNIÓN de todos los canales necesarios para los grupos activos (`/api/trial-signals?channels=...`), no un request separado por grupo — igual de barato que antes, más simple de mantener.

**Bug de layout corregido durante esta misma ronda:** el selector de chips se había posicionado con `position:absolute` sobre el chart con un padding fijo estimado a ojo — con hasta 6 filas de chips (una por modalidad/esquema), ese padding no alcanzaba y el selector podía tapar parte del gráfico. Corregido cambiando a un layout flexbox normal (`.husformer-b3-layout`, columna: selector con `max-height` + scroll propio, chart con `flex:1`) — el chart siempre recibe el espacio real restante, sin necesidad de adivinar píxeles.

**Aviso de desajuste de granularidad:** se mantiene conceptualmente (la atención sigue siendo por modalidad completa, no por región/hemisferio específico), aunque ya no hay un panel de atención visible directamente al lado dentro de B3 para contrastarlo — el usuario compara mentalmente contra B1/B2, que está en la fila de al lado.

## 3. Qué NO está resuelto todavía

- **Sin zoom/pan.** Sigue pendiente (Share Navigation: Synchronize, Munzner Cap. 12.3.3, es el mecanismo objetivo si se agrega en el futuro, sincronizado contra B1/B2).
- **Deseleccionar un grupo dispara un fetch nuevo igual que agregar uno** — no haría falta (los datos de los grupos que quedan ya están en `latestB3RawResponse`), pero se dejó así por simplicidad; optimización menor pendiente.
- **Sin drill-down hacia Vista C todavía** — la Sección 5 del paper especifica que la interacción hacia C debería ser un BRUSH (selección de un RANGO de ventanas en B1/B2), no un click puntual — dato importante para cuando se implemente esa conexión.
- **El aviso de desajuste de granularidad ya no está en la UI de B3** (se quitó junto con el panel de atención) — evaluar si conviene reintroducirlo en otro lugar (ej. en el propio B1/B2) ahora que B3 no lo muestra directamente al lado.

## 4. Mapa técnico rápido

**Backend:** ninguno nuevo — reutiliza `backend/services/signal_service.py` / `backend/routes/signal_routes.py` (`GET /api/trial-signals`, ahora invocado con LISTAS de canales, no uno solo).

**Frontend:** `frontend/js/husformer_b3_channel_groups.js` (definiciones de grupos EEG región/hemisferio + EOG/EMG/GSR/Resp+Plet+Temp, `getSignalColor`, `MAX_SIMULTANEOUS_SIGNALS`), `frontend/js/charts/husformer_b3_chart.js` (`renderHusformerB3Chart`, `buildB3Series`, `extractDuringPhaseSamples`, `averageChannels`, `zScoreNormalize`), `frontend/js/husformer_main.js` (`selectedB3GroupIds`, `latestB3RawResponse`, `loadAndRenderB3`, `renderB3`, `toggleB3Group`, `renderB3SelectorUI`, un solo `ResizeObserver`), `frontend/index.html` (`#panel-b3`, `.husformer-b3-layout`, `#husformer-b3-selector`, `#b3-chart`), `frontend/css/layout.css` (`.husformer-b3-*`).
