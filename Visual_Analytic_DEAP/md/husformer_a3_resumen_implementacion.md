# Resumen de implementación — Vista A / sub-panel A3 (mapa de patrones de fusión cross-modal)

Documento vivo, reescrito por completo el 2026-07-22 -- reemplaza la versión anterior de A3 (comparación de perfil de cuestionario, estilo LineUp), que Russell decidió descartar en la misma sesión: no aportaba lo suficiente al objetivo del trabajo. Contenido anterior disponible en el historial de git si hace falta consultarlo.

## 1. Por qué existe esta A3 nueva

El pivote surgió de dos hilos que confluyeron el mismo día:

1. **Vista C** se estaba rediseñando de "detalle de una ventana puntual dentro de un trial" a "comparación de patrones de fusión cross-modal entre trials contrastantes" (motor del Estudio de Casos pedido explícitamente por la profesora: *"mostrar en la herramienta los patrones encontrados"*). Ese rediseño necesita, en algún lugar del sistema, una forma de **elegir QUÉ trials comparar**.
2. Analizando en profundidad el paper *"A visual analytics framework for time-series feature representation and exploration"* (Yang et al. 2025, `md/paper_time_series_visual_analytics_framework_resumen.md`) y, sobre todo, revisando de nuevo la actividad de clase sobre Marks and Channels (mapa de enfermedades y genes compartidos del NYT, 2008, basado en el "diseasome" de Goh et al.), surgió la idea de adaptar ese mismo idiom -- red de nodos conectados por una relación real -- a nuestro propio dato.

Al decidir dónde debía vivir ese "selector de trials para comparar", se descartó Vista C (que ya tiene el rol de mostrar el DETALLE de trials ya elegidos, no de elegirlos entre los 1280) y se optó por Vista A -- es un mapa de **overview de todo el dataset**, el mismo tipo de tarea que ya hace A1, solo que mirando otro dato. Justo en ese momento A3 (perfil de cuestionario) había quedado libre, al decidirse que no aportaba lo suficiente -- coincidencia útil, no causalidad forzada.

### Layout — DECISIÓN DEFINITIVA (2026-07-22)

Al probar A3 en su espacio original (1/9 de la pantalla, un tercio de la fila de Vista A), 1280 nodos resultaban ilegibles sin hacer zoom/arrastre constante. Se probó temporalmente fusionar el espacio de A3 con el de B3 (2 filas de la grilla combinadas en un solo panel) -- **Russell confirmó que este arreglo se queda como diseño PERMANENTE, no era solo para pruebas.** A3 ocupa **2/9 del layout total** (el espacio que antes eran A3 + B3 por separado, apiladas una debajo de la otra en la misma columna). Esto implica, como consecuencia directa: B3 se quedó sin espacio propio -- su destino (fusionarse como una tercera opción dentro del selector de B1/B2, o quedar absorbido de otra forma en el rediseño de Vista C) es una decisión pendiente, todavía sin resolver con Russell (ver Sección 3).

## 2. Qué hace la A3 nueva

Un **mapa de patrones de fusión cross-modal entre trials**: cada uno de los 1280 trials es un nodo; dos trials se conectan si su "firma" de atención cross-modal (`attn_cross_summary` promediado sobre sus ~60 ventanas, aplanado a 25 valores) es de las más parecidas entre sí (top-4 vecinos por trial, no todos los pares posibles). El layout es de fuerza (d3-force, force-directed) -- si el patrón de fusión realmente se relaciona con el estado afectivo, el mapa debería partirse visualmente en continentes por valencia, sin que nadie se lo diga explícitamente al sistema.

