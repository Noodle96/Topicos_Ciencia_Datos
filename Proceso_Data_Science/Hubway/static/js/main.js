const monthLabels = [
    "Ene", "Feb", "Mar", "Abr", "May", "Jun",
    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"
];

let usageData = [];
let weatherData = [];
let highlightedMonthIndex = null;
let currentMunicipal = null;
/**
 * Inicializa la aplicación cargando datos de uso y clima.
 */
async function initializeApp() {
    createTooltip();

    const stationsResponse = await fetch("/api/stations");
    const stations = await stationsResponse.json();

    const usageResponse = await fetch("/api/station-monthly-usage");
    usageData = await usageResponse.json();

    const weatherResponse = await fetch("/api/weather-monthly-averages");
    weatherData = await weatherResponse.json();

    populateMunicipalDropdown(stations);
    setupDropdownListener();

    if (stations.length > 0) {
        const firstMunicipal = stations[0].municipal;
        document.getElementById("station-select").value = firstMunicipal;
        updateDashboard(firstMunicipal);
    }
}

function createTooltip() {
    const existingTooltip = document.getElementById("chart-tooltip");

    if (existingTooltip) {
        return;
    }

    const tooltip = document.createElement("div");
    tooltip.id = "chart-tooltip";
    tooltip.style.position = "absolute";
    tooltip.style.pointerEvents = "none";
    tooltip.style.background = "rgba(255, 255, 255, 0.95)";
    tooltip.style.border = "1px solid #ccc";
    tooltip.style.borderRadius = "8px";
    tooltip.style.padding = "10px 12px";
    tooltip.style.fontSize = "13px";
    tooltip.style.boxShadow = "0 2px 8px rgba(0, 0, 0, 0.15)";
    tooltip.style.display = "none";
    tooltip.style.zIndex = "9999";

    document.body.appendChild(tooltip);
}


/**
 * Llena el dropdown con municipalidades.
 */
function populateMunicipalDropdown(stations) {
    const select = document.getElementById("station-select");
    select.innerHTML = "";

    stations.forEach((station) => {
        const option = document.createElement("option");
        option.value = station.municipal;
        option.textContent = station.municipal;
        select.appendChild(option);
    });
}

/**
 * Escucha cambios en el dropdown.
 */
function setupDropdownListener() {
    const select = document.getElementById("station-select");

    select.addEventListener("change", (event) => {
        const municipal = event.target.value;
        updateDashboard(municipal);
    });
}

/**
 * Actualiza todas las gráficas para la municipalidad seleccionada.
 */
function updateDashboard(municipal) {
    currentMunicipal = municipal;

    const usageMunicipalData = usageData.find(
        (item) => item.municipal === municipal
    );

    const weatherMunicipalData = weatherData.find(
        (item) => item.municipal === municipal
    );

    if (!usageMunicipalData || !weatherMunicipalData) {
        return;
    }

    document.getElementById("usage-title").textContent =
        `Frecuencia mensual de uso - ${municipal}`;

    document.getElementById("combined-title").textContent =
        `Clima combinado - ${municipal}`;

    document.getElementById("temperature-title").textContent =
        `Temperatura - ${municipal}`;

    document.getElementById("wind-title").textContent =
        `Viento - ${municipal}`;

    document.getElementById("rain-title").textContent =
        `Lluvia - ${municipal}`;

    renderUsageBarChart(
        "#usage-chart",
        usageMunicipalData.monthly_counts,
        weatherMunicipalData
    );

    renderCombinedWeatherChart(
        "#combined-weather-chart",
        weatherMunicipalData.temperature,
        weatherMunicipalData.rain,
        weatherMunicipalData.wind
    );

    renderSingleLineChart(
        "#temperature-chart",
        weatherMunicipalData.temperature,
        "Temperatura promedio",
        "temperature",
        highlightedMonthIndex
    );

    renderSingleLineChart(
        "#wind-chart",
        weatherMunicipalData.wind,
        "Velocidad promedio del viento",
        "wind",
        highlightedMonthIndex
    );

    renderSingleLineChart(
        "#rain-chart",
        weatherMunicipalData.rain,
        "Lluvia promedio",
        "rain",
        highlightedMonthIndex
    );
}

/**
 * Devuelve el tamaño y márgenes estándar para un SVG.
 */
function getChartConfig() {
    return {
        width: 520,
        height: 260,
        margin: { top: 20, right: 30, bottom: 45, left: 55 }
    };
}

/**
 * Limpia el SVG y prepara el grupo principal.
 */
function prepareSvg(svgSelector) {
    const svg = d3.select(svgSelector);
    svg.selectAll("*").remove();

    const { width, height, margin } = getChartConfig();

    svg.attr("viewBox", `0 0 ${width} ${height}`);

    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;

    const chartGroup = svg
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);

    return {
        svg,
        chartGroup,
        width,
        height,
        margin,
        innerWidth,
        innerHeight
    };
}

/**
 * Renderiza el gráfico de barras para frecuencia de uso.
 */
