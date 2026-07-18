import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

let clipIdCounter = 0;

/**
 * Extrae, de la respuesta de /api/trial-signals, los puntos de UN canal
 * reubicados en el mismo eje temporal que usan B1/B2 (relativo al inicio
 * de la fase "During", no al registro completo).
 *
 * ALINEACIÓN CRÍTICA (ver husformer_b3_resumen_implementacion.md para el
 * detalle completo): /api/trial-signals devuelve tiempos relativos al
 * registro completo del participante (incluye Before/During/After);
 * window_start_sec de la atención es relativo solo al inicio de During.
 * Se corrige restando el `start` de la fase "During" a cada timestamp.
 */
function extractDuringPhaseSamples(signalResponse, channelName) {
    const duringPhase = signalResponse.phases.find((phase) => phase.name === "During");

    if (!duringPhase) {
        return [];
    }

    const rawSamples = signalResponse.signals[channelName] ?? [];

    return rawSamples
        .map((sample) => ({
            time: sample.time - duringPhase.start,
            value: sample.value,
        }))
        .filter((sample) => (
            sample.time >= 0
            && sample.time <= (duringPhase.end - duringPhase.start)
            && sample.value !== null
        ));
}

/**
 * Promedia varios canales punto a punto (mismo índice temporal, ya que
 * /api/trial-signals downsamplea todos los canales de un mismo trial con
 * el mismo esquema -- mismo total_points, mismo max_points -- así que
 * quedan alineados sin necesitar interpolación).
 */
function averageChannels(signalResponse, channelNames) {
    const perChannelSamples = channelNames.map(
        (channelName) => extractDuringPhaseSamples(signalResponse, channelName)
    );

    const validSamples = perChannelSamples.filter((samples) => samples.length > 0);

    if (validSamples.length === 0) {
        return [];
    }

    const pointCount = Math.min(...validSamples.map((samples) => samples.length));
    const averaged = [];

    for (let index = 0; index < pointCount; index += 1) {
        const time = validSamples[0][index].time;
        const mean = d3.mean(validSamples, (samples) => samples[index].value);
        averaged.push({ time, value: mean });
    }

    return averaged;
}

/**
 * Normaliza una serie a z-score (media 0, desvío 1) -- necesario para
 * poder superponer señales de unidades físicas distintas (µV de EEG, µS de
 * GSR, etc.) en el mismo eje Y sin que una magnitud arbitraria del sensor
 * distorsione la comparación visual.
 */
function zScoreNormalize(samples) {
    const values = samples.map((d) => d.value);
    const mean = d3.mean(values);
    const std = d3.deviation(values) || 1;

    return samples.map((d) => ({
        time: d.time,
        value: (d.value - mean) / std,
    }));
}

/**
 * Dado el JSON crudo de /api/trial-signals y la lista de grupos
 * seleccionados (ver husformer_b3_channel_groups.js), arma las series
 * finales: una por grupo, promediada sobre sus canales y normalizada.
 */
export function buildB3Series(signalResponse, selectedGroups) {
    return selectedGroups
        .map((group) => {
            const averaged = averageChannels(signalResponse, group.channels);

            if (averaged.length === 0) {
                return null;
            }

            return {
                id: group.id,
                label: group.label,
                color: group.color,
                samples: zScoreNormalize(averaged),
            };
        })
        .filter((series) => series !== null);
}

/**
 * Renderiza B3: N señales normalizadas superpuestas (una por grupo
 * seleccionado), a lo largo de toda la fase During del trial.
 *
 * REDISEÑO 2026-07-17 (a pedido de Russell, tras evaluación crítica): la
 * versión anterior apilaba un panel de atención (B2 reutilizado) debajo de
 * la señal cruda -- redundante, porque B1/B2 ya está visible al lado en la
 * misma fila del CMV todo el tiempo (Eyes Beat Memory, Munzner Cap. 6.5,
 * ya se cumple con los paneles juxtapuestos, no hace falta repetir el
 * contenido DENTRO de B3). B3 ahora usa todo su espacio para comparar
 * varias señales crudas entre sí, normalizadas.
 *
 * Colores compartidos con el panel de atención de B1/B2 (ver
 * husformer_b3_channel_groups.js, getSignalColor) -- misma justificación
 * de "share encoding" ya usada ahí.
 */
