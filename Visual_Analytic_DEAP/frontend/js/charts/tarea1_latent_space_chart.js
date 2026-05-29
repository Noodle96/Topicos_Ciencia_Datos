import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";
const PARTICIPANT_COLOR_SCALE = d3
    .scaleOrdinal(d3.schemeTableau10);
export function renderTarea1LatentSpaceChart({
    containerId,
    points,
    projectionMethod,
    filterMode,
    selectedParticipant,
    selectedExperiment,
    selectedParticipants,
    selectedPoint,
    onPointClick,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select("#tarea1-latent-tooltip").remove();

    if (!points || points.length === 0) {
        container.innerHTML = "<p>No points available.</p>";
        return;
    }

    const width = container.clientWidth || 700;
    const height = container.clientHeight || 420;

    const margin = {
        top: 28,
        right: 28,
        bottom: 48,
        left: 58,
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
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xExtent = d3.extent(points, (d) => Number(d.x));
    const yExtent = d3.extent(points, (d) => Number(d.y));

    const xScale = d3
        .scaleLinear()
        .domain(xExtent)
        .nice()
        .range([0, plotWidth]);

    const yScale = d3
        .scaleLinear()
        .domain(yExtent)
        .nice()
        .range([plotHeight, 0]);

    plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .call(d3.axisBottom(xScale).ticks(7));

    plotGroup
        .append("g")
        .call(d3.axisLeft(yScale).ticks(7));

    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", 16)
        .attr("text-anchor", "middle")
        .attr("font-size", 13)
        .attr("font-weight", "bold")
        .text(`${projectionMethod.toUpperCase()} projection | each point = one trial`);

    svg
        .append("text")
        .attr("x", width / 2)
        .attr("y", height - 6)
        .attr("text-anchor", "middle")
        .attr("font-size", 11)
        .text("Latent dimension 1");

    svg
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -height / 2)
        .attr("y", 14)
        .attr("text-anchor", "middle")
        .attr("font-size", 11)
        .text("Latent dimension 2");

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("id", "tarea1-latent-tooltip")
        .attr("class", "emotion-tooltip")
        .style("opacity", 0);

    function isHighlighted(point) {
        if (filterMode === "all") {
            return true;
        }

        if (filterMode === "participant") {
            return Number(point.Participant_id) === Number(selectedParticipant);
        }

        if (filterMode === "experiment") {
            return Number(point.Experiment_id) === Number(selectedExperiment);
        }

        return true;
    }

    function isParticipantSelected(point) {
        if (filterMode !== "experiment") {
            return false;
        }

        return selectedParticipants?.includes(point.Participant_label);
    }

    function getParticipantColor(point) {
        return PARTICIPANT_COLOR_SCALE(
            point.Participant_label
        );
    }

    function isPointSelected(point) {
        if (!selectedPoint) {
            return false;
        }

        return (
            Number(point.Participant_id) === Number(selectedPoint.Participant_id)
            && Number(point.Trial) === Number(selectedPoint.Trial)
        );
    }

    let selectedPointElement = null;

    plotGroup
        .selectAll(".tarea1-latent-point")
        .data(points)
        .enter()
        .append("circle")
        .attr("class", "tarea1-latent-point")
        .attr("cx", (d) => xScale(Number(d.x)))
        .attr("cy", (d) => yScale(Number(d.y)))
        .attr("r", (d) => {
            if (isPointSelected(d)) return 7;
            if (isParticipantSelected(d)) return 5.5;
            return isHighlighted(d) ? 4.2 : 3;
        })
        .attr("fill", (d) => {
            if (isPointSelected(d)) {
                return "#facc15";
            }

            if (isParticipantSelected(d)) {
                return getParticipantColor(d);
            }

            return "#2563eb";
        })
        .attr("opacity", (d) => {
            if (isPointSelected(d) || isParticipantSelected(d)) return 1;
            return isHighlighted(d) ? 0.82 : 0.12;
        })
        .attr("stroke", (d) => {
            if (isPointSelected(d) || isParticipantSelected(d)) return "#111827";
            return "none";
        })
        .attr("stroke-width", (d) => {
            if (isPointSelected(d)) return 1.5;
            if (isParticipantSelected(d)) return 1.1;
            return 0;
        })
        .attr("cursor", "pointer")
        .on("mouseover", function (event, d) {
            d3.select(this)
                .attr("r", 6)
                .attr("opacity", 1)
                .attr("fill", "#84cc16");

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Participant:</strong> ${d.Participant_label}<br>
                    <strong>Trial:</strong> ${d.Trial}<br>
                    <strong>Experiment:</strong> ${d.Experiment_id}<br>
                    <strong>Valence:</strong> ${d.Valence ?? "N/A"}<br>
                    <strong>Arousal:</strong> ${d.Arousal ?? "N/A"}<br>
                    <strong>Dominance:</strong> ${d.Dominance ?? "N/A"}<br>
                    <strong>Liking:</strong> ${d.Liking ?? "N/A"}<br>
                    <strong>Projection:</strong> ${d.projection_method}
                `)
                .style("left", `${event.pageX + 14}px`)
                .style("top", `${event.pageY - 18}px`);
        })
        .on("mouseout", function (event, d) {
            if (this !== selectedPointElement) {
                d3.select(this)
                    .attr("r", () => {
                        if (isPointSelected(d)) return 7;
                        if (isParticipantSelected(d)) return 5.5;
                        return isHighlighted(d) ? 4.2 : 3;
                    })
                    .attr("fill", () => {
                        if (isPointSelected(d)) {
                            return "#facc15";
                        }

                        if (isParticipantSelected(d)) {
                            return getParticipantColor(d);
                        }

                        return "#2563eb";
                    })
                    .attr("opacity", () => {
                        if (isPointSelected(d) || isParticipantSelected(d)) return 1;
                        return isHighlighted(d) ? 0.82 : 0.12;
                    })
                    .attr("stroke", () => {
                        if (isPointSelected(d) || isParticipantSelected(d)) return "#111827";
                        return "none";
                    })
                    .attr("stroke-width", () => {
                        if (isPointSelected(d)) return 1.5;
                        if (isParticipantSelected(d)) return 1.1;
                        return 0;
                    });
            }

            tooltip.style("opacity", 0);
        })
        .on("click", function (_, d) {
            selectedPointElement = this;
            if (onPointClick) {
                onPointClick(d);
            }
        });
}