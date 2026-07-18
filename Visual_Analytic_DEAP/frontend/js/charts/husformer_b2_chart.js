import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// Mismo orden fijo que B1 (husformer_b1_chart.js) y que MODALITY_LABELS en
// husformer_attention_service.py.
const MODALITY_KEYS = ["modality_1", "modality_2", "modality_3", "modality_4", "modality_5"];

// Color CATEGÓRICO por modalidad -- a diferencia de B1 (que usa Plasma,
// canal de MAGNITUD, para el mismo % de dominancia codificado como color de
// celda), acá la modalidad es la identidad de cada línea, no una magnitud.
// Justificación: Munzner Cap. 5, "Principio de expresividad: los datos
// ordenados deben mostrarse con canales de magnitud; los categóricos con
// canales de identidad -- violarlo es un error común de principiante".
// B2 en realidad invierte el mapeo de canales de B1: acá el % de dominancia
// (magnitud) va en la POSICIÓN vertical (el canal de magnitud más preciso
// que existe, más que el color), y la modalidad (categórica) va en el HUE
// -- un mapeo más ajustado al principio de expresividad que el de B1, a
// costa de perder la densidad/compacidad del heatmap (60 celdas por fila
// vs. una línea dispersa en el mismo ancho). B1 y B2 son complementarios
// exactamente por este trade-off.
//
// 5 colores saturados y NOMBRABLES (Munzner Cap. 10, 10.3.1: "colores
// saturados y nombrables -- rojo, azul, verde, amarillo, naranja... son la
// mejor base" para codificación categórica por hue). Colorblind-conscious
// (10.3.4): no se apoya SOLO en hue -- cada línea tiene además un patrón de
// trazo distinto (stroke-dasharray, ver LINE_DASH_PATTERNS) como canal
// redundante, para que dos modalidades sigan siendo distinguibles aunque
// dos hues se confundan entre sí bajo algún tipo de daltonismo.
const MODALITY_COLORS = {
    modality_1: "#2563eb", // EEG -- azul
    modality_2: "#dc2626", // EOG -- rojo
    modality_3: "#16a34a", // EMG -- verde
    modality_4: "#d97706", // GSR -- naranja/ámbar
    modality_5: "#9333ea", // Resp+Plet+Temp -- púrpura
};

const LINE_DASH_PATTERNS = {
    modality_1: "none",
    modality_2: "6,3",
    modality_3: "2,2",
    modality_4: "8,3,2,3",
    modality_5: "1,3",
};

let clipIdCounter = 0;

/**
 * Renderiza B2 (series superpuestas por modalidad, Vista B).
 *
 * MISMO DATO que B1 (attentionData.windows, % de dominancia por modalidad
 * por ventana) -- no pide nada nuevo al backend, husformer_main.js pasa
 * directamente latestB1Data. Solo cambia el IDIOM visual: heatmap (B1) vs.
 * líneas superpuestas (B2).
 *
 * POR QUÉ LÍNEAS SUPERPUESTAS (no apiladas, no small multiples): Javed et
 * al. (2010) encontraron empíricamente que, para tareas de COMPARACIÓN
 * LOCAL (leer con precisión qué serie está más arriba/abajo de cuál EN UN
 * INSTANTE dado, o dónde se cruzan), las líneas superpuestas superan a
 * layouts alternativos como series apiladas o small multiples separados.
 * Eso es exactamente lo que T4/T5 piden a nivel de detalle fino -- B1 ya
 * cubre la lectura de overview (escanear las 60 ventanas de un vistazo,
 * detectar zonas "calientes"); B2 cubre la lectura de precisión puntual.
 *
 * EJE X CONTINUO (scaleLinear sobre window_start_sec), a diferencia de la
 * scaleBand discreta de B1 -- acá SÍ tiene sentido una línea continua entre
 * ventanas consecutivas, porque cada serie es una magnitud realmente
 * ordenada y continua en el tiempo (a diferencia del eje de FILAS de B1,
 * que es categórico -- ver justificación de Zacks & Tversky en B1 para por
 * qué ahí NO se usan líneas).
 *
 * HOVER -- guía vertical + tooltip consolidado (mismo patrón que B1,
 * 2026-07-17: Munzner Cap. 6.5.3, Change Blindness -- un solo punto de foco
 * con las 5 modalidades listadas, no 5 tooltips repartidos). Se ubica el
 * punto de tiempo más cercano al cursor (d3.bisector), se dibuja una línea
 * vertical en esa posición y se listan los 5 valores de esa ventana.
 */
