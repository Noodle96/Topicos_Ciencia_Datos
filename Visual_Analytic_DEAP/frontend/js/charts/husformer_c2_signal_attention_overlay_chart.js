import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";
import { extractDuringPhaseSamples, averageChannels } from "./husformer_b3_chart.js";

/**
 * Renderiza C2 -- señal fisiológica real (sin normalizar) y dominancia de
 * atención de esa modalidad, JUXTAPUESTAS (no superpuestas en el mismo eje)
 * en una ventana corta alrededor del punto que se está hovereando en B2
 * (2026-07-22, tercer diseño de C2 -- reemplaza la tabla numérica y la
 * línea de trial completo, ambas descartadas por Russell).
 *
 * Por qué JUXTAPUESTO y no un gráfico de doble eje (superimpose): mismo
 * criterio ya usado en el diseño original de B2/B3 (ver husformer_b3_
 * resumen_implementacion.md) -- superponer dos magnitudes de unidades
 * distintas (µV/µS de la señal real vs. % de dominancia) en un solo eje Y
 * compartido sugeriría visualmente una relación de escala que no existe.
 * Dos mini-gráficos apilados, con el MISMO eje X (tiempo) y una línea guía
 * vertical sincronizada entre ambos, dan la misma posibilidad de comparar
 * "¿coinciden los picos en el tiempo?" sin la trampa del doble eje.
 *
 * Una tarjeta por MODALIDAD activa en B2 (deduplicada -- si hay dos grupos
 * de EEG activos a la vez, ej. Frontal + Izquierdo, cuentan como una sola
 * modalidad "EEG" acá, promediando sus canales reales juntos).
 *
 * Responde directamente a T5 ("relacionar picos o cambios abruptos en la
 * atención con eventos visibles en la señal original") y a G3 -- ahora
 * anclado a una acción sobre B2 (hover), no sobre B1.
 */
const WINDOW_RADIUS_SECONDS = 3;

function buildTimeWindow(hoveredWindowIndex) {
    return {
        start: Math.max(0, hoveredWindowIndex - WINDOW_RADIUS_SECONDS),
        end: hoveredWindowIndex + WINDOW_RADIUS_SECONDS + 1,
    };
}

function renderMiniLineChart({ card, samples, xDomain, yDomain, color, width, height, hoveredTime, valueFormatter }) {
    const margin = { top: 4, right: 8, bottom: 14, left: 30 };
    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    const svg = card.append("svg").attr("width", width).attr("height", height);

    const plotGroup = svg.append("g").attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3.scaleLinear().domain(xDomain).range([0, Math.max(plotWidth, 0)]);
    const yScale = d3.scaleLinear().domain(yDomain).nice().range([Math.max(plotHeight, 0), 0]);

    plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .attr("font-size", "7px")
        .call(d3.axisBottom(xScale).ticks(4).tickSize(3).tickFormat((sec) => `${sec.toFixed(0)}s`));

    plotGroup
        .append("g")
        .attr("font-size", "7px")
        .call(d3.axisLeft(yScale).ticks(3).tickSize(3).tickFormat(valueFormatter));

    if (samples.length > 0) {
        const line = d3
            .line()
            .x((d) => xScale(d.time))
            .y((d) => yScale(d.value));

        plotGroup
            .append("path")
            .datum(samples)
            .attr("fill", "none")
            .attr("stroke", color)
            .attr("stroke-width", 1.4)
            .attr("d", line);
    } else {
        plotGroup
            .append("text")
            .attr("x", plotWidth / 2)
            .attr("y", plotHeight / 2)
            .attr("text-anchor", "middle")
            .attr("font-size", "8px")
            .attr("fill", "#9ca3af")
            .text("Sin datos en esta ventana");
    }

    // Línea guía vertical -- posición del hover actual en B2, sincronizada
    // entre las dos mini-gráficas de la misma tarjeta (mismo xScale, mismo
    // xDomain) y entre tarjetas de distinta modalidad (mismo hoveredTime).
    plotGroup
        .append("line")
        .attr("x1", xScale(hoveredTime))
        .attr("x2", xScale(hoveredTime))
        .attr("y1", 0)
        .attr("y2", plotHeight)
        .attr("stroke", "#111827")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "3,3");
}

