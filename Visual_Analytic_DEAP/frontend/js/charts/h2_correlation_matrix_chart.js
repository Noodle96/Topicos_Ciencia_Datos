import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

export function renderH2CorrelationMatrix({
    containerSelector,
    data,
    selectedParticipants,
    onCellClick,
    onParticipantToggle,
}) {
    const container = d3.select(containerSelector);
    container.selectAll("*").remove();

    d3.select("#h2-matrix-tooltip").remove();

    const containerNode = container.node();
    const containerWidth = containerNode.clientWidth || 620;
    const containerHeight = containerNode.clientHeight || 420;

    if (!data || !data.row_channels || !data.participants) {
        container.append("p").text("No relationship matrix data available.");
        return;
    }

    const margin = {
        top: 26,
        right: 12,
        bottom: 48,
        left: 58,
    };

    const plotWidth = containerWidth - margin.left - margin.right;
    const plotHeight = containerHeight - margin.top - margin.bottom;

    const rowChannels = data.row_channels;
    const participants = data.participants.map(
        (participant) => participant.participant_label
    );

    const cellWidth = plotWidth / participants.length;
    const cellHeight = plotHeight / rowChannels.length;
    const cellSize = Math.min(cellWidth, cellHeight);

    const matrixWidth = cellSize * participants.length;
    const matrixHeight = cellSize * rowChannels.length;

    const svg = container
        .append("svg")
        .attr("width", containerWidth)
        .attr("height", containerHeight);

    const chart = svg
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3
        .scaleBand()
        .domain(participants)
        .range([0, matrixWidth])
        .padding(0.02);

    const yScale = d3
        .scaleBand()
        .domain(rowChannels)
        .range([0, matrixHeight])
        .padding(0.02);

    const colorScale = d3
        .scaleSequential()
        .domain([1, -1])
        .interpolator(d3.interpolateRdBu);

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("id", "h2-matrix-tooltip")
        .attr("class", "emotion-tooltip")
        .style("opacity", 0);

    chart
        .selectAll(".h2-cell")
        .data(data.cells)
        .enter()
        .append("rect")
        .attr("class", "h2-cell")
        .attr("x", (d) => xScale(d.participant_label))
        .attr("y", (d) => yScale(d.row_channel))
        .attr("width", xScale.bandwidth())
        .attr("height", yScale.bandwidth())
        .attr("fill", (d) =>
            d.correlation === null
                ? "#e5e7eb"
                : colorScale(d.correlation)
        )
        .attr("stroke", "#ffffff")
        .attr("stroke-width", 0.2)
        .attr("cursor", "pointer")
        .on("mouseover", function (event, d) {
            d3.select(this)
                .attr("stroke", "#facc15")
                .attr("stroke-width", 1.4);

            const correlationText =
                d.correlation === null
                    ? "N/A"
                    : d.correlation.toFixed(4);

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Participant:</strong> ${d.participant_label}<br>
                    <strong>Row group:</strong> ${d.row_group}<br>
                    <strong>Row channel:</strong> ${d.row_channel}<br>
                    <strong>Reference group:</strong> ${d.reference_group}<br>
                    <strong>Reference channel:</strong> ${d.reference_channel}<br>
                    <strong>Pearson:</strong> ${correlationText}
                `)
                .style("left", `${event.pageX + 14}px`)
                .style("top", `${event.pageY - 20}px`);
        })
        .on("mouseout", function () {
            d3.select(this)
                .attr("stroke", "#ffffff")
                .attr("stroke-width", 0.2);

            tooltip.style("opacity", 0);
        })
        .on("click", (_, d) => {
            if (onCellClick) {
                onCellClick(d);
            }
        });

    const xAxisGroup = chart
        .append("g")
        .attr("transform", `translate(0, ${matrixHeight})`)
        .call(d3.axisBottom(xScale).tickSize(0));

    xAxisGroup
        .selectAll("text")
        .attr("class", "h2-participant-axis-label")
        .attr("font-size", 8)
        // .attr("font-weight", "bold")
        .attr("transform", "rotate(-60)")
        .attr("text-anchor", "end")
        .attr("dx", "-0.5em")
        .attr("dy", "0.2em")
        .attr("cursor", "pointer")
        .attr("font-weight", (participantLabel) =>
            selectedParticipants.includes(participantLabel) ? 900 : 700
        )
        .attr("fill", (participantLabel) =>
            selectedParticipants.includes(participantLabel) ? "#ca8a04" : "#111827"
        )
        .on("click", (_, participantLabel) => {
            if (onParticipantToggle) {
                onParticipantToggle(participantLabel);
            }
        });

    xAxisGroup
        .selectAll(".tick")
        .append("rect")
        .attr("class", "h2-participant-selected-marker")
        .attr("x", -8)
        .attr("y", 4)
        .attr("width", 16)
        .attr("height", 3)
        .attr("rx", 2)
        .attr("fill", (participantLabel) =>
            selectedParticipants.includes(participantLabel)
                ? "#facc15"
                : "transparent"
        );

    chart
        .append("g")
        .call(d3.axisLeft(yScale).tickSize(0))
        .selectAll("text")
        .attr("font-size", 8)
        .attr("font-weight", "bold");

    svg
        .append("text")
        .attr("x", margin.left + matrixWidth / 2)
        .attr("y", 16)
        .attr("text-anchor", "middle")
        .attr("font-size", 12)
        .attr("font-weight", "bold")
        .text(
            `${data.row_group} channels vs ${data.reference_channel} across participants`
        );
}