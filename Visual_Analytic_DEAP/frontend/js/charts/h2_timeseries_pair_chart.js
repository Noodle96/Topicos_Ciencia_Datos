import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

import {
    CHANNEL_COLORS,
} from "./signal_timeseries_chart.js";

const MAX_VISUAL_POINTS = 1000;

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

function addLocalRelationshipBrush({
    plotGroup,
    xScale,
    plotWidth,
    plotHeight,
    onBrushEnd,
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

            const startSec = xScale.invert(x0);
            const endSec = xScale.invert(x1);

            if (Math.abs(endSec - startSec) < 0.5) {
                return;
            }

            if (onBrushEnd) {
                onBrushEnd({
                    startSec,
                    endSec,
                });
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
    onBrushEnd,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    if (!pairData || !pairData.times) {
        container.innerHTML = `
            <p>
                Select a relation to load the temporal explorer.
            </p>
        `;
        return;
    }

    const width = container.clientWidth || 520;
    const height = container.clientHeight || 320;

    const margin = {
        top: 34,
        right: 30,
        bottom: 42,
        left: 54,
    };

    const svg = d3
        .select(container)
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

    const eegValues = normalizeValues(pairData.eeg_values);
    const peripheralValues = normalizeValues(
        pairData.peripheral_values
    );

    const eegSamplesFull = relativeTimes.map((time, index) => ({
        time,
        value: eegValues[index],
    }));

    const peripheralSamplesFull = relativeTimes.map((time, index) => ({
        time,
        value: peripheralValues[index],
    }));

    const eegSamples = downsampleSamples(eegSamplesFull);
    const peripheralSamples = downsampleSamples(peripheralSamplesFull);

    const xScale = d3
        .scaleLinear()
        .domain(d3.extent(relativeTimes))
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
        .attr("opacity", 0.4);

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
        .datum(eegSamples)
        .attr("fill", "none")
        .attr("stroke", CHANNEL_COLORS[pairData.eeg_channel] ?? "#2563eb")
        .attr("stroke-width", 1.6)
        .attr("opacity", 0.9)
        .attr("d", lineGenerator);

    plotGroup
        .append("path")
        .datum(peripheralSamples)
        .attr("fill", "none")
        .attr("stroke", CHANNEL_COLORS[pairData.peripheral_channel] ?? "#0f766e")
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
            `${pairData.eeg_channel} ↔ ${pairData.peripheral_channel} | Pearson: ${correlationText}`
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
            label: `${pairData.eeg_channel} | EEG z-score`,
            color: CHANNEL_COLORS[pairData.eeg_channel] ?? "#2563eb",
        },
        {
            label: `${pairData.peripheral_channel} | Peripheral z-score`,
            color: CHANNEL_COLORS[pairData.peripheral_channel] ?? "#0f766e",
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
    addLocalRelationshipBrush({
        plotGroup,
        xScale,
        plotWidth,
        plotHeight,
        onBrushEnd,
    });
}