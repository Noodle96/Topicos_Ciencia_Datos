# Resumen de implementación — Vista A / sub-panel A3 (perfil de participante, LineUp)

Documento vivo. **Reescrito por completo el 2026-07-22 (segunda vez el mismo día)** -- A3 vuelve al diseño de comparación de perfil de cuestionario (LineUp), a pedido explícito de Russell, después de que la misma sesión probara e implementara por completo un mapa de red de patrones de fusión cross-modal como reemplazo. Russell decidió descartar el mapa de red: revertido en código, no solo en diseño. La sección 5 conserva el resumen de esa exploración descartada, para que quede constancia de por qué se probó y por qué se abandonó -- útil para la Sección de Metodología del paper (una decisión de diseño evaluada y rechazada con criterio es tan citable como una aceptada).

## 1. Qué hace A3

Comparación de **perfil de cuestionario** de los participantes de los trials seleccionados en A1/A2, con gramática visual LineUp (Gratzl, Lex, Gehlenborg, Pfister & Streit, 2013, IEEE TVCG 19(12): 2277-2286, Best Paper Award IEEE InfoVis 2013): una tabla compacta donde cada fila es un ítem (acá, un participante) y cada celda es una barra, no texto -- atributos categóricos como segmento de color (mismo color = misma categoría, DENTRO de esa columna), atributos numéricos como barra horizontal proporcional al valor normalizado.

**Decisión de alcance (vigente desde 2026-07-08, confirmada de nuevo el 2026-07-22):** A3 no compara Valencia/Activación/Dominancia/Liking (eso ya está codificado por color y tooltip en A1, mostrarlo de nuevo en texto no aportaba nada). Compara atributos de **cuestionario** del participante (género, lateralidad manual, consumo de alcohol/cafeína, edad, horas de sueño, etc.) -- apoyo complementario a T2 (comparar trials/participantes): una vez identificado un trial/participante atípico o interesante en A1/A2, A3 ayuda a explorar si comparte rasgos demográficos con otros seleccionados.

**Selección: la MISMA de A1/A2, no una propia.** A diferencia del mapa de red descartado (que tenía su propia selección independiente, tope de 4), A3 depende directamente de `selectedTrials` -- el mismo `Map` compartido que ya usan A1/A2. Se re-pide cada vez que la selección cambia (click en un punto o en el fondo de A1/A2).

**Backend: ninguno nuevo.** Reutiliza `/api/h2/participant-profiles` (`fetchH2ParticipantProfiles`), el mismo endpoint que ya usa la vista de perfiles de H2 -- confirmado que sigue en uso ahí antes de reconectar A3 a él.

### Marks and Channels (formato "Control Evaluación Continua III")

¿Qué canales visuales se utilizan?
- El canal color (hue categórico, `d3.schemeTableau10`) codifica el atributo valor de cada atributo CATEGÓRICO de cuestionario (ej. género, lateralidad) -- escala propia POR COLUMNA, no compartida entre atributos distintos (mismo valor de dos atributos distintos no comparte color necesariamente).
- El canal longitud (barra horizontal) codifica el atributo valor de cada atributo NUMÉRICO de cuestionario (ej. edad, horas de sueño), normalizado al rango real observado entre los participantes actualmente seleccionados.
- La posición vertical (fila) codifica el atributo identidad del participante -- sin orden inherente (orden de selección/aparición).
- La posición horizontal (columna) codifica el atributo identidad del atributo de cuestionario mostrado -- categórico, fijo (mismas columnas siempre, definidas por el backend de H2).

¿Qué marcas se utilizan?
- Una marca del tipo línea (fila completa) representa el ítem participante.
- Una marca del tipo área (segmento de color o barra) representa el ítem (participante, atributo) -- el valor de UN atributo de cuestionario para UN participante.

**Nota de énfasis interactivo, no de codificación:** las columnas donde TODOS los participantes seleccionados comparten el mismo valor se resaltan con una clase CSS distinta (`.husformer-a3-common-col`) -- esto es una ayuda de lectura derivada de `common_patterns` (ya calculado por el backend), no un canal visual nuevo sobre el dato crudo.

