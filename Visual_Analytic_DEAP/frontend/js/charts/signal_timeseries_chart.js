import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";


export const CHANNEL_COLORS = {
    Fp1: "#2563eb",
    AF3: "#1d4ed8",
    F7: "#1e40af",
    F3: "#3b82f6",
    FC1: "#60a5fa",
    FC5: "#93c5fd",
    T7: "#0284c7",
    C3: "#0ea5e9",
    CP1: "#38bdf8",
    CP5: "#7dd3fc",
    P7: "#0369a1",
    P3: "#075985",
    PO3: "#0c4a6e",
    O1: "#172554",

    Fp2: "#dc2626",
    AF4: "#b91c1c",
    F8: "#991b1b",
    F4: "#ef4444",
    FC2: "#f87171",
    FC6: "#fca5a5",
    T8: "#e11d48",
    C4: "#f43f5e",
    CP2: "#fb7185",
    CP6: "#fda4af",
    P8: "#be123c",
    P4: "#9f1239",
    PO4: "#881337",
    O2: "#7f1d1d",

    Fz: "#16a34a",
    Cz: "#15803d",
    Pz: "#166534",
    Oz: "#14532d",

    EXG1: "#9333ea",
    EXG2: "#7e22ce",
    EXG3: "#6b21a8",
    EXG4: "#581c87",

    EXG5: "#ea580c",
    EXG6: "#c2410c",
    EXG7: "#9a3412",
    EXG8: "#7c2d12",

    GSR1: "#0f766e",
    Resp: "#0891b2",
    Plet: "#0d9488",
    Temp: "#7c3aed",
};

let currentXDomain = null;
let lastRenderConfig = null;

/**
 * Restaura el dominio temporal completo del trial y vuelve a renderizar
 * la vista de señales usando la última configuración disponible.
 */
function resetZoom() {
    currentXDomain = null;

    if (lastRenderConfig) {
        renderSignalTimeseriesChart(lastRenderConfig);
    }
}

/**
 * Normaliza una señal usando z-score.
 */
function normalizeSamples(samples) {
    const values = samples.map((sample) => sample.value);

    const mean = d3.mean(values);
    const deviation = d3.deviation(values);

    if (!deviation || deviation === 0) {
        return samples.map((sample) => ({
            time: sample.time,
            value: 0,
        }));
    }

    return samples.map((sample) => ({
        time: sample.time,
        value: (sample.value - mean) / deviation,
    }));
}


/**
 * Renderiza las señales del trial seleccionado.
 *
 * Modo RAW:
 * - cada canal se dibuja en su propio track.
 *
 * Modo NORMALIZED:
 * - las señales se normalizan con z-score
 * - y se muestran en tracks comparables.
 */
export function renderSignalTimeseriesChart({
    containerId,
    signalData,
    activeChannels,
    normalizeSignals,
}) {
    const container = document.getElementById(containerId);

    container.innerHTML = "";
    lastRenderConfig = {
        containerId,
        signalData,
        activeChannels,
        normalizeSignals,
    };

    const controls = document.createElement("div");
    controls.className = "signal-zoom-controls";

    const resetButton = document.createElement("button");
    resetButton.textContent = "Reset Zoom";
    resetButton.className = "reset-zoom-button";
    resetButton.addEventListener("click", resetZoom);

    controls.appendChild(resetButton);
    container.appendChild(controls);

    if (!signalData || activeChannels.length === 0) {
        container.innerHTML = `
            <p>
                Selecciona un trial y al menos un canal.
            </p>
        `;
        return;
    }

    if (normalizeSignals) {
        renderNormalizedOverlayChart({
            container,
            signalData,
            activeChannels,
        });

        return;
    }

    activeChannels.forEach((channel) => {
        const rawSamples = signalData.signals[channel] ?? [];

        if (rawSamples.length === 0) {
            return;
        }

        renderSingleChannelTrack({
            container,
            channel,
            samples: rawSamples,
            phases: signalData.phases,
            normalizeSignals,
            fullXDomain: [
                signalData.phases[0].start,
                signalData.phases[signalData.phases.length - 1].end,
            ],
        });
    });
}