export function renderHusformerB2Chart({
    containerId,
    activeTrial,
    attentionData,
    onHoverWindowChange,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-b2-tooltip").remove();

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
        left: 30,
    };

    const svg = d3
        .select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    clipIdCounter += 1;
    const clipId = `husformer-b2-clip-${clipIdCounter}`;

    svg
        .append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("width", Math.max(plotWidth, 0))
        .attr("height", Math.max(plotHeight, 0));

    const plotGroup = svg
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3
        .scaleLinear()
        .domain(d3.extent(windows, (w) => w.window_start_sec))
        .range([0, plotWidth]);

    // Dominio Y dinámico (mismo principio que el dominio de color de B1,
    // Aigner Cap. 4 -- expansión del rango de valores): los 5 valores rondan
    // ~20% con variación moderada, un dominio fijo [0,100] aplastaría la
    // línea contra el medio del panel.
    const allValues = windows.flatMap((w) => MODALITY_KEYS.map((key) => w[key]));
    const [minValue, maxValue] = d3.extent(allValues);
    const yPadding = (maxValue - minValue) * 0.15 || 1;

    const yScale = d3
        .scaleLinear()
        .domain([minValue - yPadding, maxValue + yPadding])
        .range([plotHeight, 0]);

    plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .attr("font-size", "8px")
        .call(
            d3
                .axisBottom(xScale)
                .ticks(6)
                .tickSize(3)
                .tickFormat((sec) => `${Math.round(sec)}s`)
        );

    plotGroup
        .append("g")
        .attr("font-size", "8px")
        .call(
            d3
                .axisLeft(yScale)
                .ticks(4)
                .tickSize(3)
                .tickFormat((pct) => `${Math.round(pct)}%`)
        );

    const linesGroup = plotGroup
        .append("g")
        .attr("clip-path", `url(#${clipId})`);

    MODALITY_KEYS.forEach((modalityKey) => {
        const series = windows.map((w) => ({
            window_start_sec: w.window_start_sec,
            value: w[modalityKey],
        }));

        const seriesLine = d3
            .line()
            .x((d) => xScale(d.window_start_sec))
            .y((d) => yScale(d.value));

        linesGroup
            .append("path")
            .attr("class", "husformer-b2-line")
            .attr("data-modality", modalityKey)
            .attr("fill", "none")
            .attr("stroke", MODALITY_COLORS[modalityKey])
            .attr("stroke-width", 1.6)
            .attr("stroke-dasharray", LINE_DASH_PATTERNS[modalityKey])
            .attr("d", seriesLine(series));

        // Puntos por ventana (2026-07-17, a pedido de Russell -- pensado
        // originalmente como "un puntito verde por modalidad" para poder
        // ubicar/seleccionar una ventana en B2 igual que en B1). Se usa el
        // color DE CADA LÍNEA, no un verde uniforme -- EMG ya es verde en
        // esta paleta (ver MODALITY_COLORS), un punto verde fijo se hubiera
        // confundido con la línea de EMG y, sobre las otras 4 líneas,
        // hubiera competido con su color real en vez de identificarlas.
        // Además de servir como referencia visual de selección, deja en
        // claro que cada serie son 60 MUESTRAS DISCRETAS (una por ventana
        // de 1s), no una señal continua -- un mark de punto en cada dato
        // real, distinto del mark de línea que solo conecta (Munzner
        // Cap. 5, Marks and Channels).
        linesGroup
            .selectAll(`.husformer-b2-point-${modalityKey}`)
            .data(series)
            .enter()
            .append("circle")
            .attr("class", "husformer-b2-point")
            .attr("data-modality", modalityKey)
            .attr("cx", (d) => xScale(d.window_start_sec))
            .attr("cy", (d) => yScale(d.value))
            .attr("r", 1.8)
            .attr("fill", MODALITY_COLORS[modalityKey])
            .style("pointer-events", "none");
    });

    // Guía vertical de hover -- oculta hasta el primer mousemove.
    const hoverLine = plotGroup
        .append("line")
        .attr("class", "husformer-b2-hover-line")
        .attr("y1", 0)
        .attr("y2", plotHeight)
        .attr("stroke", "#111827")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "3,3")
        .style("opacity", 0)
        .style("pointer-events", "none");

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "husformer-b2-tooltip")
        .style("opacity", 0);

    const bisectStartSec = d3.bisector((w) => w.window_start_sec).left;

    function findNearestWindow(hoveredSec) {
        let index = bisectStartSec(windows, hoveredSec);
        index = Math.max(0, Math.min(windows.length - 1, index));

        // Ajusta al vecino más cercano (bisector da el punto de inserción,
        // no necesariamente el más cercano).
        if (
            index > 0
            && Math.abs(windows[index - 1].window_start_sec - hoveredSec)
                < Math.abs(windows[index].window_start_sec - hoveredSec)
        ) {
            index -= 1;
        }

        return windows[index];
    }

    // showGuideAtWindow/clearGuide -- extraídas como funciones reusables
    // (2026-07-17, sincronización bidireccional con B1/B3, a pedido de
    // Russell): dibujan SOLO la guía vertical, sin tooltip -- el tooltip
    // necesita una posición real de mouse para anclarse, que no existe
    // cuando el resaltado viene de otro panel. El mousemove interno sí
    // agrega el tooltip por su cuenta, encima de esto.
    function showGuideAtWindow(activeWindow) {
        hoverLine
            .attr("x1", xScale(activeWindow.window_start_sec))
            .attr("x2", xScale(activeWindow.window_start_sec))
            .style("opacity", 1);
    }

    function clearGuide() {
        hoverLine.style("opacity", 0);
    }

    // Rectángulo transparente que captura mousemove sobre TODO el área de
    // plot -- necesario porque el hover debe funcionar en cualquier punto X,
    // no solo exactamente sobre una línea (a diferencia de hacer hover
    // sobre elementos puntuales como en B1).
    plotGroup
        .append("rect")
        .attr("width", plotWidth)
        .attr("height", plotHeight)
        .attr("fill", "transparent")
        .on("mousemove", function (event) {
            const [mouseX] = d3.pointer(event, this);
            const activeWindow = findNearestWindow(xScale.invert(mouseX));

            showGuideAtWindow(activeWindow);

            const rowsHtml = MODALITY_KEYS
                .map((modalityKey) => `
                    <div class="husformer-b1-tooltip-row">
                        <span style="color:${MODALITY_COLORS[modalityKey]}">●</span>
                        <span>${modalityLabels[modalityKey]}</span>
                        <span>${activeWindow[modalityKey].toFixed(1)}%</span>
                    </div>
                `)
                .join("");

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Tiempo: ${activeWindow.window_start_sec.toFixed(1)}s</strong>
                    ${rowsHtml}
                `)
                .style("left", `${event.pageX + 14}px`)
                .style("top", `${event.pageY - 18}px`);

            if (onHoverWindowChange) {
                onHoverWindowChange(activeWindow.window_index);
            }
        })
        .on("mouseleave", () => {
            clearGuide();
            tooltip.style("opacity", 0);

            if (onHoverWindowChange) {
                onHoverWindowChange(null);
            }
        });

    const windowByIndex = new Map(windows.map((w) => [w.window_index, w]));

    return {
        highlightWindow(windowIndex) {
            const targetWindow = windowByIndex.get(windowIndex);
            if (targetWindow) {
                showGuideAtWindow(targetWindow);
            }
        },
        clearHighlight: clearGuide,
    };
}