function renderModalityCard({ container, modality, rawSignalResponse, b1Windows, timeWindow, hoveredTime, chartHeight, cardWidth }) {
    const card = container
        .append("div")
        .attr("class", "husformer-c2-card")
        // Ancho FIJO explícito, calculado de antemano en base al total de
        // tarjetas (ver bug corregido en renderHusformerC2SignalAttentionChart)
        // -- no se deja que cada tarjeta mida su propio clientWidth.
        .style("width", `${cardWidth}px`)
        .style("flex", "0 0 auto");

    card
        .append("div")
        .attr("class", "husformer-c2-card-label")
        .style("color", modality.color)
        .text(modality.label);

    // -- Gráfica 1: señal real, sin normalizar --
    const averaged = averageChannels(rawSignalResponse, modality.channels);
    const rawSamples = averaged.filter(
        (sample) => sample.time >= timeWindow.start && sample.time <= timeWindow.end
    );
    const rawDomain = rawSamples.length > 0
        ? d3.extent(rawSamples, (d) => d.value)
        : [0, 1];

    card.append("div").attr("class", "husformer-c2-mini-label").text("Señal real");
    renderMiniLineChart({
        card,
        samples: rawSamples,
        xDomain: [timeWindow.start, timeWindow.end],
        yDomain: rawDomain,
        color: modality.color,
        width: cardWidth,
        height: chartHeight,
        hoveredTime,
        valueFormatter: (v) => v.toFixed(1),
    });

    // -- Gráfica 2: dominancia de atención de esta modalidad --
    const dominanceSamples = b1Windows
        .filter((w) => w.window_start_sec >= timeWindow.start && w.window_start_sec <= timeWindow.end)
        .map((w) => ({ time: w.window_start_sec, value: w[modality.modalityKey] }));

    card.append("div").attr("class", "husformer-c2-mini-label").text("% Dominancia de atención");
    renderMiniLineChart({
        card,
        samples: dominanceSamples,
        xDomain: [timeWindow.start, timeWindow.end],
        yDomain: [0, 100],
        color: "#374151",
        width: cardWidth,
        height: chartHeight,
        hoveredTime,
        valueFormatter: (v) => `${v.toFixed(0)}%`,
    });
}

export function renderHusformerC2SignalAttentionChart({
    containerId,
    activeTrial,
    hoveredWindowIndex,
    activeModalities,
    rawSignalResponse,
    b1Windows,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    if (!activeTrial) {
        container.innerHTML = '<div class="husformer-b1-empty">Selecciona un trial en Vista A</div>';
        return;
    }

    if (hoveredWindowIndex === null || hoveredWindowIndex === undefined) {
        container.innerHTML = '<div class="husformer-b1-empty">Pasá el mouse sobre la señal en B2</div>';
        return;
    }

    if (!activeModalities || activeModalities.length === 0) {
        container.innerHTML = '<div class="husformer-b1-empty">Elegí una o más señales en B2 para comparar.</div>';
        return;
    }

    if (!rawSignalResponse || !b1Windows) {
        container.innerHTML = '<div class="husformer-b1-empty">Cargando...</div>';
        return;
    }

    const timeWindow = buildTimeWindow(hoveredWindowIndex);
    const hoveredTime = hoveredWindowIndex + 0.5; // centro de la ventana de 1s

    // Alto de cada mini-gráfico -- CALCULADO a partir del alto real del
    // panel (2026-07-22, a pedido de Russell: antes era un valor fijo de
    // 70px, dejaba mucho espacio vacío sin usar cuando el panel es grande).
    // Cada tarjeta tiene: label de modalidad + 2×(mini-label + gráfico) +
    // gaps -- se descuenta ese espacio fijo y el resto se reparte entre las
    // DOS gráficas por igual.
    const containerHeight = container.clientHeight || 240;
    const FIXED_LABELS_HEIGHT = 20 /* label de modalidad */ + 2 * 12 /* mini-labels */ + 3 * 4 /* gaps */ + 20 /* padding vertical */;
    const chartHeight = Math.max(60, (containerHeight - FIXED_LABELS_HEIGHT) / 2);

    // Ancho de cada tarjeta -- CALCULADO UNA SOLA VEZ, ANTES de crear
    // ninguna tarjeta (bug corregido 2026-07-22: medir clientWidth tarjeta
    // por tarjeta, DENTRO del loop, daba un ancho viejo/incorrecto a las
    // primeras tarjetas -- se medían cuando eran las únicas en la fila,
    // antes de que el resto empujara el layout real, y esas SVG quedaban
    // con un ancho fijo en píxeles más grande que su tarjeta ya achicada --
    // eso es lo que se veía como gráficas superpuestas). Repartir el ancho
    // disponible en partes iguales de antemano, respetando el mismo rango
    // min/max-width que ya define .husformer-c2-card en CSS.
    const containerWidth = container.clientWidth || 600;
    const ROW_PADDING = 20; // 10px a cada lado, .husformer-c2-scroll-row
    const CARD_GAP = 18;
    const CARD_MIN_WIDTH = 180;
    const CARD_MAX_WIDTH = 420;
    const totalGaps = CARD_GAP * Math.max(0, activeModalities.length - 1);
    const rawCardWidth = (containerWidth - ROW_PADDING - totalGaps) / activeModalities.length;
    const cardWidth = Math.min(CARD_MAX_WIDTH, Math.max(CARD_MIN_WIDTH, rawCardWidth));

    const scrollRow = d3
        .select(container)
        .append("div")
        .attr("class", "husformer-c2-scroll-row");

    activeModalities.forEach((modality) => {
        renderModalityCard({ container: scrollRow, modality, rawSignalResponse, b1Windows, timeWindow, hoveredTime, chartHeight, cardWidth });
    });
}
