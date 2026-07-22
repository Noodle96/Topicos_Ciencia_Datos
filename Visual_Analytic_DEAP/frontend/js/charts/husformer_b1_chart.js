import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// Orden fijo de filas -- mismo orden que MODALITY_LABELS en
// husformer_attention_service.py (backend), que a su vez sigue
// MODALITY_CHANNEL_GROUPS (config.py): EEG, EOG, EMG, GSR, Resp+Plet+Temp.
// NO se reordena por similitud (a diferencia de, por ejemplo, un heatmap con
// dendrograma) -- son solo 5 categorías fijas con identidad semántica
// propia (cada una es una modalidad fisiológica distinta), reordenar no
// revelaría ninguna estructura nueva, a diferencia de una matriz con muchas
// filas intercambiables.
const MODALITY_KEYS = ["modality_1", "modality_2", "modality_3", "modality_4", "modality_5"];

// Colormap SECUENCIAL (no divergente, no categórico) -- decisión de diseño
// justificada en Munzner Cap. 10 (10.3.1): la taxonomía de colormaps
// ordenados se divide en sequential (mín→máx, un extremo) vs. diverging (dos
// extremos + punto neutro central significativo). El "peso de dominancia de
// modalidad" (promedio de attn_final_summary sobre el eje query) es una
// magnitud sin signo que va de 0 hacia arriba, SIN un punto de divergencia
// significativo (a diferencia de Valencia en A1, que sí tiene un centro
// neutro real en ~5) -- por eso aquí NO se reutiliza la escala azul-blanco-
// naranja de A1, ni la paleta categórica de A2 (que codifica identidad de
// cluster, no magnitud).
//
// d3.interpolatePlasma (2026-07-17, cambiado desde Viridis a pedido de
// Russell -- "más llamativo") -- misma familia de colormaps perceptualmente
// uniformes que Viridis (matplotlib/BIDS), NO un colormap arcoíris genérico:
// sigue cumpliendo la recomendación explícita de Munzner 10.3.2 ("colormaps
// de luminancia monótonamente creciente combinados con múltiples hues"),
// solo que con una paleta cálida (morado-rosa-naranja-amarillo) en vez de la
// fría de Viridis (morado-verde azulado-amarillo) -- mismo rigor perceptual
// y de accesibilidad (colorblind-safe, luminancia monótona), más vívida.
const ATTENTION_COLOR_INTERPOLATOR = d3.interpolatePlasma;

let clipIdCounter = 0;

/**
 * Renderiza B1 (heatmap modalidad x tiempo, Vista B).
 *
 * ESTRUCTURA -- matriz de dos claves (Munzner Cap. 7.3: "dos claves y un
 * valor = heatmaps"; 7.5.2 Matrix Alignment: una clave por filas, otra por
 * columnas, celda = región del ítem). Filas = modalidad (categórica, 5
 * valores fijos), columnas = ventana de tiempo del trial (~60, ordenadas
 * cronológicamente), celda = peso de dominancia de esa modalidad en esa
 * ventana, codificado en color.
 *
 * Por qué HEATMAP y no líneas superpuestas (eso es B2, con el mismo dato
 * agregado): el eje de filas es CATEGÓRICO (identidad de modalidad, sin
 * orden natural), y Zacks & Tversky (1999) -- citados en el resumen de
 * Munzner Cap. 7 de este proyecto -- advierten contra usar line charts
 * cuando uno de los ejes es categórico, porque implica visualmente una
 * tendencia continua que no existe entre categorías discretas. Un heatmap
 * evita ese problema: cada celda es independiente, no hay una "línea" que
 * conecte EEG con EOG sugiriendo una transición gradual entre ambas.
 *
 * B1 es el punto de entrada de Vista B ("overview first" de Shneiderman, ya
 * citado en la Sección 5 del paper) -- por eso NO tiene zoom/pan ni
 * selección propia (a diferencia de A1/A2): es una vista de resumen de UN
 * trial a la vez (el del drill-down desde Vista A), con tooltip como único
 * mecanismo de detalle-bajo-demanda (Shneiderman, "details on demand").
 *
 * DATO: % DE DOMINANCIA, NO PESO CRUDO (2026-07-17, a pedido de Russell) --
 * husformer_attention_service.py ya no devuelve el peso crudo de atención
 * (~1/640, con toda la variación real comprimida en el 3er-4to dígito
 * decimal -- dos valores distintos podían redondear ambos a "0.002" en la
 * UI). Devuelve en cambio el % de participación de cada modalidad DENTRO de
 * su ventana (las 5 modalidades de una ventana siempre suman 100, línea
 * base uniforme = 20% c/u) -- derivación justificada en Munzner Cap. 3
 * ("Derive": nuevo atributo por transformación de uno existente) y Aigner
 * Cap. 4 (4.2.2: tareas de COMPARACIÓN -- T4 compara 5 modalidades entre sí
 * -- requieren una escala unificada entre lo comparado).
 *
 * ESCALA DE COLOR DINÁMICA (por trial, no fija [0,100]) -- justificado en
 * Aigner et al. Cap. 4 (4.2.2, "Codificación de color dependiente de la
 * tarea"): Telea (2007), factor 1, advierte que una función de mapeo lineal
 * sobre un dataset sesgado comprime la mayoría de los valores en un rango
 * estrecho de colores. Aun en porcentaje, los 5 valores de una ventana
 * rondan ~20% con variación moderada -- un dominio fijo [0,100] dejaría
 * casi toda la variación real comprimida en una franja angosta de la
 * escala. Se usa en cambio la técnica de "expansión del rango de valores"
 * (Schulze-Wollgast et al. 2005; Tominski et al. 2008, citados en el mismo
 * capítulo): el dominio de color se ajusta al mín/máx REAL de los datos del
 * trial actual, maximizando el contraste para la tarea de comparación local
 * (T4: identificar qué modalidad domina y cuándo, DENTRO de este trial) a
 * costa de que el color ya no sea comparable en términos absolutos entre
 * trials distintos -- un trade-off aceptable porque T4 es una tarea de
 * comparación LOCAL, no una de lookup de magnitud absoluta.
 */
