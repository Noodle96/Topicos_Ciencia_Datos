import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

import {
    CHANNEL_COLORS,
} from "./signal_timeseries_chart.js";


let currentXDomain = null;
let lastRenderConfig = null;

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

// function resetZoom() {
export function resetTarea1SignalZoom() {
    currentXDomain = null;

    if (lastRenderConfig) {
        renderTarea1TemporalSignalChart(lastRenderConfig);
    }
}

function computeMean(samples) {
    return d3.mean(samples, (sample) => sample.value) ?? 0;
}

function renderMeanLine({
    plotGroup,
    yScale,
    plotWidth,
    meanValue,
    label,
    color,
}) {
    const y = yScale(meanValue);

    plotGroup
        .append("line")
        .attr("x1", 0)
        .attr("x2", plotWidth)
        .attr("y1", y)
        .attr("y2", y)
        .attr("stroke", color)
        .attr("stroke-width", 1.2)
        .attr("stroke-dasharray", "5,4");

    plotGroup
        .append("text")
        .attr("x", plotWidth - 4)
        .attr("y", y - 4)
        .attr("text-anchor", "end")
        .attr("font-size", 10)
        .attr("fill", color)
        .text(label);
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

            if (Math.abs(selectedEnd - selectedStart) < 0.4) {
                return;
            }

            currentXDomain = [selectedStart, selectedEnd];

            if (lastRenderConfig) {
                renderTarea1TemporalSignalChart(lastRenderConfig);
            }
        });

    plotGroup
        .append("g")
        .attr("class", "zoom-brush")
        .call(brush);
}

