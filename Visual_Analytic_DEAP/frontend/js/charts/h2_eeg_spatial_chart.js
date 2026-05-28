import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

const EEG_2D_POSITIONS = {
    Fp1: { x: 38, y: 10 },
    Fp2: { x: 62, y: 10 },

    AF3: { x: 35, y: 20 },
    AF4: { x: 65, y: 20 },

    F7: { x: 18, y: 30 },
    F3: { x: 35, y: 32 },
    Fz: { x: 50, y: 30 },
    F4: { x: 65, y: 32 },
    F8: { x: 82, y: 30 },

    FC5: { x: 25, y: 43 },
    FC1: { x: 42, y: 43 },
    FC2: { x: 58, y: 43 },
    FC6: { x: 75, y: 43 },

    T7: { x: 12, y: 55 },
    C3: { x: 34, y: 55 },
    Cz: { x: 50, y: 55 },
    C4: { x: 66, y: 55 },
    T8: { x: 88, y: 55 },

    CP5: { x: 25, y: 67 },
    CP1: { x: 42, y: 67 },
    CP2: { x: 58, y: 67 },
    CP6: { x: 75, y: 67 },

    P7: { x: 18, y: 78 },
    P3: { x: 35, y: 78 },
    Pz: { x: 50, y: 80 },
    P4: { x: 65, y: 78 },
    P8: { x: 82, y: 78 },

    PO3: { x: 38, y: 88 },
    PO4: { x: 62, y: 88 },

    O1: { x: 38, y: 96 },
    Oz: { x: 50, y: 98 },
    O2: { x: 62, y: 96 },
};

function buildSpatialPoints({ matrixData, selectedCell }) {
    return matrixData.cells
        .filter((cell) => {
            return (
                cell.participant_id === selectedCell.participant_id &&
                cell.row_group === "EEG" &&
                EEG_2D_POSITIONS[cell.row_channel]
            );
        })
        .map((cell) => ({
            channel: cell.row_channel,
            correlation: cell.correlation,
            position: EEG_2D_POSITIONS[cell.row_channel],
            isSelected: cell.row_channel === selectedCell.row_channel,
        }));
}