### Abstracción de Datos (formato "Control Evaluación Continua III", Paso 3)

- **Attribute 1** — Name: participante. Type: categórico (clave). Cardinality: variable, hasta 32 (uno por cada participante con al menos un trial en `selectedTrials`). Range: N/A.
- **Attribute 2** — Name: atributo de cuestionario categórico (ej. género, lateralidad manual). Type: categórico. Cardinality: variable según el atributo (definida por el backend de H2, ej. género = 2). Range: N/A.
- **Attribute 3** — Name: atributo de cuestionario numérico (ej. edad, horas de sueño, consumo de cafeína). Type: cuantitativo. Cardinality: continuo o entero según el atributo. Range: variable, normalizado en el frontend al mín/máx real de los participantes actualmente seleccionados (no un rango fijo global -- si todos comparten el mismo valor, la barra se dibuja llena, no vacía, para no sugerir "valor bajo" donde en realidad es "todos iguales").
- **Attribute 4** — Name: cantidad de trials seleccionados de ese participante. Type: cuantitativo, derivado (Cap. 3, "Derive" -- se cuenta en el frontend a partir de `selectedTrials`, no viene del backend). Cardinality: entero, 1 a 40. Range: mostrado en el label de la fila (ej. "P01 (3)"), no como barra.

### Coordinación entre vistas (formato "Control Evaluación Continua III")

**A1/A2 → A3 → E) Vista general/detalle, variante por SELECCIÓN (no por click único).** A3 muestra el subconjunto de participantes con al menos un trial en la selección múltiple de A1/A2 (`selectedTrials`, compartido) -- comparten exactamente los mismos elementos de datos (Share Data: Subset, Munzner Cap. 12.3.1), pero con una codificación completamente distinta (tabla LineUp vs. scatter). A diferencia de B1 (drill-down de UN trial, el último clickeado), A3 responde a la selección MÚLTIPLE completa, actualizándose con cada click de agregar/quitar.

**Botón "×" por fila -- interacción que viaja en la dirección opuesta (A3 → A1/A2).** Quitar un participante desde A3 elimina TODOS sus trials de `selectedTrials` y re-renderiza A1/A2 también -- la coordinación no es unidireccional, cualquiera de las tres vistas puede modificar la selección compartida.

## 2. Qué NO está resuelto todavía

- **Sin indicador de outliers dentro del perfil mismo** -- A3 muestra los valores, pero no resalta cuál de los participantes seleccionados es el más atípico en algún atributo puntual (a diferencia de A1, que sí tiene ese propósito para el espacio de representación).
- **Sin límite de participantes seleccionables** -- a diferencia del mapa de red descartado (tope de 4 trials), A3 no impone ningún máximo; con muchos trials seleccionados de muchos participantes distintos, la tabla puede crecer bastante alto (mitigado por el scroll interno vertical, `.husformer-a3-table-wrapper`).
- **Vista A vuelve a 3 columnas iguales (1/3 cada una)** -- confirmado con Russell (2026-07-22): A1, A2 y A3 ocupan el mismo ancho, sin la asimetría que había tenido brevemente el mapa de red.

## 3. Mapa técnico rápido

**Backend:** ninguno nuevo -- reutiliza `backend/services/h2_participant_profile_service.py` / `backend/routes/h2_participant_profile_routes.py` (`GET /api/h2/participant-profiles?participants=X,Y,Z`), el mismo que usa la vista H2.

**Frontend:** `frontend/js/charts/husformer_a3_panel.js` (`renderHusformerA3Panel` -- tabla LineUp, sin dependencias de backend propias, recibe `profileData` ya resuelto), `frontend/js/husformer_main.js` (`latestA3ProfileData`, `a3RequestId`, `getParticipantTrialCounts`, `handleRemoveParticipant`, `renderA3`, `loadAndRenderA3Profiles`, `observeA3Container` -- disparado desde `handlePointToggle`/`handleBackgroundClick`), `frontend/js/api.js` (`fetchH2ParticipantProfiles`), `frontend/index.html` (`#panel-a3`, `#a3-chart`), `frontend/css/layout.css` (`.husformer-a3-*`, sin cambios -- las reglas de la tabla LineUp nunca se borraron durante la exploración del mapa de red).

