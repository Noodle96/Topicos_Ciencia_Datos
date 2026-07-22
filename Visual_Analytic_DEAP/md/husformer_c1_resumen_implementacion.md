# Resumen de implementación — T6 (Vista C / sub-panel C1)

Documento vivo, creado 2026-07-22. Mismo objetivo que los documentos de A1-A3/B1-B3: registrar en el momento las decisiones de diseño y su justificación por capítulo, como insumo directo para la redacción del paper.

## 1. Qué es T6 y por qué importa

**T6:** *"Inspeccionar qué modalidad recibe mayor peso de atención cross-modal en un instante dado dentro de un trial."* Categoría: Query — Identify. Goals: **G3**, G4.

**G3:** *"Relacionar los patrones de atención del modelo con las señales fisiológicas originales y con el conocimiento fisiológico esperado."* — T6, T7 (C2) y T8 (C3) sirven a G3.

Vista C ("Detalle de Atención Cross-Modal por Ventana") es el tercer y último nivel del *drill-down* del sistema (participante/trial → dinámica del trial → detalle de ventana puntual). C1 es su punto de entrada: la matriz completa de atención cross-modal de UNA ventana específica, seleccionada en B1/B2.

## 2. Cómo el sistema atiende T6 hoy — Vista C, sub-panel C1

### 2.1 Qué hace C1

Heatmap 5×5: fila = módulo de atención cruzada que "pregunta" (`trans_m{i}_all`), columna = modalidad fuente atendida, color = peso de atención promedio (`attn_cross_summary`) de esa ventana puntual. Es un **drill-down de UNA ventana a la vez** — la última ventana clickeada en B1/B2 del trial activo.

**Por qué `attn_cross_summary` y no `attn_final_summary` (el dato que ya usan B1/B2):** son dos matrices distintas del modelo (ver `extract_representations.py`). `attn_final_summary` resume la auto-atención del transformer de fusión FINAL, sobre la secuencia ya concatenada de las 5 modalidades — B1/B2 la usan porque interesa la dominancia agregada de cada modalidad en la representación fusionada (T4). `attn_cross_summary` resume, en cambio, los 5 módulos de atención CRUZADA (`trans_m{i}_all`) que ocurren ANTES de esa fusión — cada uno de estos módulos es "la modalidad i preguntando a las otras 4 (+ a sí misma)". Esta es la matriz que expone la pregunta de T6 ("qué modalidad recibe mayor atención EN UN INSTANTE dado") con el detalle fila×columna completo — B1/B2 no pueden responderla porque ya promediaron sobre el eje query antes de mostrar nada.

### Marks and Channels (formato "Control Evaluación Continua III")

Mismo formato aplicado en A3/B1/B2/B3 — estructura de matriz (Munzner Cap. 7.5.2), mismos dos ejes categóricos que B1 pero SIN el eje de tiempo (acá ambos ejes son la misma categoría: modalidad).

¿Qué canales visuales se utilizan?
- El canal posición vertical (fila) codifica el atributo módulo de atención cruzada que pregunta (categórico, 5 valores fijos, uno por modalidad).
- El canal posición horizontal (columna) codifica el atributo modalidad fuente atendida (categórico, los mismos 5 valores).
- El canal color (escala secuencial Plasma) codifica el atributo peso de atención cross-modal promedio entre ambas (cuantitativo, dominio ajustado al mín/máx de los 25 valores de esta ventana).

¿Qué marcas se utilizan?
- Una marca del tipo área (celda rectangular de la matriz) representa el ítem (módulo que pregunta, modalidad fuente) — la combinación puntual de qué módulo atiende a qué modalidad, dentro de la ventana activa.

### Abstracción de Datos (formato "Control Evaluación Continua III", Paso 3)

- **Attribute 1** — Name: módulo de atención cruzada (query). Type: categórico. Cardinality: 5 (uno por `trans_m{i}_all`, mismo orden que EEG/EOG/EMG/GSR/Resp+Plet+Temp). Range: N/A.
- **Attribute 2** — Name: modalidad fuente (atendida). Type: categórico. Cardinality: 5 (mismas 5 modalidades). Range: N/A.
- **Attribute 3** — Name: peso de atención cross-modal. Type: cuantitativo, crudo (a diferencia de B1/B2, NO se deriva ni se reescala a porcentaje — ver nota de diseño abajo). Cardinality: continuo. Range: variable por ventana, dominio ajustado dinámicamente a los 25 valores de la matriz activa.

