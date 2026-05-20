import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

/**
 * Renderiza el scatter plot del espacio emocional.
 */
export function renderEmotionSpaceChart({
    containerId,
    points,
    xVariable,
    yVariable,
    onPointClick,
}) {
    const container = document.getElementById(containerId);

    container.innerHTML = "";
    // console.log("Emotion Space points:", points);
    // console.log("Container width:", container.clientWidth);
    // console.log("Container height:", container.clientHeight);

    if (!points || points.length === 0) {
        container.innerHTML = "<p>No hay puntos para mostrar.</p>";
        return;
    }

    const width = container.clientWidth;
    const height = container.clientHeight || 380;

    const margin = {
        top: 40,
        right: 40,
        bottom: 70,
        left: 70,
    };

    const svg = d3
        .select(`#${containerId}`)
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
        .scaleLinear()
        .domain([1, 9])
        .range([0, plotWidth]);

    const yScale = d3
        .scaleLinear()
        .domain([1, 9])
        .range([plotHeight, 0]);

    const xAxis = d3.axisBottom(xScale);

    const yAxis = d3.axisLeft(yScale);

    // Eje X cruzando por y = 5
    plotGroup
        .append("g")
        .attr(
            "transform",
            `translate(0, ${yScale(5)})`
        )
        .call(xAxis);

    // Eje Y cruzando por x = 5
    plotGroup
        .append("g")
        .attr(
            "transform",
            `translate(${xScale(5)}, 0)`
        )
        .call(yAxis);

    plotGroup
        .append("text")
        .attr("x", plotWidth / 2)
        .attr("y", plotHeight + 50)
        .attr("text-anchor", "middle")
        .text(xVariable);

    plotGroup
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -plotHeight / 2)
        .attr("y", -45)
        .attr("text-anchor", "middle")
        .text(yVariable);

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "emotion-tooltip")
        .style("opacity", 0);

    let selectedPoint = null;

    plotGroup
        .selectAll("circle")
        .data(points)
        .enter()
        .append("circle")
        .attr("cx", (d) => xScale(d.x))
        .attr("cy", (d) => yScale(d.y))
        .attr("r", 4)
        .attr("fill", "#2563eb")
        .attr("opacity", 0.55)
        .attr("cursor", "pointer")

        .on("mouseover", function (event, d) {
            if (this !== selectedPoint) {
                d3.select(this)
                    .attr("fill", "#84cc16")
                    .attr("opacity", 0.95)
                    .attr("r", 6);
            }
            const experimentId = Number(d.Experiment_id);
            const thumbnailPath =
                `./assets/video_thumbnails/experiment_${String(experimentId).padStart(2, "0")}.jpg`;
            tooltip
                .style("opacity", 1)
                .html(`
                    <img
                        src="${thumbnailPath}"
                        class="emotion-tooltip-thumbnail"
                    >
                    <strong>Participant:</strong> S${String(d.Participant_id).padStart(2, "0")}<br>
                    <strong>Experiment:</strong> ${d.Experiment_id}<br>
                    <strong>Trial:</strong> ${d.Trial}<br>
                    <strong>Valence:</strong> ${d.Valence}<br>
                    <strong>Arousal:</strong> ${d.Arousal}<br>
                    <strong>Dominance:</strong> ${d.Dominance}<br>
                    <strong>Liking:</strong> ${d.Liking}<br>
                    <strong>Familiarity:</strong> ${d.Familiarity ?? "N/A"}
                `)
                .style("left", `${event.pageX + 15}px`)
                .style("top", `${event.pageY - 20}px`);
        })

        .on("mouseout", function () {
            if (this !== selectedPoint) {
                d3.select(this)
                    .attr("fill", "#2563eb")
                    .attr("opacity", 0.55)
                    .attr("r", 4);
            }

            tooltip.style("opacity", 0);
        })

        .on("click", function (_, d) {
            if (selectedPoint) {
                d3.select(selectedPoint)
                    .attr("fill", "#2563eb")
                    .attr("opacity", 0.55)
                    .attr("r", 4);
            }

            selectedPoint = this;

            d3.select(this)
                .attr("fill", "#9dff0aff")
                .attr("opacity", 1)
                .attr("r", 6);

            if (onPointClick) {
                onPointClick(d);
            }
        });
}