## 4. Layout de Vista A y Vista B — reajuste conjunto (2026-07-22)

Al volver A3 a su tamaño de 1/3 (igual que A1/A2), quedó libre el espacio que el mapa de red había tomado permanentemente de Vista B (2/9 del layout total, fusionando A3+B3). Russell aprovechó ese espacio liberado para reajustar Vista B también, en la misma decisión:

- **Vista A:** 3 columnas iguales (A1, A2, A3 -- 1/3 cada una), sin overrides. Vuelve a las variables por defecto de `.cmv-vista` (`--col-1/2/3: 1fr`).
- **Vista B:** ya no son 3 sub-paneles (B1/B2/B3) sino 2. **El B2 original (líneas superpuestas) se descarta del sistema por completo** -- ya no hay selector Heatmap/Líneas en B1, el panel siempre muestra el heatmap. B1 ocupa 1/3 de Vista B; el panel de comparación de señales fisiológicas crudas (con todas sus funciones ya implementadas: selección múltiple de grupos, zoom, resaltado sincronizado con B1) ocupa los otros 2/3 fusionados (`grid-template-columns: 1fr 2fr` en `.cmv-vista[data-vista="B"]`). **Ese panel se reetiquetó de B3 a B2 el mismo día** (a pedido de Russell, para no dejar un hueco de numeración -- ya no tiene sentido "B3" si "B2" quedó libre): los ids/clases/nombres de función en el código ya dicen B2 (`#panel-b2`, `renderB2`, etc.), aunque los archivos siguen llamándose `husformer_b3_chart.js` / `husformer_b3_channel_groups.js` (no se pudieron renombrar, sin acceso a shell en ese momento). Ver `husformer_b3_resumen_implementacion.md` para el detalle del panel en sí.

**`husformer_b2_chart.js` NO se borró** -- mismo criterio que con el backend viejo de A3: queda como código muerto pero disponible, por si se reconsidera en el futuro. Las reglas CSS de `.husformer-b2-legend` tampoco se borraron (ya no se aplican a ningún elemento del DOM).

## 5. Historia -- el mapa de red de patrones de fusión (implementado y luego descartado, mismo día)

Antes de esta reversión, A3 fue rediseñada por completo como un **mapa de patrones de fusión cross-modal entre trials**: cada uno de los 1280 trials como nodo, conectados por similitud coseno de su firma de atención cross-modal (`attn_cross_summary` promediado y aplanado a 25 valores, top-4 vecinos por trial), layout de fuerza (d3-force), inspirado explícitamente en el mapa de enfermedades y genes compartidos del NYT (2008, basado en el "diseasome" de Goh et al.) visto en la actividad de clase de Marks and Channels -- nodo=trial, arista=similitud de firma, tamaño=grado de conexión en la red (corregido desde `|valencia-5|` tras detectar redundancia con el canal de color), color=valencia.

**Por qué se implementó:** Vista C se estaba rediseñando hacia comparación de trials contrastantes (motor de estudio de casos), y necesitaba un lugar para ELEGIR qué trials comparar -- A3 pareció el lugar natural (Vista A ya es overview de todo el dataset).

**Por qué se descartó:** decisión de Russell, sin una única razón documentada como "el" motivo -- ver `estado_proyecto.md` (memoria del proyecto) para el registro completo de la sesión, incluyendo el trabajo de layout (encuadre automático, corrección del canal de tamaño) y de infraestructura (caché en memoria, resolución del cuelgue recurrente del servidor Flask) que se hizo mientras el mapa de red estuvo vigente. El backend que construyó (`compute_trial_pattern_network`, endpoint `/api/husformer/trial-pattern-network`) y el frontend (`husformer_a3_network_chart.js`) **no se borraron** -- quedan como código funcional pero sin uso, mismo criterio que el resto del proyecto para diseños descartados.