### Coordinación entre vistas (formato "Control Evaluación Continua III")

**Vista B → Vista C (drill-down) → E) Vista general/detalle — Multiforme.** Mismo tipo de relación que A→B (ver `husformer_b1_resumen_implementacion.md`): C1 muestra el detalle de UNA sola ventana (subconjunto de las ~60 que muestra B1/B2), con una codificación distinta (matriz categoría×categoría, no categoría×tiempo) — continúa la cadena de vistas general/detalle del sistema.

**Mecanismo de selección — dos rondas de decisión el mismo día (2026-07-22):**

*Ronda 1:* a diferencia de lo que describía originalmente la Sección 5 del paper (*brushing*, seleccionar un RANGO de ventanas), se implementó selección por **click simple de una sola ventana**, confirmado con Russell. Justificación: C1 solo necesita UNA ventana activa a la vez, brushing hubiera sido trabajo adicional (nueva interacción D3 + decidir qué ventana del rango usar) sin beneficio para C1.

*Ronda 2 (☑️ vigente):* tras usarlo, Russell reportó que las matrices cross-modal cambian poco entre ventanas vecinas del mismo trial, y que click obligaba a una acción discreta por ventana para notar la diferencia — demasiado lento para "barrer" varias ventanas seguidas comparando. Se cambió el disparador de C1 de click a **hover**: mover el cursor sobre B1/B2 actualiza C1 en tiempo real, sin clicks, permitiendo una lectura fluida tipo scrubbing. El click se dejó funcionando igual (mismo handler, `handleWindowSelect` en `husformer_main.js`) — no molesta, y sirve como respaldo en touch, donde no existe hover real.

**Comportamiento "sticky" al retirar el cursor.** Si C1 volviera a su estado vacío cada vez que el mouse sale de B1/B2 (mismo patrón que el highlight de hover ya existente para B3), sería imposible mover el cursor HACIA C1 para examinarlo de cerca sin que se vaciara en el camino. Por eso `handleWindowSelect(null)` (disparado en el mouseout de B1/B2) no hace nada — C1 se queda mostrando la última ventana marcada hasta el próximo hover real.

**Guard contra fetches redundantes.** El hover de B2 dispara en cada evento `mousemove` (no uno por ventana, a diferencia de B1) — sin un guard, mover el mouse lentamente DENTRO de una misma ventana dispararía decenas de requests idénticos al backend. `handleWindowSelect` ignora la llamada si `windowIndex` es igual al ya mostrado, evitando esto sin necesitar debounce.

La Sección 5 (`Interacciones`) del `.tex` fue corregida dos veces el mismo día para reflejar cada ronda — primero de *brushing* a *clicking*, después de *clicking* a *hovering* para B→C (A→B sigue siendo *clicking*, eso no cambió).

**Diferencia con el hover ya existente en B1/B2/B3:** la selección de ventana es un estado NUEVO y distinto del hover (`selectedWindowIndex` en `husformer_main.js`, separado de `onHoverWindowChange`). El hover es transitorio (solo mientras el mouse está encima, ya usado para sincronizar B1/B2↔B3); la selección debe persistir sin el mouse encima, porque es lo que alimenta a C1. Se marca visualmente en B1 (marco color teal alrededor de la columna) y B2 (línea vertical teal) con un color deliberadamente distinto de los grises usados para hover (Munzner Cap. 11.4.2: el idiom de codificación de una interacción debe distinguirse visualmente del de otra, no compartir el mismo lenguaje visual).

### 2.2 Pipeline de datos

`backend/services/husformer_attention_service.py` → `load_husformer_window_cross_attention(participant_id, trial, window_index)`: busca la fila única del manifest para esa ventana puntual, indexa `attn_cross_summary` (matriz 5×5 cruda) del split correspondiente vía `local_id`, y la devuelve TAL CUAL — sin promediar ningún eje ni reescalar a porcentaje (a diferencia de `load_husformer_trial_attention`, usado por B1/B2). Se calcula al vuelo por request, mismo patrón que el resto del sistema (sin precómputo ni caché en disco).

