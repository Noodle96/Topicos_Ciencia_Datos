import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";


/**
 * Renderiza el timeline temporal del trial seleccionado.
 */
export function renderTrialTimeline({
    containerId,
    selectedTrial,
}) {
    const container = document.getElementById(containerId);

    container.innerHTML = "";

    if (!selectedTrial) {
        return;
    }

    const width = container.clientWidth;
    const height = 140;

    const margin = {
        top: 20,
        right: 30,
        bottom: 20,
        left: 30,
    };

    const svg = d3
        .select(`#${containerId}`)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const timelineWidth =
        width - margin.left - margin.right;

    const timelineGroup = svg
        .append("g")
        .attr(
            "transform",
            `translate(${margin.left}, ${margin.top})`
        );

    /**
     * Segmentos temporales del trial.
     */
    const segments = [
        {
            label: "Before",
            status: 3,
            duration: 5,
            color: "#60a5fa",
        },
        {
            label: "During",
            status: 4,
            duration: 60,
            color: "#f59e0b",
        },
        {
            label: "After",
            status: 5,
            duration: 3,
            color: "#34d399",
        },
    ];

    const totalDuration = d3.sum(
        segments,
        (d) => d.duration
    );

    let currentX = 0;

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "emotion-tooltip")
        .style("opacity", 0);

    segments.forEach((segment) => {
        const segmentWidth =
            (segment.duration / totalDuration) *
            timelineWidth;

        timelineGroup
            .append("rect")
            .attr("x", currentX)
            .attr("y", 20)
            .attr("width", segmentWidth)
            .attr("height", 50)
            .attr("fill", segment.color)
            .attr("rx", 6)
            .attr("cursor", "pointer")

            .on("mouseover", function (event) {
                d3.select(this)
                    .attr("stroke", "#111827")
                    .attr("stroke-width", 2);

                tooltip
                    .style("opacity", 1)
                    .html(`
            <strong>Status:</strong> ${segment.status}<br>
            <strong>Phase:</strong> ${segment.label}<br>
            <strong>Duration:</strong> ${segment.duration} sec
          `)
                    .style("left", `${event.pageX + 12}px`)
                    .style("top", `${event.pageY - 20}px`);
            })

            .on("mouseout", function () {
                d3.select(this)
                    .attr("stroke", "none");

                tooltip.style("opacity", 0);
            })

            .on("click", function () {
                console.log(
                    "Temporal segment selected:",
                    segment
                );
            });

        timelineGroup
            .append("text")
            .attr(
                "x",
                currentX + segmentWidth / 2
            )
            .attr("y", 50)
            .attr("text-anchor", "middle")
            .attr("fill", "#111827")
            .attr("font-size", 12)
            .attr("font-weight", "bold")
            .text(segment.label);

        timelineGroup
            .append("text")
            .attr(
                "x",
                currentX + segmentWidth / 2
            )
            .attr("y", 88)
            .attr("text-anchor", "middle")
            .attr("fill", "#374151")
            .attr("font-size", 11)
            .text(`${segment.duration}s`);

        currentX += segmentWidth;
    });

    svg
        .append("text")
        .attr("x", margin.left)
        .attr("y", 15)
        .attr("font-size", 13)
        .attr("font-weight", "bold")
        .text(
            `Participant ${selectedTrial.Participant_id} — Trial ${selectedTrial.Trial}`
        );
}