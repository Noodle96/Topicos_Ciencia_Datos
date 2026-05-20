import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

import {
    CHANNEL_COLORS,
} from "./signal_timeseries_chart.js";


const PHASES = [
    "Before",
    "During",
    "After",
];

const METRICS = [
    "mean",
    "std",
    "rms",
    "min",
    "max",
];

const tooltip = d3
    .select("body")
    .append("div")
    .attr("class", "summary-tooltip")
    .style("opacity", 0);


/**
 * Renderiza resúmenes visuales por canal.
 *
 * Cada fila representa un canal.
 * Cada mini-gráfico representa una métrica.
 * Cada mini-gráfico tiene 3 barras: Before, During, After.
 */
export function renderSummaryMetricsChart({
    containerId,
    signalData,
    activeChannels,
}) {
    const container = document.getElementById(containerId);

    container.innerHTML = "";

    if (!signalData || !signalData.metrics) {
        container.innerHTML = `
            <p>
                Selecciona un trial para visualizar resúmenes.
            </p>
        `;
        return;
    }

    activeChannels.forEach((channel) => {
        const channelMetrics = signalData.metrics[channel];

        if (!channelMetrics) {
            return;
        }

        const row = document.createElement("div");
        row.className = "summary-channel-row";

        const title = document.createElement("div");
        title.className = "summary-channel-title";
        title.style.color = CHANNEL_COLORS[channel] ?? "#111827";
        title.textContent = channel;

        const chartsWrapper = document.createElement("div");
        chartsWrapper.className = "summary-mini-charts";

        row.appendChild(title);
        row.appendChild(chartsWrapper);

        container.appendChild(row);

        METRICS.forEach((metricName) => {
            renderMetricMiniBarChart({
                container: chartsWrapper,
                channel,
                metricName,
                channelMetrics,
            });
        });
    });
}


function renderMetricMiniBarChart({
    container,
    channel,
    metricName,
    channelMetrics,
}) {
    const chartBox = document.createElement("div");
    chartBox.className = "summary-mini-chart";

    container.appendChild(chartBox);


    const data = PHASES.map((phase) => ({
        phase,
        value: channelMetrics[phase][metricName],
    }));

    const width = 160;
    const height = 120;

    const margin = {
        top: 22,
        right: 10,
        bottom: 28,
        left: 42,
    };

    const svg = d3
        .select(chartBox)
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

    const xScale = d3
        .scaleBand()
        .domain(PHASES)
        .range([0, plotWidth])
        .padding(0.25);

    const values = data.map((d) => d.value);

    const yMin = Math.min(0, d3.min(values));
    const yMax = Math.max(0, d3.max(values));

    const yScale = d3
        .scaleLinear()
        .domain([yMin, yMax])
        .nice()
        .range([plotHeight, 0]);

    plotGroup
        .append("g")
        .attr(
            "transform",
            `translate(0, ${plotHeight})`
        )
        .call(
            d3.axisBottom(xScale)
        )
        .selectAll("text")
        .attr("font-size", 9);

    plotGroup
        .append("g")
        .call(
            d3.axisLeft(yScale).ticks(3)
        )
        .selectAll("text")
        .attr("font-size", 9);

    plotGroup
        .append("line")
        .attr("x1", 0)
        .attr("x2", plotWidth)
        .attr("y1", yScale(0))
        .attr("y2", yScale(0))
        .attr("stroke", "#6b7280")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "3,3");

    plotGroup
        .selectAll("rect")
        .data(data)
        .enter()
        .append("rect")
        .attr("x", (d) => xScale(d.phase))
        .attr("y", (d) => yScale(Math.max(0, d.value)))
        .attr("width", xScale.bandwidth())
        .attr("height", (d) =>
            Math.abs(yScale(d.value) - yScale(0))
        )
        .attr("fill", CHANNEL_COLORS[channel] ?? "#111827")
        .attr("opacity", 0.8)
        .on("mouseover", function (event, d) {
            d3.select(this).attr("opacity", 1);

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Channel:</strong> ${channel}<br>
                    <strong>Metric:</strong> ${metricName.toUpperCase()}<br>
                    <strong>Phase:</strong> ${d.phase}<br>
                    <strong>Value:</strong> ${d.value.toExponential(4)}
                `)
                .style("left", `${event.pageX + 12}px`)
                .style("top", `${event.pageY - 20}px`);
        })
        .on("mouseout", function () {
            d3.select(this).attr("opacity", 0.8);
            tooltip.style("opacity", 0);
        });

    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", 13)
        .attr("text-anchor", "middle")
        .attr("font-size", 11)
        .attr("font-weight", "bold")
        .text(metricName.toUpperCase());
}