export function renderHusformerB3Chart({
    containerId,
    activeTrial,
    seriesList,
    initialZoomTransform,
    onZoomChange,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-b3-tooltip").remove();

    if (!activeTrial) {
        container.innerHTML = '<div class="husformer-b1-empty">Selecciona un trial en Vista A</div>';
        return;
    }

    if (!seriesList) {
        container.innerHTML = '<div class="husformer-b1-empty">Cargando...</div>';
        return;
    }

    if (seriesList.length === 0) {
        container.innerHTML = '<div class="husformer-b1-empty">Elegí una o más señales arriba para comparar.</div>';
        return;
    }

    const width = container.clientWidth || 360;
    const height = container.clientHeight || 220;

    const margin = {
        top: 8,
        right: 10,
        bottom: 18,
        left: 34,
    };

    const svg = d3
        .select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    clipIdCounter += 1;
    const clipId = `husformer-b3-clip-${clipIdCounter}`;

    svg
        .append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("width", Math.max(plotWidth, 0))
        .attr("height", Math.max(plotHeight, 0));

    const plotGroup = svg
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const allSamples = seriesList.flatMap((series) => series.samples);

    const xScale = d3
        .scaleLinear()
        .domain(d3.extent(allSamples, (d) => d.time))
        .range([0, plotWidth]);

    // Dominio Y simétrico alrededor de 0 (z-score) -- todas las señales ya
    // están en la misma escala normalizada, así que un solo eje Y compartido
    // es válido y comparable entre ellas.
    const yExtent = d3.extent(allSamples, (d) => d.value);
    const yAbsMax = Math.max(Math.abs(yExtent[0]), Math.abs(yExtent[1]), 1);

    const yScale = d3
        .scaleLinear()
        .domain([-yAbsMax, yAbsMax])
        .nice()
        .range([plotHeight, 0]);

    const xAxisGroup = plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .attr("font-size", "8px")
        .call(d3.axisBottom(xScale).ticks(6).tickSize(3).tickFormat((sec) => `${Math.round(sec)}s`));

    plotGroup
        .append("g")
        .attr("font-size", "8px")
        .call(d3.axisLeft(yScale).ticks(4).tickSize(3));

    const linesGroup = plotGroup
        .append("g")
        .attr("clip-path", `url(#${clipId})`);

    const linePaths = seriesList.map((series) => (
        linesGroup
            .append("path")
            .attr("fill", "none")
            .attr("stroke", series.color)
            .attr("stroke-width", 1.4)
    ));

    // currentXScale es MUTABLE -- arranca igual a xScale, y se reemplaza por
    // transform.rescaleX(xScale) en cada evento de zoom (ver zoomBehavior
    // más abajo). El eje Y NUNCA se reescala -- ver docstring del módulo,
    // Munzner Cap. 11: reescalar Y dinámicamente podría hacer parecer que
    // una señal "creció" cuando en realidad solo cambió la escala visible.
    let currentXScale = xScale;

    function drawLines() {
        const lineGenerator = d3
            .line()
            .x((d) => currentXScale(d.time))
            .y((d) => yScale(d.value));

        seriesList.forEach((series, index) => {
            linePaths[index].attr("d", lineGenerator(series.samples));
        });
    }

    drawLines();

    // Guía vertical + tooltip consolidado (mismo patrón que B1/B2, Munzner
    // Cap. 6.5.3 Change Blindness): un solo punto de foco con TODAS las
    // señales seleccionadas listadas, no una por serie.
    const hoverLine = plotGroup
        .append("line")
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
        .attr("class", "husformer-b3-tooltip")
        .style("opacity", 0);

    const bisectTime = d3.bisector((d) => d.time).left;

    function showTooltip(event, hoveredTime) {
        const rowsHtml = seriesList
            .map((series) => {
                let index = bisectTime(series.samples, hoveredTime);
                index = Math.max(0, Math.min(series.samples.length - 1, index));
                const point = series.samples[index];

                return `
                    <div class="husformer-b1-tooltip-row">
                        <span style="color:${series.color}">●</span>
                        <span>${series.label}</span>
                        <span>${point.value.toFixed(2)}</span>
                    </div>
                `;
            })
            .join("");

        const referenceTime = seriesList[0].samples[
            Math.max(0, Math.min(
                seriesList[0].samples.length - 1,
                bisectTime(seriesList[0].samples, hoveredTime)
            ))
        ].time;

        hoverLine
            .attr("x1", currentXScale(referenceTime))
            .attr("x2", currentXScale(referenceTime))
            .style("opacity", 1);

        tooltip
            .style("opacity", 1)
            .html(`
                <strong>Tiempo: ${referenceTime.toFixed(1)}s (z-score)</strong>
                ${rowsHtml}
            `)
            .style("left", `${event.pageX + 14}px`)
            .style("top", `${event.pageY - 18}px`);
    }

    const overlay = plotGroup
        .append("rect")
        .attr("width", plotWidth)
        .attr("height", plotHeight)
        .attr("fill", "transparent")
        .attr("cursor", "grab")
        .on("mousemove", function (event) {
            const [mouseX] = d3.pointer(event, this);
            showTooltip(event, currentXScale.invert(mouseX));
        })
        .on("mouseleave", () => {
            hoverLine.style("opacity", 0);
            tooltip.style("opacity", 0);
        });

    // ZOOM/PAN SOLO EN X (2026-07-17, a pedido de Russell) -- rueda del
    // mouse para zoom, arrastre para pan, mismo mecanismo que ya usan
    // A1/A2 (consistencia de interacción en todo el sistema, no un gesto
    // nuevo por panel). scaleExtent hasta 20x -- suficiente para acercarse
    // a un tramo de un par de segundos dentro de los ~60s del trial, sin
    // perder de vista que sigue siendo el mismo trial.
    const zoomBehavior = d3
        .zoom()
        .scaleExtent([1, 20])
        .translateExtent([[0, 0], [plotWidth, plotHeight]])
        .extent([[0, 0], [plotWidth, plotHeight]])
        .on("zoom", (event) => {
            const transform = event.transform;
            currentXScale = transform.rescaleX(xScale);

            xAxisGroup.call(
                d3.axisBottom(currentXScale).ticks(6).tickSize(3).tickFormat((sec) => `${Math.round(sec)}s`)
            );

            drawLines();
            hoverLine.style("opacity", 0);
            tooltip.style("opacity", 0);

            if (onZoomChange) {
                onZoomChange(transform);
            }
        });

    // Doble-click resetea el zoom -- d3.zoom() por defecto usa dblclick
    // para ACERCAR (2x), hay que desactivar ese comportamiento primero
    // (".on('dblclick.zoom', null)") antes de poder engancharle nuestro
    // propio handler de reset.
    svg.call(zoomBehavior);
    svg.on("dblclick.zoom", null);
    overlay.on("dblclick", () => {
        svg.transition().duration(300).call(zoomBehavior.transform, d3.zoomIdentity);
    });

    // Reaplica el zoom persistido de una interacción anterior (mismo fix
    // que ya existe en A1/B1: sin esto, cualquier re-render -- resize,
    // cambio de selección de señales -- perdería el zoom actual). Se
    // dispara el mismo handler "zoom" de arriba de forma síncrona.
    if (initialZoomTransform) {
        svg.call(zoomBehavior.transform, initialZoomTransform);
    }
}
