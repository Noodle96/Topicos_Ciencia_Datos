import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

const CATEGORY_COLORS = d3.schemeTableau10;

function getCategoricalColorScale(values) {
    const uniqueValues = Array.from(
        new Set(values.filter((value) => value !== null && value !== "N/A"))
    );

    return d3
        .scaleOrdinal()
        .domain(uniqueValues)
        .range(CATEGORY_COLORS);
}

function buildCategoricalCells(profileData) {
    const cells = [];

    profileData.categorical_attributes.forEach((attribute) => {
        const values = profileData.records.map((record) => {
            return record.categorical[attribute] ?? "N/A";
        });

        const colorScale = getCategoricalColorScale(values);

        profileData.records.forEach((record) => {
            const value = record.categorical[attribute] ?? "N/A";

            cells.push({
                participant: record.Participant_id,
                attribute,
                value,
                color: value === "N/A" ? "#e5e7eb" : colorScale(value),
            });
        });
    });

    return cells;
}

function renderCategoricalHeatmap({
    container,
    profileData,
}) {
    const title = document.createElement("h4");
    title.textContent = "Categorical Attribute Heatmap";
    container.appendChild(title);

    const chartContainer = document.createElement("div");
    chartContainer.className = "h2-profile-chart";
    container.appendChild(chartContainer);

    const participants = profileData.selected_participants;
    const attributes = profileData.categorical_attributes;
    const cells = buildCategoricalCells(profileData);

    const width = chartContainer.clientWidth || container.clientWidth || 700;
    const height = 280;

    const margin = {
        top: 24,
        right: 20,
        bottom: 38,
        left: 190,
    };

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    const svg = d3
        .select(chartContainer)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const plotGroup = svg
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3
        .scaleBand()
        .domain(participants)
        .range([0, plotWidth])
        .padding(0.05);

    const yScale = d3
        .scaleBand()
        .domain(attributes)
        .range([0, plotHeight])
        .padding(0.08);

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "summary-tooltip")
        .style("opacity", 0);

    plotGroup
        .selectAll(".profile-categorical-cell")
        .data(cells)
        .enter()
        .append("rect")
        .attr("class", "profile-categorical-cell")
        .attr("x", (d) => xScale(d.participant))
        .attr("y", (d) => yScale(d.attribute))
        .attr("width", xScale.bandwidth())
        .attr("height", yScale.bandwidth())
        .attr("fill", (d) => d.color)
        .attr("stroke", "#ffffff")
        .attr("stroke-width", 0.7)
        .on("mouseover", function (event, d) {
            d3.select(this)
                .attr("stroke", "#111827")
                .attr("stroke-width", 1.4);

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Participant:</strong> ${d.participant}<br>
                    <strong>Attribute:</strong> ${d.attribute}<br>
                    <strong>Value:</strong> ${d.value}
                `)
                .style("left", `${event.pageX + 12}px`)
                .style("top", `${event.pageY - 20}px`);
        })
        .on("mouseout", function () {
            d3.select(this)
                .attr("stroke", "#ffffff")
                .attr("stroke-width", 0.7);

            tooltip.style("opacity", 0);
        });

    plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .call(d3.axisBottom(xScale).tickSize(0))
        .selectAll("text")
        .attr("font-size", 10)
        .attr("transform", "rotate(-35)")
        .attr("text-anchor", "end");

    plotGroup
        .append("g")
        .call(d3.axisLeft(yScale).tickSize(0))
        .selectAll("text")
        .attr("font-size", 10);
}

function buildNumericPoints(profileData) {
    const points = [];

    profileData.numeric_attributes.forEach((attribute) => {
        profileData.records.forEach((record) => {
            const value = record.numeric[attribute];

            if (value === null || value === undefined) {
                return;
            }

            points.push({
                participant: record.Participant_id,
                attribute,
                value,
            });
        });
    });

    return points;
}

function renderNumericDotPlot({
    container,
    profileData,
}) {
    const title = document.createElement("h4");
    title.textContent = "Numeric Attribute Dot Plot";
    container.appendChild(title);

    const chartContainer = document.createElement("div");
    chartContainer.className = "h2-profile-chart";
    container.appendChild(chartContainer);

    const attributes = profileData.numeric_attributes;
    const points = buildNumericPoints(profileData);

    const width = chartContainer.clientWidth || container.clientWidth || 700;
    const height = 230;

    const margin = {
        top: 24,
        right: 30,
        bottom: 28,
        left: 190,
    };

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    const svg = d3
        .select(chartContainer)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const plotGroup = svg
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const values = points.map((point) => point.value);

    const xScale = d3
        .scaleLinear()
        .domain(d3.extent(values))
        .nice()
        .range([0, plotWidth]);

    const yScale = d3
        .scaleBand()
        .domain(attributes)
        .range([0, plotHeight])
        .padding(0.35);

    const participantColor = d3
        .scaleOrdinal()
        .domain(profileData.selected_participants)
        .range(d3.schemeSet2);

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "summary-tooltip")
        .style("opacity", 0);

    plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .call(d3.axisBottom(xScale).ticks(6));

    plotGroup
        .append("g")
        .call(d3.axisLeft(yScale).tickSize(0))
        .selectAll("text")
        .attr("font-size", 10);

    plotGroup
        .selectAll(".profile-numeric-point")
        .data(points)
        .enter()
        .append("circle")
        .attr("class", "profile-numeric-point")
        .attr("cx", (d) => xScale(d.value))
        .attr("cy", (d) => yScale(d.attribute) + yScale.bandwidth() / 2)
        .attr("r", 5)
        .attr("fill", (d) => participantColor(d.participant))
        .attr("stroke", "#111827")
        .attr("stroke-width", 0.3)
        .attr("opacity", 0.9)
        .on("mouseover", function (event, d) {
            d3.select(this)
                .attr("r", 7)
                .attr("stroke-width", 1.2);

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Participant:</strong> ${d.participant}<br>
                    <strong>Attribute:</strong> ${d.attribute}<br>
                    <strong>Value:</strong> ${d.value}
                `)
                .style("left", `${event.pageX + 12}px`)
                .style("top", `${event.pageY - 20}px`);
        })
        .on("mouseout", function () {
            d3.select(this)
                .attr("r", 5)
                .attr("stroke-width", 0.3);

            tooltip.style("opacity", 0);
        });
}

export function renderH2ParticipantProfiles({
    containerId,
    profileData,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.selectAll(".summary-tooltip").remove();

    if (
        !profileData ||
        !profileData.records ||
        profileData.records.length === 0
    ) {
        container.innerHTML = "";
        return;
    }

    renderCategoricalHeatmap({
        container,
        profileData,
    });

    renderNumericDotPlot({
        container,
        profileData,
    });
}