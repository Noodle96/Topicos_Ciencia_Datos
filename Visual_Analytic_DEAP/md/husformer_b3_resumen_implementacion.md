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

### 2.5 Selector horizontal en vez de vertical — 2026-07-17

Russell notó que el selector consumía demasiado alto: los 6 grupos (EEG Región, EEG Hemisferio, EOG, EMG, GSR, Resp+Plet+Temp) se apilaban de arriba a abajo, una fila por grupo. Se cambió `.husformer-b3-selector` de `flex-direction: column` a `flex-direction: row` + `flex-wrap: wrap` -- los grupos ahora fluyen de izquierda a derecha, cada uno como unidad compacta (label + sus chips, sin separarse entre sí vía `flex-wrap: nowrap` en `.husformer-b3-selector-row`), y solo pasan a una nueva línea cuando ya no entran en el ancho disponible. Cambio puramente de CSS, sin tocar `husformer_main.js` (la estructura DOM que arma `renderB3SelectorUI` no cambió, solo cómo se acomoda visualmente).

### 2.6 Resaltar los labels de grupo — 2026-07-17

Russell pidió que se notara más la diferencia entre los 6 grupos (EEG·Región, EEG·Hemisferio, EOG, EMG, GSR, Resp+Plet+Temp), que quedaban en fila corrida sin separación visual clara. Dos cambios: (1) separador vertical (`border-right`) entre cada grupo; (2) un punto de color junto al label, con el color BASE de la modalidad de ese grupo (mismo share encoding que ya usan los chips activos), más el texto del label agrandado y oscurecido (antes 8px gris casi invisible, ahora 9.5px `#111827`). Así cada grupo se distingue de un vistazo por color + separador, no solo por el texto.

### 2.7 Selección por defecto + colores por rampa explícita (no dinámicos) — 2026-07-17

**Selección por defecto.** B3 arrancaba sin nada seleccionado ("elegí una o más señales"). A pedido de Russell, ahora arranca con `DEFAULT_B3_GROUP_IDS` ya activos: Frontal (EEG región), Izquierdo (EEG hemisferio), EXG1 (EOG), EXG5 (EMG), GSR1 y Resp — una señal de cada una de las 6 familias de color, exactamente al tope de `MAX_SIMULTANEOUS_SIGNALS`. Da una primera impresión ya comparativa entre TODAS las modalidades, en vez de un panel vacío esperando que el usuario arme la selección desde cero.

**EEG Hemisferio deja de compartir familia de color con EEG Región.** Russell reportó que se confundían — con la selección por defecto activando Frontal + Izquierdo a la vez, ambos quedaban en tonos de azul apenas distintos por luminancia. Se le dio a Hemisferio su propia `modalityKey` (`modality_1h`, en vez de `modality_1`) con una familia de color propia (cian, no azul) — justificado en Munzner Cap. 5 (los atributos CATEGÓRICOS deben codificarse con canales de identidad, es decir HUE, no solo luminancia): Región y Hemisferio son dos esquemas de agrupamiento distintos, categóricamente separados entre sí, no dos variantes de intensidad de la misma cosa. Costo aceptado explícitamente por Russell: Hemisferio ya no comparte el azul exacto de la línea de atención EEG en B1/B2 (Región sí lo sigue haciendo).

**Rampas de color explícitas, no calculadas con `d3.color().brighter()/darker()`.** El cálculo dinámico anterior (alternar oscurecer/aclarar en pasos de 0.55) podía producir diferencias demasiado sutiles entre índices consecutivos, sobre todo hacia el lado "más claro" (se acerca al blanco del fondo del panel y pierde contraste). Se reemplazó por `COLOR_RAMPS`: 5 tonos elegidos a mano por familia (escala tipo Tailwind 300/400/600/800/900 de cada hue), con saltos de luminosidad grandes y verificables a simple vista, no derivados sobre la marcha.

### 2.8 Zoom (solo eje X) + reset por botón y doble-click — 2026-07-17