function renderUsageBarChart(svgSelector, monthlyCounts, weatherMunicipalData) {
  const { chartGroup, innerWidth, innerHeight } = prepareSvg(svgSelector);

  const baseBarColor = "#4A90C2";
  const hoverBarColor = "#2F6F9F";

  const data = monthLabels.map((month, index) => ({
    month,
    monthIndex: index,
    value: monthlyCounts[index],
    temperature: weatherMunicipalData.temperature[index],
    rain: weatherMunicipalData.rain[index],
    wind: weatherMunicipalData.wind[index]
  }));

  const xScale = d3
    .scaleBand()
    .domain(data.map((d) => d.month))
    .range([0, innerWidth])
    .padding(0.2);

  const yMax = d3.max(data, (d) => d.value) || 0;

  const yScale = d3
    .scaleLinear()
    .domain([0, yMax])
    .nice()
    .range([innerHeight, 0]);

  chartGroup
    .append("g")
    .attr("transform", `translate(0, ${innerHeight})`)
    .call(d3.axisBottom(xScale));

  chartGroup
    .append("g")
    .call(d3.axisLeft(yScale));

  const tooltip = document.getElementById("chart-tooltip");

  chartGroup
    .selectAll(".bar")
    .data(data)
    .enter()
    .append("rect")
    .attr("class", "bar")
    .attr("x", (d) => xScale(d.month))
    .attr("y", (d) => yScale(d.value))
    .attr("width", xScale.bandwidth())
    .attr("height", (d) => innerHeight - yScale(d.value))
    .attr("fill", (d) =>
      highlightedMonthIndex === d.monthIndex ? hoverBarColor : baseBarColor
    )
    .on("mouseover", function (event, d) {
      highlightedMonthIndex = d.monthIndex;

      d3.select(this).attr("fill", hoverBarColor);

      tooltip.style.display = "block";
      tooltip.innerHTML = `
        <strong>${d.month}</strong><br>
        Frecuencia: ${d.value}<br>
        Temperatura: ${formatMetricValue(d.temperature)}<br>
        Lluvia: ${formatMetricValue(d.rain)}<br>
        Viento: ${formatMetricValue(d.wind)}
      `;

      updateDashboard(currentMunicipal);
    })
    .on("mousemove", function (event) {
      tooltip.style.left = `${event.pageX + 12}px`;
      tooltip.style.top = `${event.pageY - 20}px`;
    })
    .on("mouseout", function () {
      highlightedMonthIndex = null;

      tooltip.style.display = "none";

      updateDashboard(currentMunicipal);
    });

  chartGroup
    .append("text")
    .attr("x", innerWidth / 2)
    .attr("y", innerHeight + 35)
    .attr("text-anchor", "middle")
    .attr("class", "axis-label")
    .text("Mes");

  chartGroup
    .append("text")
    .attr("transform", "rotate(-90)")
    .attr("x", -innerHeight / 2)
    .attr("y", -40)
    .attr("text-anchor", "middle")
    .attr("class", "axis-label")
    .text("Frecuencia");
}

function formatMetricValue(value) {
    if (value === null || value === undefined) {
        return "N/A";
    }

    return value.toFixed(2);
}

/**
 * Renderiza una gráfica combinada con 3 líneas.
 * Aquí NO dibujamos línea de promedio para evitar ruido visual.
 */
function renderCombinedWeatherChart(svgSelector, temperature, rain, wind) {
    const { chartGroup, innerWidth, innerHeight } = prepareSvg(svgSelector);

    const data = monthLabels.map((month, index) => ({
        month,
        temperature: temperature[index],
        rain: rain[index],
        wind: wind[index]
    }));

    const xScale = d3
        .scalePoint()
        .domain(monthLabels)
        .range([0, innerWidth]);

    const allValues = [
        ...temperature.filter((value) => value !== null),
        ...rain.filter((value) => value !== null),
        ...wind.filter((value) => value !== null)
    ];

    const yMax = d3.max(allValues) || 0;

    const yScale = d3
        .scaleLinear()
        .domain([0, yMax])
        .nice()
        .range([innerHeight, 0]);

    chartGroup
        .append("g")
        .attr("transform", `translate(0, ${innerHeight})`)
        .call(d3.axisBottom(xScale));

    chartGroup
        .append("g")
        .call(d3.axisLeft(yScale));

    const temperatureLine = d3
        .line()
        .defined((d) => d.temperature !== null)
        .x((d) => xScale(d.month))
        .y((d) => yScale(d.temperature));

    const rainLine = d3
        .line()
        .defined((d) => d.rain !== null)
        .x((d) => xScale(d.month))
        .y((d) => yScale(d.rain));

    const windLine = d3
        .line()
        .defined((d) => d.wind !== null)
        .x((d) => xScale(d.month))
        .y((d) => yScale(d.wind));

    chartGroup
        .append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#e74c3c")
        .attr("stroke-width", 2)
        .attr("d", temperatureLine);

    chartGroup
        .append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#3498db")
        .attr("stroke-width", 2)
        .attr("d", rainLine);

    chartGroup
        .append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", "#27ae60")
        .attr("stroke-width", 2)
        .attr("d", windLine);

    chartGroup
        .append("text")
        .attr("x", innerWidth / 2)
        .attr("y", innerHeight + 35)
        .attr("text-anchor", "middle")
        .attr("class", "axis-label")
        .text("Mes");

    chartGroup
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -innerHeight / 2)
        .attr("y", -40)
        .attr("text-anchor", "middle")
        .attr("class", "axis-label")
        .text("Valor");

    renderLegend(chartGroup, [
        { label: "Temperatura", color: "#e74c3c" },
        { label: "Lluvia", color: "#3498db" },
        { label: "Viento", color: "#27ae60" }
    ]);
}