function renderNormalizedOverlayChart({
    container,
    signalData,
    activeChannels,
}) {
    const chartContainer = document.createElement("div");
    chartContainer.className = "normalized-overlay-chart";

    container.appendChild(chartContainer);

    const width = chartContainer.clientWidth || container.clientWidth;
    const height = 430;

    const margin = {
        top: 24,
        right: 30,
        bottom: 38,
        left: 58,
    };

    const svg = d3
        .select(chartContainer)
        .append("svg")
        .attr("class", "signal-track-svg")
        .attr("width", width)
        .attr("height", height);

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    const plotGroup = svg
        .append("g")
        .attr(
            "transform",
            `translate(${margin.left}, ${margin.top})`
        );

    const fullXDomain = [
        signalData.phases[0].start,
        signalData.phases[signalData.phases.length - 1].end,
    ];

    const xScale = d3
        .scaleLinear()
        .domain(currentXDomain ?? fullXDomain)
        .range([0, plotWidth]);

    const yScale = d3
        .scaleLinear()
        .domain([-4, 4])
        .range([plotHeight, 0]);

    renderPhaseBackgrounds({
        plotGroup,
        phases: signalData.phases,
        xScale,
        plotHeight,
    });

    plotGroup
        .append("g")
        .attr(
            "transform",
            `translate(0, ${plotHeight})`
        )
        .call(d3.axisBottom(xScale).ticks(8));

    plotGroup
        .append("g")
        .call(d3.axisLeft(yScale).ticks(6));

    const lineGenerator = d3
        .line()
        .x((sample) => xScale(sample.time))
        .y((sample) => yScale(sample.value));

    activeChannels.forEach((channel) => {
        const rawSamples = signalData.signals[channel] ?? [];

        if (rawSamples.length === 0) {
            return;
        }

        const normalizedSamples = normalizeSamples(rawSamples);

        plotGroup
            .append("path")
            .datum(normalizedSamples)
            .attr("fill", "none")
            .attr("stroke", CHANNEL_COLORS[channel] ?? "#111827")
            .attr("stroke-width", 1.5)
            .attr("opacity", 0.85)
            .attr("d", lineGenerator);
    });

    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", 14)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("font-weight", "bold")
        .text("Normalized overlay view (z-score)");

    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", height - 4)
        .attr("text-anchor", "middle")
        .attr("font-size", 10)
        .attr("fill", "#374151")
        .text("Tiempo relativo del trial (s)");

    renderOverlayLegend({
        svg,
        activeChannels,
        width,
    });

    addBrushZoom({
        plotGroup,
        xScale,
        plotWidth,
        plotHeight,
    });
}

function renderOverlayLegend({
    svg,
    activeChannels,
    width,
}) {
    const legendGroup = svg
        .append("g")
        .attr(
            "transform",
            `translate(${width - 150}, 24)`
        );

    activeChannels.forEach((channel, index) => {
        const itemGroup = legendGroup
            .append("g")
            .attr(
                "transform",
                `translate(0, ${index * 18})`
            );

        itemGroup
            .append("line")
            .attr("x1", 0)
            .attr("x2", 18)
            .attr("y1", 0)
            .attr("y2", 0)
            .attr("stroke", CHANNEL_COLORS[channel] ?? "#111827")
            .attr("stroke-width", 2);

        itemGroup
            .append("text")
            .attr("x", 24)
            .attr("y", 4)
            .attr("font-size", 11)
            .attr("fill", CHANNEL_COLORS[channel] ?? "#111827")
            .text(channel);
    });
}



/**
 * Renderiza un track individual para un canal.
 */
