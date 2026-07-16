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
// d3.interpolateViridis se elige específicamente (no un colormap arcoíris
// genérico) porque es la solución que Munzner recomienda explícitamente en
// 10.3.2: "colormaps de luminancia monótonamente creciente combinados con
// múltiples hues" -- viridis fue diseñado siguiendo exactamente ese
// principio (perceptualmente uniforme, luminancia monótona, seguro para
// daltonismo), a diferencia de un rainbow/jet clásico (hue sin orden
// perceptual, no lineal, detalle fino ilegible).
const ATTENTION_COLOR_INTERPOLATOR = d3.interpolateViridis;

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
 * ESCALA DE COLOR DINÁMICA (por trial, no fija [0,1]) -- justificado en
 * Aigner et al. Cap. 4 (4.2.2, "Codificación de color dependiente de la
 * tarea"): Telea (2007), factor 1, advierte que una función de mapeo lineal
 * sobre un dataset sesgado comprime la mayoría de los valores en un rango
 * estrecho de colores. Como cada peso de dominancia es un promedio de 5
 * valores de atención que típicamente rondan ~0.2 (1/5) con variación
 * moderada, un dominio fijo [0,1] dejaría casi toda la variación real
 * comprimida cerca del extremo bajo de la escala. Se usa en cambio la
 * técnica de "expansión del rango de valores" (Schulze-Wollgast et al. 2005;
 * Tominski et al. 2008, citados en el mismo capítulo): el dominio de color
 * se ajusta al mín/máx REAL de los datos del trial actual, maximizando el
 * contraste para la tarea de comparación local (T4: identificar qué
 * modalidad domina y cuándo, DENTRO de este trial) a costa de que el color
 * ya no sea comparable en términos absolutos entre trials distintos -- un
 * trade-off aceptable porque T4 es una tarea de comparación LOCAL, no una
 * de lookup de magnitud absoluta.
 */
export function renderHusformerB1Chart({ containerId, activeTrial, attentionData }) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-b1-tooltip").remove();

    if (!activeTrial) {
        container.innerHTML = '<div class="husformer-b1-empty">Selecciona un trial en Vista A</div>';
        return;
    }

    if (!attentionData || !attentionData.windows || attentionData.windows.length === 0) {
        container.innerHTML = '<div class="husformer-b1-empty">Cargando...</div>';
        return;
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
            value: w[modalityKey],
        }))
    );

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "husformer-b1-tooltip")
        .style("opacity", 0);

    cellsGroup
        .selectAll(".husformer-b1-cell")
        .data(cellData)
        .enter()
        .append("rect")
        .attr("class", "husformer-b1-cell")
        .attr("x", (d) => xScale(d.windowIndex))
        .attr("y", (d) => yScale(d.modalityKey))
        .attr("width", xScale.bandwidth())
        .attr("height", yScale.bandwidth())
        .attr("fill", (d) => colorScale(d.value))
        .attr("cursor", "default")
        .on("mouseover", function (event, d) {
            d3.select(this)
                .attr("stroke", "#111827")
                .attr("stroke-width", 1.2);

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Modalidad:</strong> ${d.modalityLabel}<br>
                    <strong>Tiempo:</strong> ${d.windowStartSec.toFixed(1)}s<br>
                    <strong>Peso de dominancia:</strong> ${d.value.toFixed(3)}
                `)
                .style("left", `${event.pageX + 14}px`)
                .style("top", `${event.pageY - 18}px`);
        })
        .on("mouseout", function () {
            d3.select(this).attr("stroke", "none");
            tooltip.style("opacity", 0);
        });
}