export function renderHusformerB1Chart({
    containerId,
    activeTrial,
    attentionData,
    onHoverWindowChange,
    onWindowSelect,
    selectedWindowIndex,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-b1-tooltip").remove();

    if (!activeTrial) {
        container.innerHTML = '<div class="husformer-b1-empty">Selecciona un trial en Vista A</div>';
        return null;
    }

    if (!attentionData || !attentionData.windows || attentionData.windows.length === 0) {
        container.innerHTML = '<div class="husformer-b1-empty">Cargando...</div>';
        return null;
    }

    const windows = attentionData.windows;
    const modalityLabels = attentionData.modality_labels;

    const width = container.clientWidth || 360;
    const height = container.clientHeight || 260;

    const margin = {
        top: 10,
        right: 10,
        bottom: 20,
        left: 92, // más ancho que A1/A2 -- necesita caber "Resp+Plet+Temp"
    };

    const svg = d3
        .select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    clipIdCounter += 1;
    const clipId = `husformer-b1-clip-${clipIdCounter}`;

    svg
        .append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("width", Math.max(plotWidth, 0))
        .attr("height", Math.max(plotHeight, 0));

    const plotGroup = svg
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const windowIndexToStartSec = new Map(
        windows.map((w) => [w.window_index, w.window_start_sec])
    );

    const xScale = d3
        .scaleBand()
        .domain(windows.map((w) => w.window_index))
        .range([0, plotWidth])
        .padding(0.05);

    const yScale = d3
        .scaleBand()
        .domain(MODALITY_KEYS)
        .range([0, plotHeight])
        .padding(0.08);

    // Dominio dinámico -- ver docstring (Aigner Cap. 4, expansión del rango
    // de valores).
    const allValues = windows.flatMap((w) => MODALITY_KEYS.map((key) => w[key]));
    const [minValue, maxValue] = d3.extent(allValues);

    const colorScale = d3
        .scaleSequential(ATTENTION_COLOR_INTERPOLATOR)
        .domain([minValue, maxValue]);

    // Ticks de tiempo dispersos (no uno por ventana, sería ilegible con ~60
    // columnas) -- uno cada ~10 ventanas, mostrando window_start_sec (tiempo
    // real dentro del trial, 0-60s) en vez del índice crudo de ventana, para
    // anclar la lectura a algo interpretable.
    const tickEvery = Math.max(1, Math.round(windows.length / 6));
    const tickIndices = windows
        .map((w) => w.window_index)
        .filter((_, position) => position % tickEvery === 0);

    plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .attr("font-size", "8px")
        .call(
            d3
                .axisBottom(xScale)
                .tickValues(tickIndices)
                .tickSize(3)
                .tickFormat((index) => `${Math.round(windowIndexToStartSec.get(index))}s`)
        );

    plotGroup
        .append("g")
        .attr("font-size", "8px")
        .call(
            d3
                .axisLeft(yScale)
                .tickSize(3)
                .tickFormat((modalityKey) => modalityLabels[modalityKey])
        );

    const cellsGroup = plotGroup
        .append("g")
        .attr("clip-path", `url(#${clipId})`);

    const cellData = windows.flatMap((w) =>
        MODALITY_KEYS.map((modalityKey) => ({
            windowIndex: w.window_index,
            windowStartSec: w.window_start_sec,
            modalityKey,
            modalityLabel: modalityLabels[modalityKey],
            // Porcentaje de dominancia dentro de la ventana (0-100, las 5
            // modalidades de una misma ventana suman 100) -- ver
            // husformer_attention_service.py para la derivación exacta.
            valuePct: w[modalityKey],
        }))
    );

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "husformer-b1-tooltip")
        .style("opacity", 0);

    // Agrupa las celdas por ventana -- permite armar UN tooltip consolidado
    // con las 5 modalidades de la ventana hovereada, en vez de 5 tooltips
    // separados. Decisión de diseño (Russell, 2026-07-17, tras discutir
    // ambas opciones): un solo tooltip con las 5 filas listadas evita que la
    // información quede repartida en 5 puntos distintos de la pantalla --
    // Munzner Cap. 6 (6.5.3, Change Blindness: "somos sorprendentemente
    // ciegos a cambios fuera del foco de nuestra atención") es un argumento
    // directo en contra de fragmentar el detalle en varias ventanitas
    // simultáneas lejos entre sí; consolidarlo en un solo punto mantiene
    // todo dentro del mismo foco visual (el cursor), un solo golpe de vista
    // real en vez de 5 saccades.
    const cellsByWindow = d3.group(cellData, (d) => d.windowIndex);

    const cellSelection = cellsGroup
        .selectAll(".husformer-b1-cell")
        .data(cellData)
        .enter()
        .append("rect")
        .attr("class", "husformer-b1-cell")
        .attr("x", (d) => xScale(d.windowIndex))
        .attr("y", (d) => yScale(d.modalityKey))
        .attr("width", xScale.bandwidth())
        .attr("height", yScale.bandwidth())
        .attr("fill", (d) => colorScale(d.valuePct))
        .attr("cursor", "pointer");

    // HOVER -- resalta la ventana (columna) completa de las 5 modalidades,
    // atenuando el resto. Decisión de diseño (Russell, 2026-07-17):
    //
    // Munzner Cap. 11 (11.4.2, Highlighting) distingue el idiom de
    // INTERACCIÓN (acá: hover) del idiom de CODIFICACIÓN visual del
    // resaltado, y advierte explícitamente que cambiar el COLOR DE RELLENO
    // para resaltar oculta la codificación de color ya existente -- acá el
    // color YA codifica el % de dominancia (el dato que se está
    // inspeccionando), así que un highlight por color lo taparía. Por eso
    // el resaltado se hace con CONTORNO/stroke (preserva el color de cada
    // celda) + bajar la opacidad de las columnas no relacionadas -- mismo
    // patrón que "Dynamic Layers" (Munzner Cap. 12.5.3, ejemplo Cerebral):
    // una capa de primer plano saturada/prominente contra un fondo de baja
    // saturación, construida al vuelo sobre el elemento bajo el cursor.
    // applyColumnHighlight/clearColumnHighlight -- extraídas como funciones
    // reusables (2026-07-17, sincronización bidireccional con B3, a pedido
    // de Russell): el mouseover interno de B1 las usa (y además avisa hacia
    // afuera vía onHoverWindowChange, para que B3 se resalte también), y
    // TAMBIÉN se exponen en el objeto de retorno para que husformer_main.js
    // pueda resaltar una ventana desde afuera (cuando el hover ocurre en
    // B3, no acá) -- sin reconstruir el SVG entero, solo tocando la
    // opacidad/contorno ya existente (mismo mecanismo, no uno duplicado).
    function applyColumnHighlight(windowIndex) {
        cellSelection.attr("opacity", (other) => (
            other.windowIndex === windowIndex ? 1 : 0.25
        ));

        cellSelection.attr("stroke", (other) => (
            other.windowIndex === windowIndex ? "#4b5563" : "none"
        ));

        cellSelection.attr("stroke-width", (other) => (
            other.windowIndex === windowIndex ? 0.8 : 0
        ));
    }

    function clearColumnHighlight() {
        cellSelection.attr("opacity", 1).attr("stroke", "none").attr("stroke-width", 0);
    }

    // SELECCIÓN (click) -- distinta del hover: hover es transitorio (solo
    // mientras el mouse está encima), selección es PERSISTENTE (alimenta
    // Vista C, que necesita saber "qué ventana" incluso sin el mouse
    // encima). Decisión de diseño confirmada con Russell (2026-07-22):
    // click simple sobre UNA ventana, no brushing de un rango -- más simple
    // de implementar ahora, y C2 puede sumar varias ventanas más adelante
    // con otro mecanismo (shift+click o checkboxes) sin rehacer esto.
    //
    // Se dibuja como un MARCO independiente del mecanismo de hover (no
    // reutiliza applyColumnHighlight/clearColumnHighlight) para que la
    // ventana seleccionada siga marcada incluso mientras se hace hover
    // sobre OTRA columna -- si compartiera el mismo stroke que el hover, el
    // marcador de selección desaparecería cada vez que el usuario explora
    // otras ventanas con el mouse. Color teal (#0d9488), distinto de los
    // grises de hover (#111827/#4b5563) y de los 5 colores categóricos de
    // B2 -- ver Munzner Cap. 11 (11.4.2): el idiom de codificación de
    // selección debe ser visualmente distinguible del de hover, no el mismo.
    const selectionGroup = plotGroup.append("g").attr("pointer-events", "none");

    const selectionMarker = selectionGroup
        .append("rect")
        .attr("fill", "none")
        .attr("stroke", "#0d9488")
        .attr("stroke-width", 2)
        .attr("y", 0)
        .attr("height", Math.max(plotHeight, 0))
        .style("opacity", 0);

    function drawSelectionMarker(windowIndex) {
        const x = xScale(windowIndex);

        if (x === undefined) {
            selectionMarker.style("opacity", 0);
            return;
        }

        selectionMarker
            .attr("x", x)
            .attr("width", xScale.bandwidth())
            .style("opacity", 1);
    }

    if (selectedWindowIndex !== null && selectedWindowIndex !== undefined) {
        drawSelectionMarker(selectedWindowIndex);
    }

    cellSelection.on("click", function (event, d) {
        if (onWindowSelect) {
            onWindowSelect(d.windowIndex);
        }
    });

    cellSelection
        .on("mouseover", function (event, d) {
            applyColumnHighlight(d.windowIndex);

            // La celda exacta bajo el cursor se distingue con un trazo más
            // grueso que el resto de su columna (mismo detalle que ya
            // existía) -- se aplica DESPUÉS de applyColumnHighlight porque
            // solo aplica al hover real, no al resaltado externo desde B3
            // (ahí no hay "una celda exacta", solo la ventana entera).
            d3.select(this).attr("stroke", "#111827").attr("stroke-width", 1.6);

            const windowCells = cellsByWindow.get(d.windowIndex);
            const rowsHtml = windowCells
                .map((cell) => {
                    const isHovered = cell.modalityKey === d.modalityKey;
                    return `
                        <div class="husformer-b1-tooltip-row${isHovered ? " husformer-b1-tooltip-row-active" : ""}">
                            <span>${cell.modalityLabel}</span>
                            <span>${cell.valuePct.toFixed(1)}%</span>
                        </div>
                    `;
                })
                .join("");

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Tiempo: ${d.windowStartSec.toFixed(1)}s</strong>
                    ${rowsHtml}
                `)
                .style("left", `${event.pageX + 14}px`)
                .style("top", `${event.pageY - 18}px`);

            if (onHoverWindowChange) {
                onHoverWindowChange(d.windowIndex);
            }
        })
        .on("mouseout", function () {
            clearColumnHighlight();
            tooltip.style("opacity", 0);

            if (onHoverWindowChange) {
                onHoverWindowChange(null);
            }
        });

    return {
        highlightWindow: applyColumnHighlight,
        clearHighlight: clearColumnHighlight,
        updateSelection: drawSelectionMarker,
    };
}