**Zoom/pan agregado, solo en el eje de TIEMPO, no en el eje Y.** Las señales ya están normalizadas (z-score) sobre un eje Y compartido -- si el zoom también reescalara Y al acercar, se podría leer erróneamente que una señal "creció" cuando en realidad solo cambió la escala visible (Munzner Cap. 11, mismo tipo de trampa que ya se evitó en A1 re-escalando los ejes en cada zoom en vez de dejarlos fijos, pero acá en sentido inverso: Y se deja fijo a propósito). Mecanismo idéntico al que ya usan A1/A2 (`d3.zoom()`, rueda = zoom, arrastre = pan) -- misma interacción en todo el sistema, no un gesto nuevo por panel. `scaleExtent` hasta 20x.

**Distinción importante aclarada con Russell antes de implementar:** zoom NO es lo mismo que la futura interacción de "seleccionar un rango de ventanas en B1/B2 para Vista C" (Sección 5, Interacciones -- brushing). Zoom es una operación de NAVEGACIÓN (cómo estoy mirando los datos, Munzner Cap. 11) que no marca nada como seleccionado ni le avisa a ningún otro panel; el brush hacia C es una operación de SELECCIÓN (qué datos me interesan para otra vista) -- categorías distintas en la taxonomía de Munzner, aunque ambas "elijan un rango de tiempo". No se conflaron en la misma interacción.

**Reset: solo del zoom, no de la selección de señales.** Aclarado explícitamente con Russell: "volver al estado original" se refería únicamente a volver a ver el trial completo (0-60s), no a resetear qué señales están activas -- son dos estados independientes (`currentB3ZoomTransform` vs. `selectedB3GroupIds`), cada uno con su propio mecanismo de reset (el zoom se resetea, la selección no se toca).

**Dos formas de resetear el zoom, ambas agregadas a pedido de Russell:** un botón visible "↺ Reset zoom" (mecanismo DESCUBRIBLE -- un doble-click no tiene ninguna pista visual de que existe) y doble-click sobre el chart (atajo rápido para quien ya lo conoce, patrón común en mapas/visualizadores). Ambos llevan el transform a `d3.zoomIdentity`. Nota técnica: `d3.zoom()` usa doble-click para ACERCAR por defecto -- hubo que desactivar ese comportamiento (`svg.on('dblclick.zoom', null)`) antes de engancharle el handler de reset propio, si no el doble-click hacía lo contrario de lo pedido.

### 2.9 Resaltado sincronizado BIDIRECCIONAL con B1/B2 — 2026-07-17

A pedido de Russell: hover en B3 resalta la ventana correspondiente en B1/B2, y viceversa (hover en B1/B2 resalta la banda correspondiente en B3). Confirmado con Russell antes de implementar: (a) bidireccional, no solo B3→B1/B2; (b) el mapeo tiempo→ventana usa `Math.floor(tiempo)` como `window_index` (justificado: `window_start_seconds[i] ≈ i` segundos exactos, confirmado en `windowing.py` -- `WINDOW_SECONDS=1.0`).

**Justificación:** linked highlighting / brushing (Becker & Cleveland 1987, ya citado en `husformer_a1_resumen_implementacion.md`) y "Share Navigation" (Munzner Cap. 12.3.3) -- el mecanismo formal para que una interacción en una vista se refleje en otra vista coordinada.

**Cómo se implementó (importante para no romperlo en cambios futuros):** cada chart (`renderHusformerB1Chart`, `renderHusformerB2Chart`, `renderHusformerB3Chart`) ahora retorna un `{ highlightWindow(windowIndex), clearHighlight() }` en vez de `undefined` -- estas funciones tocan SOLO la opacidad/contorno/posición de elementos ya existentes en el SVG (reutilizando exactamente la misma lógica que ya usaba el hover interno de cada uno), NUNCA reconstruyen el gráfico entero. Esto es deliberado: `onHoverWindowChange` se dispara en cada `mousemove` (decenas de veces por segundo) -- si la respuesta hubiera sido "volver a llamar a `renderB1()`/`renderB3()` completo" (que hacen `container.innerHTML = ""` y reconstruyen todo desde cero), el resultado habría sido lento y con parpadeos visibles. `husformer_main.js` guarda el handle activo de cada panel (`activeB1B2Handle`, `activeB3Handle`) y los conecta cruzados: el `onHoverWindowChange` de B1/B2 llama a `activeB3Handle?.highlightWindow(...)`, y el de B3 llama a `activeB1B2Handle?.highlightWindow(...)`.