function renderSingleChannelTrack({
    container,
    channel,
    samples,
    phases,
    normalizeSignals,
    fullXDomain,
}) {
    const trackWrapper = document.createElement("div");
    trackWrapper.className = "signal-track";

    const title = document.createElement("div");
    title.className = "signal-track-title";
    title.style.color = CHANNEL_COLORS[channel] ?? "#111827";
    title.textContent = normalizeSignals
        ? `${channel} | z-score`
        : `${channel} | raw`;

    const chartContainer = document.createElement("div");
    chartContainer.className = "signal-track-chart";

    trackWrapper.appendChild(title);
    trackWrapper.appendChild(chartContainer);
    container.appendChild(trackWrapper);

    const width = chartContainer.clientWidth || container.clientWidth;
    const height = 150;

    const margin = {
        top: 12,
        right: 24,
        bottom: 28,
        left: 58,
    };

    const svg = d3
        .select(chartContainer)
        .append("svg")
        .attr("class", "signal-track-svg")
        .attr("width", width)
        .attr("height", height);

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    const plotGroup = svg
        .append("g")
        .attr(
            "transform",
            `translate(${margin.left}, ${margin.top})`
        );


    const xScale = d3
        .scaleLinear()
        .domain(currentXDomain ?? fullXDomain)
        .range([0, plotWidth]);

    const values = samples.map((sample) => sample.value);

    const extent = d3.extent(values);

    const padding = ((extent[1] ?? 1) - (extent[0] ?? -1)) * 0.12 || 1;

    const yScale = d3
        .scaleLinear()
        .domain([
            (extent[0] ?? -1) - padding,
            (extent[1] ?? 1) + padding,
        ])
        .range([plotHeight, 0]);

    renderPhaseBackgrounds({
        plotGroup,
        phases,
        xScale,
        plotHeight,
    });

    plotGroup
        .append("g")
        .attr(
            "transform",
            `translate(0, ${plotHeight})`
        )
        .call(
            d3
                .axisBottom(xScale)
                .ticks(8)
        );

    plotGroup
        .append("g")
        .call(
            d3
                .axisLeft(yScale)
                .ticks(4)
        );

    const lineGenerator = d3
        .line()
        .x((sample) => xScale(sample.time))
        .y((sample) => yScale(sample.value));

    plotGroup
        .append("path")
        .datum(samples)
        .attr("fill", "none")
        .attr("stroke", CHANNEL_COLORS[channel] ?? "#111827")
        .attr("stroke-width", 1.5)
        .attr("opacity", 0.95)
        .attr("d", lineGenerator);

    addBrushZoom({
        plotGroup,
        xScale,
        plotWidth,
        plotHeight,
    });

    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", height - 4)
        .attr("text-anchor", "middle")
        .attr("font-size", 10)
        .attr("fill", "#374151")
        .text("Tiempo relativo del trial (s)");
}


/**
 * Dibuja los fondos suaves Before / During / After.
 */
function renderPhaseBackgrounds({
    plotGroup,
    phases,
    xScale,
    plotHeight,
}) {
    phases.forEach((phase) => {
        const phaseColor =
            phase.name === "Before"
                ? "#dbeafe"
                : phase.name === "During"
                ? "#fef3c7"
                : "#dcfce7";

        plotGroup
            .append("rect")
            .attr("x", xScale(phase.start))
            .attr("y", 0)
            .attr(
                "width",
                xScale(phase.end) - xScale(phase.start)
            )
            .attr("height", plotHeight)
            .attr("fill", phaseColor)
            .attr("opacity", 0.45);

        plotGroup
            .append("text")
            .attr(
                "x",
                (xScale(phase.start) + xScale(phase.end)) / 2
            )
            .attr("y", 12)
            .attr("text-anchor", "middle")
            .attr("font-size", 10)
            .attr("font-weight", "bold")
            .attr("fill", "#374151")
            .text(phase.name);
    });
}


function addBrushZoom({
    plotGroup,
    xScale,
    plotWidth,
    plotHeight,
}) {
    const brush = d3
        .brushX()
        .extent([
            [0, 0],
            [plotWidth, plotHeight],
        ])
        .on("end", (event) => {
            if (!event.selection) {
                return;
            }

            const [x0, x1] = event.selection;

            const selectedStart = xScale.invert(x0);
            const selectedEnd = xScale.invert(x1);

            if (Math.abs(selectedEnd - selectedStart) < 0.2) {
                return;
            }

            currentXDomain = [
                selectedStart,
                selectedEnd,
            ];

            if (lastRenderConfig) {
                renderSignalTimeseriesChart(lastRenderConfig);
            }
        });

    plotGroup
        .append("g")
        .attr("class", "zoom-brush")
        .call(brush);
}