export function renderH2EEGSpatialChart({
    containerId,
    matrixData,
    selectedCell,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    if (!matrixData || !selectedCell) {
        container.innerHTML = `
            <p>Select a matrix cell to inspect its EEG spatial pattern.</p>
        `;
        return;
    }

    if (matrixData.row_group !== "EEG") {
        container.innerHTML = `
            <p>
                EEG Spatial Explorer is available when Group Y = EEG.
            </p>
        `;
        return;
    }

    const spatialPoints = buildSpatialPoints({
        matrixData,
        selectedCell,
    });

    const width = container.clientWidth || 520;
    const height = container.clientHeight || 320;

    const svg = d3
        .select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const plotWidth = Math.min(width * 0.72, height * 0.9);
    const plotHeight = plotWidth;

    const originX = 24;
    const originY = (height - plotHeight) / 2;

    const xScale = d3
        .scaleLinear()
        .domain([0, 100])
        .range([originX, originX + plotWidth]);

    const yScale = d3
        .scaleLinear()
        .domain([0, 100])
        .range([originY, originY + plotHeight]);

    const colorScale = d3
        .scaleSequential()
        .domain([1, -1])
        .interpolator(d3.interpolateRdBu);

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "summary-tooltip")
        .style("opacity", 0);

    svg
        .append("ellipse")
        .attr("cx", xScale(50))
        .attr("cy", yScale(55))
        .attr("rx", plotWidth * 0.43)
        .attr("ry", plotHeight * 0.47)
        .attr("fill", "#f9fafb")
        .attr("stroke", "#111827")
        .attr("stroke-width", 1.3);

    svg
        .append("path")
        .attr(
            "d",
            `
            M ${xScale(44)} ${yScale(8)}
            Q ${xScale(50)} ${yScale(0)} ${xScale(56)} ${yScale(8)}
            `
        )
        .attr("fill", "none")
        .attr("stroke", "#111827")
        .attr("stroke-width", 1.3);

    svg
        .append("text")
        .attr("x", xScale(50))
        .attr("y", yScale(4))
        .attr("text-anchor", "middle")
        .attr("font-size", 10)
        .attr("font-weight", "bold")
        .text("Nasion");

    svg
        .selectAll(".eeg-spatial-node")
        .data(spatialPoints)
        .enter()
        .append("circle")
        .attr("class", "eeg-spatial-node")
        .attr("cx", (d) => xScale(d.position.x))
        .attr("cy", (d) => yScale(d.position.y))
        .attr("r", (d) => (d.isSelected ? 8 : 6))
        .attr("fill", (d) =>
            d.correlation === null ? "#e5e7eb" : colorScale(d.correlation)
        )
        .attr("stroke", (d) => (d.isSelected ? "#facc15" : "#111827"))
        .attr("stroke-width", (d) => (d.isSelected ? 2.5 : 0.7))
        .on("mouseover", function (event, d) {
            d3.select(this)
                .attr("r", d.isSelected ? 9 : 7)
                .attr("stroke-width", 2);

            const correlationText =
                d.correlation === null
                    ? "N/A"
                    : d.correlation.toFixed(4);

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Participant:</strong> ${selectedCell.participant_label}<br>
                    <strong>Channel:</strong> ${d.channel}<br>
                    <strong>Reference:</strong> ${selectedCell.reference_channel}<br>
                    <strong>Pearson:</strong> ${correlationText}
                `)
                .style("left", `${event.pageX + 12}px`)
                .style("top", `${event.pageY - 20}px`);
        })
        .on("mouseout", function (_, d) {
            d3.select(this)
                .attr("r", d.isSelected ? 8 : 6)
                .attr("stroke", d.isSelected ? "#facc15" : "#111827")
                .attr("stroke-width", d.isSelected ? 2.5 : 0.7);

            tooltip.style("opacity", 0);
        });

    svg
        .selectAll(".eeg-spatial-label")
        .data(spatialPoints)
        .enter()
        .append("text")
        .attr("class", "eeg-spatial-label")
        .attr("x", (d) => xScale(d.position.x))
        .attr("y", (d) => yScale(d.position.y) - 9)
        .attr("text-anchor", "middle")
        .attr("font-size", 8)
        .attr("font-weight", "bold")
        .attr("fill", "#111827")
        .text((d) => d.channel);

    const legendX = originX + plotWidth + 34;
    const legendY = originY + 42;
    const legendHeight = Math.min(180, plotHeight * 0.65);
    const legendWidth = 14;

    const defs = svg.append("defs");

    const gradient = defs
        .append("linearGradient")
        .attr("id", "h2-spatial-gradient")
        .attr("x1", "0%")
        .attr("x2", "0%")
        .attr("y1", "0%")
        .attr("y2", "100%");

    gradient
        .append("stop")
        .attr("offset", "0%")
        .attr("stop-color", colorScale(1));

    gradient
        .append("stop")
        .attr("offset", "50%")
        .attr("stop-color", colorScale(0));

    gradient
        .append("stop")
        .attr("offset", "100%")
        .attr("stop-color", colorScale(-1));

    svg
        .append("rect")
        .attr("x", legendX)
        .attr("y", legendY)
        .attr("width", legendWidth)
        .attr("height", legendHeight)
        .attr("fill", "url(#h2-spatial-gradient)");

    const legendScale = d3
        .scaleLinear()
        .domain([1, -1])
        .range([legendY, legendY + legendHeight]);

    svg
        .append("g")
        .attr("transform", `translate(${legendX + legendWidth}, 0)`)
        .call(d3.axisRight(legendScale).ticks(5))
        .selectAll("text")
        .attr("font-size", 9);

    svg
        .append("text")
        .attr("x", legendX)
        .attr("y", legendY - 12)
        .attr("font-size", 10)
        .attr("font-weight", "bold")
        .text("Pearson");

    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", 16)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("font-weight", "bold")
        .text(
            `${selectedCell.participant_label}: EEG vs ${selectedCell.reference_channel}`
        );
}