**Distinción visual entre hover propio y resaltado externo (en B3):** el hover propio de B3 sigue usando la línea vertical punteada fina + tooltip de siempre; el resaltado que llega DESDE B1/B2 se dibuja como una banda semitransparente ancha (`externalHighlightBand`, sin tooltip -- no hay una posición de mouse real donde anclarlo). Así el usuario puede distinguir "estoy hovereando yo mismo acá" de "algo se resaltó porque estoy mirando otro panel".

**Interacción con el zoom de B3:** si la banda de resaltado externo está activa y el usuario hace zoom/pan en B3, la banda se redibuja en la posición correcta para el nuevo nivel de zoom (usa `currentXScale`, la misma escala mutable que ya actualiza el zoom) -- si no se hubiera contemplado esto, la banda se habría quedado "flotando" en la posición en píxeles vieja, ya no alineada con el segundo real que representa.

**Distinción respecto a la Sección 5 (Interacciones) del paper -- aclarada explícitamente con Russell:** esto NO es el brushing hacia Vista C (`"seleccionar un rango de ventanas en B1/B2 filtra las ventanas disponibles para inspección en Vista C"`). Son dos mecanismos distintos en la taxonomía de Munzner: este resaltado es "Navigate" (cómo estoy mirando, no marca nada como elegido para otra vista); el brush hacia C es "Select" (qué datos me interesan para pasarle a otra vista). No se conflaron en la misma interacción.

## 3. Qué NO está resuelto todavía

- **Zoom implementado (sección 2.8) pero SIN sincronizar contra B1/B2** — Share Navigation: Synchronize (Munzner Cap. 12.3.3) sigue siendo el mecanismo objetivo si en el futuro se quiere que acercarse en B3 también marque la misma ventana en B1/B2 -- no implementado todavía, hoy el zoom de B3 es independiente.
- **Deseleccionar un grupo dispara un fetch nuevo igual que agregar uno** — no haría falta (los datos de los grupos que quedan ya están en `latestB3RawResponse`), pero se dejó así por simplicidad; optimización menor pendiente.
- **Sin drill-down hacia Vista C todavía** — la Sección 5 del paper especifica que la interacción hacia C debería ser un BRUSH (selección de un RANGO de ventanas en B1/B2), no un click puntual — dato importante para cuando se implemente esa conexión.
- **El aviso de desajuste de granularidad ya no está en la UI de B3** (se quitó junto con el panel de atención) — evaluar si conviene reintroducirlo en otro lugar (ej. en el propio B1/B2) ahora que B3 no lo muestra directamente al lado.

## 4. Mapa técnico rápido

**Backend:** ninguno nuevo — reutiliza `backend/services/signal_service.py` / `backend/routes/signal_routes.py` (`GET /api/trial-signals`, ahora invocado con LISTAS de canales, no uno solo).

**Frontend:** `frontend/js/husformer_b3_channel_groups.js` (definiciones de grupos EEG región/hemisferio + EOG/EMG/GSR/Resp+Plet+Temp, `COLOR_RAMPS`, `getSignalColor`, `MAX_SIMULTANEOUS_SIGNALS`, `DEFAULT_B3_GROUP_IDS`), `frontend/js/charts/husformer_b3_chart.js` (`renderHusformerB3Chart` -- ahora recibe también `initialZoomTransform`/`onZoomChange`, zoom-X con `d3.zoom()`, reset por doble-click -- `buildB3Series`, `extractDuringPhaseSamples`, `averageChannels`, `zScoreNormalize`), `frontend/js/husformer_main.js` (`selectedB3GroupIds`, `latestB3RawResponse`, `currentB3ZoomTransform`, `loadAndRenderB3`, `renderB3`, `toggleB3Group`, `renderB3SelectorUI`, `resetB3Zoom`, un solo `ResizeObserver`), `frontend/index.html` (`#panel-b3`, `.husformer-b3-layout`, `#husformer-b3-selector`, `#husformer-b3-reset-zoom`, `#b3-chart`), `frontend/css/layout.css` (`.husformer-b3-*`).