**Por qué NO se reescala a porcentaje acá (a diferencia de B1/B2):** el reescalado de B1/B2 tiene sentido porque compara 5 modalidades ENTRE SÍ dentro de una ventana ya promediada (T4, "quién domina"), y esas 5 comparten un total fijo (1/128) que hace el porcentaje matemáticamente exacto. C1 no compara 5 valores con un total compartido — expone una matriz completa de 25 pesos independientes (T6, "quién le presta atención a quién"), donde no existe la misma restricción de suma constante por fila/columna que justificaba el reescalado en B1/B2.

### 2.3 Diseño visual de C1 — decisiones y justificación

**Estructura de matriz, mismo idiom que B1 (heatmap + Plasma).** Reutilizar el mismo lenguaje visual (Share Encoding, Munzner Cap. 12.3.1) ayuda a leer C1 como una continuación/zoom de B1, no como una vista sin relación — el usuario ya aprendió a leer "color = intensidad de atención" en B1.

**Colormap secuencial Plasma, dominio dinámico por ventana.** Misma justificación que B1 (Munzner 10.3.1/10.3.2, magnitud sin signo sin punto de divergencia; Aigner Cap. 4, expansión del rango de valores) — acá el "trial de referencia" para el mín/máx es la propia matriz de 25 valores de la ventana activa, no un trial completo de 60 ventanas.

**Etiquetas de eje explícitas ("Modalidad fuente" / "Módulo que pregunta").** A diferencia de B1 (donde el eje X es obviamente tiempo y el eje Y obviamente modalidad, sin ambigüedad posible), acá AMBOS ejes son la misma categoría (las 5 modalidades) — sin una etiqueta que aclare cuál es cuál, la matriz sería ambigua sobre qué representa cada eje.

**Sin zoom/pan/selección propia.** C1 es la vista de detalle MÁS profunda del sistema (no hay una Vista D después) — su único mecanismo de detalle-bajo-demanda es el tooltip por celda (mismo patrón que B1/A1).

## 3. Qué NO está resuelto todavía

- **C2 y C3 no implementados aún** — C1 es el primer sub-panel de Vista C; C2 (Small Multiples de varias ventanas) y C3 (señal cruda de la ventana activa) quedan pendientes.
- **Sin sincronización de hover C1↔B1/B2** (a diferencia de B1/B2↔B3) — hacer hover sobre una celda de C1 no resalta nada en B1/B2, ni viceversa (el mecanismo existente ahí es de SELECCIÓN, no de hover). Podría evaluarse más adelante si aporta algo remarcar en B1/B2 la fila/columna correspondiente al hover en C1.
- **Sin indicador de si el patrón mostrado es fisiológicamente plausible** (relacionado con G3/T6) — queda para la Sección de Discusión del paper, no es algo que la UI pueda resolver por sí sola.

## 4. Mapa técnico rápido

**Backend:** `backend/services/husformer_attention_service.py` (`load_husformer_window_cross_attention`, además de `_load_split_attn_cross_summary`), `backend/routes/husformer_attention_routes.py` (`GET /api/husformer/window-cross-attention?participant_id=X&trial=Y&window_index=Z`), mismo blueprint que B1/B2 (`/api/husformer`), sin cambios en `app.py` (blueprint ya registrado).

**Frontend:** `frontend/js/charts/husformer_c1_chart.js` (heatmap 5×5, Plasma, tooltip por celda), `frontend/js/husformer_main.js` (`selectedWindowIndex`, `latestC1Data`, `loadAndRenderC1`, `renderC1`, `handleWindowSelect` — y el click nuevo agregado a `renderHusformerB1Chart`/`renderHusformerB2Chart` vía `onWindowSelect`/`updateSelection`), `frontend/js/api.js` (`fetchHusformerWindowCrossAttention`), `frontend/index.html` (`#panel-c1`, ya scaffolded desde antes).

**Paper:** `articulo_DEAP_visualization/secciones/05_diseno_visual.tex`, Sección `Interacciones` corregida (2026-07-22) — decía *brushing* para B→C, ahora dice *clicking* (selección de una ventana), reflejando la implementación real.
