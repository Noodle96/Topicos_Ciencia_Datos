import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

import {
    CHANNEL_COLORS,
} from "./signal_timeseries_chart.js";


const MAX_VISUAL_POINTS = 1200;

let currentXDomain = null;
let lastRenderConfig = null;


function normalizeValues(values) {
    const mean = d3.mean(values);
    const deviation = d3.deviation(values);

    if (!deviation || deviation === 0) {
        return values.map(() => 0);
    }

    return values.map((value) => (value - mean) / deviation);
}


function downsampleSamples(samples, maxPoints = MAX_VISUAL_POINTS) {
    if (samples.length <= maxPoints) {
        return samples;
    }

    const step = Math.ceil(samples.length / maxPoints);

    return samples.filter((_, index) => index % step === 0);
}


function resetH2TimeseriesZoom() {
    currentXDomain = null;

    if (lastRenderConfig) {
        renderH2TimeseriesPairChart(lastRenderConfig);
    }
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

            if (Math.abs(selectedEnd - selectedStart) < 0.5) {
                return;
            }

            currentXDomain = [
                selectedStart,
                selectedEnd,
            ];

            if (lastRenderConfig) {
                renderH2TimeseriesPairChart(lastRenderConfig);
            }
        });

    plotGroup
        .append("g")
        .attr("class", "zoom-brush")
        .call(brush);
}


export function renderH2TimeseriesPairChart({
    containerId,
    pairData,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    lastRenderConfig = {
        containerId,
        pairData,
    };

    if (!pairData || !pairData.times) {
        container.innerHTML = `
            <p>
                Select a relation to load the temporal explorer.
            </p>
        `;
        return;
    }

    const controls = document.createElement("div");
    controls.className = "signal-zoom-controls";

    const resetButton = document.createElement("button");
    resetButton.textContent = "Reset Zoom";
    resetButton.className = "reset-zoom-button";
    resetButton.addEventListener("click", resetH2TimeseriesZoom);

    controls.appendChild(resetButton);
    container.appendChild(controls);

    const chartContainer = document.createElement("div");
    chartContainer.className = "h2-timeseries-chart-area";
    container.appendChild(chartContainer);

    const width = chartContainer.clientWidth || container.clientWidth || 520;
    const height = Math.max(
        240,
        (container.clientHeight || 320) - 38
    );

    const margin = {
        top: 34,
        right: 30,
        bottom: 42,
        left: 54,
    };

    const svg = d3
        .select(chartContainer)
        .append("svg")
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

    const relativeTimes = pairData.times.map(
        (time) => time - pairData.times[0]
    );

    const channelAValues = normalizeValues(pairData.channel_a_values);
    const channelBValues = normalizeValues(pairData.channel_b_values);

    const channelASamplesFull = relativeTimes.map((time, index) => ({
        time,
        value: channelAValues[index],
    }));

    const channelBSamplesFull = relativeTimes.map((time, index) => ({
        time,
        value: channelBValues[index],
    }));

    const fullXDomain = d3.extent(relativeTimes);
    const xDomain = currentXDomain ?? fullXDomain;

    const visibleChannelASamples = channelASamplesFull.filter(
        (sample) => sample.time >= xDomain[0] && sample.time <= xDomain[1]
    );

    const visibleChannelBSamples = channelBSamplesFull.filter(
        (sample) => sample.time >= xDomain[0] && sample.time <= xDomain[1]
    );

    const channelASamples = downsampleSamples(visibleChannelASamples);
    const channelBSamples = downsampleSamples(visibleChannelBSamples);

    const xScale = d3
        .scaleLinear()
        .domain(xDomain)
        .range([0, plotWidth]);

    const yScale = d3
        .scaleLinear()
        .domain([-4, 4])
        .range([plotHeight, 0]);

    plotGroup
        .append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", plotWidth)
        .attr("height", plotHeight)
        .attr("fill", "#fef3c7")
        .attr("opacity", 0.35);

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

    plotGroup
        .append("path")
        .datum(channelASamples)
        .attr("fill", "none")
        .attr("stroke", CHANNEL_COLORS[pairData.channel_a] ?? "#2563eb")
        .attr("stroke-width", 1.6)
        .attr("opacity", 0.9)
        .attr("d", lineGenerator);

    plotGroup
        .append("path")
        .datum(channelBSamples)
        .attr("fill", "none")
        .attr("stroke", CHANNEL_COLORS[pairData.channel_b] ?? "#0f766e")
        .attr("stroke-width", 1.6)
        .attr("opacity", 0.9)
        .attr("d", lineGenerator);

    const correlationText =
        pairData.correlation === null
            ? "N/A"
            : pairData.correlation.toFixed(4);

    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", 16)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("font-weight", "bold")
        .text(
            `${pairData.channel_a} ↔ ${pairData.channel_b} | Pearson: ${correlationText}`
        );

    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", height - 6)
        .attr("text-anchor", "middle")
        .attr("font-size", 10)
        .attr("fill", "#374151")
        .text("Time during stimulus (s)");

    const legend = svg
        .append("g")
        .attr(
            "transform",
            `translate(${margin.left + 10}, ${margin.top + 10})`
        );

    const legendItems = [
        {
            label: `${pairData.channel_a} | z-score`,
            color: CHANNEL_COLORS[pairData.channel_a] ?? "#2563eb",
        },
        {
            label: `${pairData.channel_b} | z-score`,
            color: CHANNEL_COLORS[pairData.channel_b] ?? "#0f766e",
        },
    ];

    legend
        .selectAll(".h2-timeseries-legend-item")
        .data(legendItems)
        .enter()
        .append("g")
        .attr("class", "h2-timeseries-legend-item")
        .attr("transform", (_, index) => `translate(0, ${index * 18})`)
        .each(function (item) {
            const group = d3.select(this);

            group
                .append("line")
                .attr("x1", 0)
                .attr("x2", 18)
                .attr("y1", 0)
                .attr("y2", 0)
                .attr("stroke", item.color)
                .attr("stroke-width", 2);

            group
                .append("text")
                .attr("x", 24)
                .attr("y", 4)
                .attr("font-size", 11)
                .attr("fill", item.color)
                .text(item.label);
        });

    addBrushZoom({
        plotGroup,
        xScale,
        plotWidth,
        plotHeight,
    });
}