/**
 * Renderiza una gráfica individual de línea con promedio horizontal.
 */
function renderSingleLineChart(
    svgSelector,
    values,
    yAxisLabel,
    metricType,
    highlightedMonthIndexParam
) {
    const { chartGroup, innerWidth, innerHeight } = prepareSvg(svgSelector);

    const data = monthLabels.map((month, index) => ({
        month,
        monthIndex: index,
        value: values[index]
    }));

    const validValues = values.filter((value) => value !== null);
    const yMax = d3.max(validValues) || 0;

    const xScale = d3
        .scalePoint()
        .domain(monthLabels)
        .range([0, innerWidth]);

    const yScale = d3
        .scaleLinear()
        .domain([0, yMax])
        .nice()
        .range([innerHeight, 0]);

    if (highlightedMonthIndexParam !== null) {
        const selectedMonth = monthLabels[highlightedMonthIndexParam];
        const selectedX = xScale(selectedMonth);

        if (selectedX !== undefined) {
            const spacing =
                highlightedMonthIndexParam < monthLabels.length - 1
                    ? xScale(monthLabels[1]) - xScale(monthLabels[0])
                    : 30;

            chartGroup
                .append("rect")
                .attr("x", selectedX - spacing / 2)
                .attr("y", 0)
                .attr("width", spacing)
                .attr("height", innerHeight)
                .attr("fill", "#4A90C2")
                .attr("opacity", 0.12);
        }
    }

    chartGroup
        .append("g")
        .attr("transform", `translate(0, ${innerHeight})`)
        .call(d3.axisBottom(xScale));

    chartGroup
        .append("g")
        .call(d3.axisLeft(yScale));

    const color = getMetricColor(metricType);

    const lineGenerator = d3
        .line()
        .defined((d) => d.value !== null)
        .x((d) => xScale(d.month))
        .y((d) => yScale(d.value));

    chartGroup
        .append("path")
        .datum(data)
        .attr("fill", "none")
        .attr("stroke", color)
        .attr("stroke-width", 2.5)
        .attr("d", lineGenerator);

    chartGroup
        .selectAll(".point")
        .data(data.filter((d) => d.value !== null))
        .enter()
        .append("circle")
        .attr("cx", (d) => xScale(d.month))
        .attr("cy", (d) => yScale(d.value))
        .attr("r", 4)
        .attr("fill", color)
        .attr("class", "line-point");

    const avgValue = d3.mean(validValues);

    if (avgValue !== undefined) {
        chartGroup
            .append("line")
            .attr("x1", 0)
            .attr("x2", innerWidth)
            .attr("y1", yScale(avgValue))
            .attr("y2", yScale(avgValue))
            .attr("class", "avg-line");

        chartGroup
            .append("text")
            .attr("x", innerWidth - 5)
            .attr("y", yScale(avgValue) - 5)
            .attr("text-anchor", "end")
            .attr("class", "avg-label")
            .text(`Prom: ${avgValue.toFixed(2)}`);
    }

    chartGroup
        .append("text")
        .attr("x", innerWidth / 2)
        .attr("y", innerHeight + 35)
        .attr("text-anchor", "middle")
        .attr("class", "axis-label")
        .text("Mes");

    chartGroup
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -innerHeight / 2)
        .attr("y", -40)
        .attr("text-anchor", "middle")
        .attr("class", "axis-label")
        .text(yAxisLabel);
}

/**
 * Devuelve color según métrica.
 */
function getMetricColor(metricType) {
    if (metricType === "temperature") {
        return "#e74c3c";
    }

    if (metricType === "rain") {
        return "#3498db";
    }

    return "#27ae60";
}

/**
 * Dibuja una leyenda simple.
 */
function renderLegend(chartGroup, items) {
    const legendGroup = chartGroup
        .append("g")
        .attr("transform", "translate(10, 10)");

    items.forEach((item, index) => {
        const row = legendGroup
            .append("g")
            .attr("transform", `translate(${index * 110}, 0)`);

        row
            .append("line")
            .attr("x1", 0)
            .attr("x2", 20)
            .attr("y1", 0)
            .attr("y2", 0)
            .attr("stroke", item.color)
            .attr("stroke-width", 3);

        row
            .append("text")
            .attr("x", 28)
            .attr("y", 4)
            .style("font-size", "12px")
            .text(item.label);
    });
}

initializeApp();