**Inspiración explícita y adaptación:** mapa de enfermedades y genes compartidos del NYT (2008, http://www.nytimes.com/interactive/2008/05/05/science/20080506_DISEASE.html, basado en Goh et al., "diseasome") -- visto en la actividad de clase de Marks and Channels. Ahí: nodo = enfermedad, arista = gen causante compartido, tamaño = cantidad de genes asociados (que en la práctica determina cuántas conexiones POTENCIALES tiene esa enfermedad con las demás), color = categoría médica. Acá: nodo = trial, arista = firma de atención cross-modal parecida, tamaño = **grado real del nodo en esta red**, color = valencia.

**⚠️ Corrección de diseño (2026-07-22, mismo día):** la primera versión usaba el tamaño para `|valencia - 5|` (qué tan extrema es la valencia reportada). Russell notó, con una pregunta directa, que esto era **redundante con el color**: la escala divergente azul-naranja ya muestra "qué tan extremo" es un trial a través de cuán saturado se ve (cerca de 5 = pálido/grisáceo, cerca de 1 o 9 = vívido) -- el tamaño estaba repitiendo la misma información dos veces por dos canales distintos. Se cambió a **grado de conexión en la red** (cuántos vecinos tiene ese nodo, contando tanto sus propios `top_k_neighbors` elegidos como cuántos otros trials lo eligieron a él de vuelta) -- además de no ser redundante con el color, es la adaptación MÁS FIEL al propio ejemplo del mapa de enfermedades que inspiró el diseño (ahí el tamaño también estaba ligado a la estructura de conexiones, no a un atributo externo sin relación con la red).

### Marks and Channels (formato "Control Evaluación Continua III")

¿Qué canales visuales se utilizan?
- El canal color (hue, escala divergente azul-naranja) codifica el atributo valencia reportada del trial -- **reutiliza exactamente la misma escala que A1** (`VALENCE_COLOR_SCALE`, exportada de `husformer_a1_chart.js`, pensada para esto desde el 2026-07-07), Share Encoding (Munzner Cap. 12.3.1): mismo lenguaje visual en todo el sistema para el mismo atributo.
- El canal área (tamaño del nodo) codifica el atributo grado del nodo (cantidad de conexiones) en la red de similitud -- cuántos otros trials tienen una firma de fusión cross-modal parecida a la de este, contando tanto sus propias conexiones elegidas como las que otros trials le asignaron a él. Dominio dinámico, ajustado al mín/máx real de grado presente en el grafo (mismo criterio de "expansión del rango de valores" que ya usa la escala de color de B1, Aigner Cap. 4).
- La posición de cada nodo **no codifica ningún atributo elegido** -- es resultado de una simulación de fuerza (atrae nodos conectados, repele el resto). Es la misma "trampa" de los node-link diagrams que ya identificamos en la actividad de clase sobre el mapa de enfermedades: agrupa visualmente lo conectado, pero no es una decisión de codificación real y hay que decirlo explícitamente, no dejar que se lea como si lo fuera.

¿Qué marcas se utilizan?
- Una marca del tipo punto representa el ítem trial.
- Una marca del tipo línea (de conexión) representa el ítem relación de similitud de firma de atención cross-modal entre dos trials.

### Abstracción de Datos (formato "Control Evaluación Continua III", Paso 3)

- **Attribute 1** — Name: firma de atención cross-modal del trial. Type: cuantitativo, derivado (Cap. 3, "Derive" -- `attn_cross_summary` promediado sobre las ventanas de un trial, aplanado). Cardinality: continuo, vector de 25 dimensiones. Range: variable, sin reescalar (mismo criterio que C1 -- no hay un total compartido que justifique normalizar a porcentaje, a diferencia de B1/B2).
- **Attribute 2** — Name: valencia reportada del trial. Type: cuantitativo. Cardinality: continuo. Range: 1-9 (escala DEAP).
- **Attribute 3** — Name: similitud de firma entre dos trials. Type: cuantitativo, derivado (similitud coseno entre los vectores de 25 dimensiones de dos trials). Cardinality: continuo, [-1, 1] en teoría, en la práctica siempre positivo dado que los valores de atención son no negativos. Range: se conserva solo el top-4 más alto por trial, no el rango completo.
- **Attribute 4** — Name: grado del trial en la red. Type: cuantitativo, derivado dos veces (Cap. 3, "Derive" -- primero la similitud de Attribute 3, después contar cuántas aristas tocan a cada nodo). Cardinality: entero, mínimo `top_k_neighbors` (4, sus propias conexiones elegidas), sin techo teórico fijo (depende de cuántos otros trials lo eligieron de vuelta). Range: variable según el grafo real, dominio dinámico ajustado en el frontend al mín/máx observado.

### Coordinación entre vistas (formato "Control Evaluación Continua III")

**A1 ↔ A3 → comparten canal de color, pero NO comparten selección.** Decisión deliberada (2026-07-22): A1/A2 comparten el mismo `Map` de selección (`selectedTrials`) desde el principio del proyecto; A3 tiene su **propio** conjunto de selección (`selectedComparisonTrials`, tope de 4), porque su propósito es distinto -- elegir CASOS CONTRASTANTES para Vista C, no marcar puntos de interés general en el espacio de representación. Forzar la misma selección hubiera mezclado dos intenciones distintas del usuario. Si en algún momento se decide unificarlas, hay que revisar el tope de selección primero.

**A3 → Vista C (pendiente de implementar):** los trials seleccionados en A3 (hasta 4) son el insumo que va a alimentar la Vista C rediseñada (comparación de casos). Todavía no está conectado -- Vista C sigue pendiente de reconstruirse.

## 3. Qué NO está resuelto todavía

- **Destino de B3, decisión pendiente con Russell** -- ver nota de layout en la Sección 1. B3 (comparación de señales fisiológicas crudas) se quedó sin panel propio al fusionarse A3 con su espacio. Opciones sobre la mesa, ninguna decidida: (a) tercera opción dentro del selector de B1/B2 (mismo patrón de botones excluyentes), (b) absorbido de otra forma dentro del rediseño de Vista C.
- **Legibilidad con 1280 nodos, parcialmente resuelta.** Ya implementado: encuadre automático al cargar (calcula el rectángulo que ocupan todos los nodos tras asentarse la simulación de fuerza, y ajusta el zoom/pan inicial para que entren todos sin arrastrar el mouse), zoom/pan manual libre desde ese punto de partida. Pendiente, a pedido de Russell: mecanismos para inspeccionar el detalle de un círculo puntual sin perder el contexto general (algo más que el zoom libre actual) -- todavía sin diseñar.
- **Conexión/coordinación con A1 y A2** -- pendiente de diseñar. Hoy A3 comparte el canal de color con A1 (Share Encoding) pero NO hay vínculo interactivo real (clickear un punto en A1/A2 no resalta nada en A3, ni viceversa). Explícitamente dejado para después de que el layout y el contenido de Vista C estén asentados (evitar rehacer interacciones si el diseño de las vistas todavía cambia).
- **Conexión con Vista C** -- pendiente, pieza siguiente del pivote grande (ver `estado_proyecto.md`, memoria del proyecto).
- **Arrastrar nodos a mano** -- no implementado; si el zoom no alcanza para desenredar zonas densas, considerar sumarlo.

## 4. Mapa técnico rápido

**Backend:** `backend/services/husformer_attention_service.py` (`compute_trial_pattern_network`, agregación por trial + similitud coseno + top-k vecinos + grado por nodo, con caché en memoria -- `_trial_pattern_network_cache`, ver nota de rendimiento más abajo), `backend/routes/husformer_attention_routes.py` (`GET /api/husformer/trial-pattern-network`, sin parámetros -- mapa del dataset completo), mismo blueprint que B1/B2/C1 (`/api/husformer`).

**Frontend:** `frontend/js/charts/husformer_a3_network_chart.js` (d3-force, simulación corrida de una vez con 300 ticks síncronos antes de dibujar, encuadre automático post-simulación -- no animada tick a tick, por rendimiento con 1280 nodos), `frontend/js/husformer_main.js` (`selectedComparisonTrials`, `MAX_SELECTED_COMPARISON_TRIALS`, `A3B3_MERGED_CONTAINER_ID`, `loadAndRenderA3Network`, `renderA3`, `handleA3NodeToggle`, `handleA3BackgroundClick`), `frontend/js/api.js` (`fetchHusformerTrialPatternNetwork`), `frontend/index.html` (`#panel-a3b3-merged`, `#a3b3-merged-chart` -- panel fusionado con lo que antes era B3, spans 2 filas de la grilla; reutiliza `.husformer-a1-legend` para la leyenda de color), `frontend/css/layout.css` (`.cmv-panel-a3b3-merged`, `.husformer-a3-selection-count`, y el ajuste de `grid-template-columns`/`grid-column` en `.system-cmv-grid`/`.cmv-vista[data-vista="A"]`/`.cmv-vista[data-vista="B"]` para el spanning de 2 filas -- **quedan marcados `⚠️ TEMPORAL` en el código todavía, pendiente pasarlos a permanentes ahora que el layout está confirmado**).

**Backend viejo de A3 (perfil de cuestionario) -- NO se borró.** `h2_participant_profile_service.py`/rutas se siguen usando desde la vista H2 (pestaña separada, confirmado revisando `h2_main.js`/`tarea1_main.js` antes de tocar nada) -- solo se dejó de llamar desde `husformer_main.js`.

**Nota de rendimiento/estabilidad (2026-07-22):** `compute_trial_pattern_network` es el cálculo más pesado del sistema (matriz de similitud 1280x1280 + carga de 3 `.npz`). Se agregó caché en memoria (se calcula una sola vez por sesión del servidor) tras una sesión larga de debugging de cuelgues del servidor Flask -- la causa raíz real terminó siendo que **scikit-learn/joblib (usado por el clustering de A2, no por A3 en sí) no es seguro corriendo en un hilo secundario creado por el servidor de desarrollo con `threaded=True`**; el arreglo definitivo fue cambiar a `threaded=False` en `backend/app.py` (ver `estado_proyecto.md` para el diagnóstico completo). La caché de A3 se queda igual, es una buena práctica por separado (evita recalcular en cada carga de página), no era la causa del cuelgue.