export function renderTarea1TemporalSignalChart({
    containerId,
    signalData,
    activeChannels,
    normalizeSignals,
    onSignalHover,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    lastRenderConfig = {
        containerId,
        signalData,
        activeChannels,
        normalizeSignals,
        onSignalHover,
    };

    if (!signalData || !signalData.signals || activeChannels.length === 0) {
        container.innerHTML = `
            <p>Select a point and at least one channel.</p>
        `;
        return;
    }

    // const controls = document.createElement("div");
    // controls.className = "signal-zoom-controls";

    // const resetButton = document.createElement("button");
    // resetButton.textContent = "Reset Zoom";
    // resetButton.className = "reset-zoom-button";
    // resetButton.addEventListener("click", resetZoom);

    // controls.appendChild(resetButton);
    // container.appendChild(controls);

    if (normalizeSignals) {
        renderNormalizedOverlay({
            container,
            signalData,
            activeChannels,
            onSignalHover,
        });
        return;
    }

    activeChannels.forEach((channel) => {
        const samples = signalData.signals[channel] ?? [];

        if (samples.length === 0) {
            return;
        }

        renderSingleRawTrack({
            container,
            channel,
            samples,
            signalData,
            onSignalHover,
        });
    });
}

function renderSingleRawTrack({
    container,
    channel,
    samples,
    signalData,
    onSignalHover,
}) {
    const trackWrapper = document.createElement("div");
    trackWrapper.className = "signal-track";

    trackWrapper.addEventListener("mouseenter", () => {
        if (onSignalHover) {
            onSignalHover({
                channel,
                channelType: signalData.channel_types[channel],
                statistics: signalData.statistics[channel],
                mode: "raw",
            });
        }
});

    const title = document.createElement("div");
    title.className = "signal-track-title";
    title.style.color = CHANNEL_COLORS[channel] ?? "#111827";
    title.textContent = `${channel} | raw`;

    const chartContainer = document.createElement("div");
    chartContainer.className = "signal-track-chart";

    trackWrapper.appendChild(title);
    trackWrapper.appendChild(chartContainer);
    container.appendChild(trackWrapper);

    const width = chartContainer.clientWidth || container.clientWidth || 700;
    const height = 145;

    const margin = {
        top: 12,
        right: 28,
        bottom: 30,
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
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const fullXDomain = d3.extent(samples, (sample) => sample.time);
    const xDomain = currentXDomain ?? fullXDomain;

    const visibleSamples = samples.filter((sample) => {
        return sample.time >= xDomain[0] && sample.time <= xDomain[1];
    });

    const xScale = d3
        .scaleLinear()
        .domain(xDomain)
        .range([0, plotWidth]);

    const extent = d3.extent(visibleSamples, (sample) => sample.value);
    const padding = ((extent[1] ?? 1) - (extent[0] ?? -1)) * 0.12 || 1;

    const yScale = d3
        .scaleLinear()
        .domain([
            (extent[0] ?? -1) - padding,
            (extent[1] ?? 1) + padding,
        ])
        .range([plotHeight, 0]);

    plotGroup
        .append("rect")
        .attr("x", 0)
        .attr("y", 0)
        .attr("width", plotWidth)
        .attr("height", plotHeight)
        .attr("fill", "#fef3c7")
        .attr("opacity", 0.3);

    plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .call(d3.axisBottom(xScale).ticks(8));

    plotGroup
        .append("g")
        .call(d3.axisLeft(yScale).ticks(4));

    const lineGenerator = d3
        .line()
        .defined((sample) => sample.value !== null)
        .x((sample) => xScale(sample.time))
        .y((sample) => yScale(sample.value));

    // plotGroup
    //     .append("path")
    //     .datum(visibleSamples)
    //     .attr("fill", "none")
    //     .attr("stroke", CHANNEL_COLORS[channel] ?? "#111827")
    //     .attr("stroke-width", 1.4)
    //     .attr("opacity", 0.95)
    //     .attr("d", lineGenerator)
    //     .on("mouseover", () => {
    //         if (onSignalHover) {
    //             onSignalHover({
    //                 channel,
    //                 channelType: signalData.channel_types[channel],
    //                 statistics: signalData.statistics[channel],
    //                 mode: "raw",
    //             });
    //         }
    //     });

    plotGroup
        .append("path")
        .datum(visibleSamples)
        .attr("fill", "none")
        .attr("stroke", CHANNEL_COLORS[channel] ?? "#111827")
        .attr("stroke-width", 1.4)
        .attr("opacity", 0.95)
        .attr("d", lineGenerator);

    plotGroup
        .append("path")
        .datum(visibleSamples)
        .attr("fill", "none")
        .attr("stroke", "transparent")
        .attr("stroke-width", 14)
        .attr("cursor", "crosshair")
        .attr("d", lineGenerator)
        .on("mouseover", () => {
            if (onSignalHover) {
                onSignalHover({
                    channel,
                    channelType: signalData.channel_types[channel],
                    statistics: signalData.statistics[channel],
                    mode: "raw",
                });
            }
        });

    const meanValue = computeMean(samples);

    renderMeanLine({
        plotGroup,
        yScale,
        plotWidth,
        meanValue,
        label: "mean",
        color: "#dc2626",
    });

    addBrushZoom({
        plotGroup,
        xScale,
        plotWidth,
        plotHeight,
    });
}

function renderNormalizedOverlay({
    container,
    signalData,
    activeChannels,
    onSignalHover,
}) {
    const chartContainer = document.createElement("div");
    chartContainer.className = "normalized-overlay-chart";
    container.appendChild(chartContainer);

    const width = chartContainer.clientWidth || container.clientWidth || 760;
    const height = 430;

    const margin = {
        top: 24,
        right: 34,
        bottom: 40,
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
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const firstChannelSamples = signalData.signals[activeChannels[0]] ?? [];
    const fullXDomain = d3.extent(firstChannelSamples, (sample) => sample.time);
    const xDomain = currentXDomain ?? fullXDomain;

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
        .attr("opacity", 0.3);

    plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .call(d3.axisBottom(xScale).ticks(8));

    plotGroup
        .append("g")
        .call(d3.axisLeft(yScale).ticks(6));

    renderMeanLine({
        plotGroup,
        yScale,
        plotWidth,
        meanValue: 0,
        label: "z = 0",
        color: "#6b7280",
    });

    const lineGenerator = d3
        .line()
        .defined((sample) => sample.value !== null)
        .x((sample) => xScale(sample.time))
        .y((sample) => yScale(sample.value));

    activeChannels.forEach((channel) => {
        const rawSamples = signalData.signals[channel] ?? [];

        if (rawSamples.length === 0) {
            return;
        }

        const normalizedSamples = normalizeSamples(rawSamples).filter((sample) => {
            return sample.time >= xDomain[0] && sample.time <= xDomain[1];
        });

        // plotGroup
        //     .append("path")
        //     .datum(normalizedSamples)
        //     .attr("fill", "none")
        //     .attr("stroke", CHANNEL_COLORS[channel] ?? "#111827")
        //     .attr("stroke-width", 1.45)
        //     .attr("opacity", 0.85)
        //     .attr("d", lineGenerator)
        //     .on("mouseover", () => {
        //         if (onSignalHover) {
        //             onSignalHover({
        //                 channel,
        //                 channelType: signalData.channel_types[channel],
        //                 statistics: signalData.statistics[channel],
        //                 mode: "normalized",
        //             });
        //         }
        //     });
        plotGroup
            .append("path")
            .datum(normalizedSamples)
            .attr("fill", "none")
            .attr("stroke", CHANNEL_COLORS[channel] ?? "#111827")
            .attr("stroke-width", 1.45)
            .attr("opacity", 0.85)
            .attr("d", lineGenerator);

        plotGroup
            .append("path")
            .datum(normalizedSamples)
            .attr("fill", "none")
            .attr("stroke", "transparent")
            .attr("stroke-width", 14)
            .attr("cursor", "crosshair")
            .attr("d", lineGenerator)
            .on("mouseover", () => {
                if (onSignalHover) {
                    onSignalHover({
                        channel,
                        channelType: signalData.channel_types[channel],
                        statistics: signalData.statistics[channel],
                        mode: "normalized",
                    });
                }
            });
    });

    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", 16)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("font-weight", "bold")
        .text("Normalized overlay view | z-score");

    const legendGroup = svg
        .append("g")
        .attr("transform", `translate(${margin.left + 12}, ${margin.top + 12})`)
        .style("pointer-events", "all");

    activeChannels.forEach((channel, index) => {
        const itemGroup = legendGroup
            .append("g")
            .attr("transform", `translate(0, ${index * 18})`)
            .attr("cursor", "pointer")
            .on("mouseenter", () => {
                if (onSignalHover) {
                    onSignalHover({
                        channel,
                        channelType: signalData.channel_types[channel],
                        statistics: signalData.statistics[channel],
                        mode: "normalized",
                    });
                }
            });

        itemGroup
            .append("rect")
            .attr("x", -6)
            .attr("y", -10)
            .attr("width", 120)
            .attr("height", 18)
            .attr("fill", "rgba(255,255,255,0.01)")
            .style("pointer-events", "all");

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

    addBrushZoom({
        plotGroup,
        xScale,
        plotWidth,
        plotHeight,
    });
}