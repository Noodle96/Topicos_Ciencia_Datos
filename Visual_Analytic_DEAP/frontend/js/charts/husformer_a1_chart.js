import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// DEAP: valencia en escala continua 1-9 (ver koelstra2012deap). Rojo = baja
// valencia (negativa), verde = alta valencia (positiva) -- codificación
// directa de G1 (contrastar la posición de un trial en el espacio de
// representación con su autorreporte subjetivo de valencia/activación/
// dominancia). Se usa valencia (no participante) como color por defecto en
// A1 porque es el eje que motiva G1, a diferencia de Tarea1 donde el color
// por participante servía a un propósito de comparación distinto.
const VALENCE_COLOR_SCALE = d3
    .scaleSequential(d3.interpolateRdYlGn)
    .domain([1, 9]);

// Opacidad/trazo por defecto -- subidos (2026-07-07, a pedido de Russell:
// "colores un poco más fuertes") respecto a la primera versión (0.75, sin
// stroke en puntos no seleccionados).
const DEFAULT_POINT_OPACITY = 0.92;
const DEFAULT_POINT_STROKE = "rgba(17, 24, 39, 0.35)";
const DEFAULT_POINT_STROKE_WIDTH = 0.6;

let zoomIdCounter = 0;

/**
 * Renderiza el sub-panel A1 (proyección 2D de last_hs agregado por trial).
 *
 * Sin título ni ejes descriptivos dentro del SVG -- decisión de diseño
 * (Russell, 2026-07-07): los paneles del CMV de Husformer usan solo un chip
 * corto ("A1") fuera del chart, no texto adicional que ocupe espacio. Los
 * ticks numéricos de los ejes se mantienen (orientación mínima), pero sin
 * etiquetas de eje ni título de proyección.
 *
 * Zoom (2026-07-07, a pedido de Russell): rueda del mouse hacia arriba
 * acerca, hacia abajo aleja de vuelta hasta el tamaño original
 * (scaleExtent mínimo = 1, no se puede alejar más que el ajuste inicial).
 * El arrastre (pan) queda habilitado junto con el zoom porque sin poder
 * desplazarse, hacer zoom en un panel chico no sirve de mucho -- Russell no
 * lo pidió explícitamente pero es el complemento natural, se lo avisé en el
 * chat.
 *
 * CORRECCIÓN (2026-07-07, Russell notó que los ejes se quedaban fijos
 * mientras los puntos se movían con el zoom -- correcto, eso rompía la
 * correspondencia entre lo que se ve y lo que dice el eje). Ahora los ejes
 * se RE-ESCALAN en cada evento de zoom con `transform.rescaleX/rescaleY`
 * (patrón estándar de D3): los puntos se mueven aplicando `event.transform`
 * directamente al grupo (barato, no recalcula cx/cy), y el eje se redibuja
 * con una escala derivada de ese mismo transform -- por construcción,
 * `rescaleX(xScale)(x)` da exactamente el mismo píxel que el transform le
 * aplicó al punto, así que ambos quedan matemáticamente sincronizados.
 */
export function renderHusformerA1Chart({
    containerId,
    points,
    projectionMethod,
    selectedTrial,
    onPointClick,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-a1-tooltip").remove();

    if (!points || points.length === 0) {
        container.innerHTML = "<p>No points available.</p>";
        return;
    }

    const width = container.clientWidth || 360;
    const height = container.clientHeight || 260;

    const margin = {
        top: 10,
        right: 10,
        bottom: 20,
        left: 28,
    };

    const svg = d3
        .select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    // Clip-path propio -- evita que los puntos se salgan visualmente del
    // área de plot cuando se hace zoom/pan (además del overflow:hidden que
    // ya tiene .cmv-panel como red de seguridad general).
    zoomIdCounter += 1;
    const clipId = `husformer-a1-clip-${zoomIdCounter}`;

    svg
        .append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("width", plotWidth)
        .attr("height", plotHeight);

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

    // Ejes -- se re-escalan en cada evento de zoom (ver docstring y el
    // handler de zoom más abajo), por eso quedan guardados en variables.
    const xAxisGroup = plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .attr("font-size", "8px")
        .call(d3.axisBottom(xScale).ticks(4).tickSize(3));

    const yAxisGroup = plotGroup
        .append("g")
        .attr("font-size", "8px")
        .call(d3.axisLeft(yScale).ticks(4).tickSize(3));

    // Grupo que sí hace zoom/pan -- solo la nube de puntos.
    const pointsGroup = plotGroup
        .append("g")
        .attr("clip-path", `url(#${clipId})`)
        .append("g")
        .attr("class", "husformer-a1-points-group");

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "husformer-a1-tooltip")
        .style("opacity", 0);

    function isPointSelected(point) {
        if (!selectedTrial) {
            return false;
        }

        return (
            Number(point.Participant_id) === Number(selectedTrial.Participant_id)
            && Number(point.Trial) === Number(selectedTrial.Trial)
        );
    }

    const pointSelection = pointsGroup
        .selectAll(".husformer-a1-point")
        .data(points)
        .enter()
        .append("circle")
        .attr("class", "husformer-a1-point")
        .attr("cx", (d) => xScale(Number(d.x)))
        .attr("cy", (d) => yScale(Number(d.y)))
        .attr("r", (d) => (isPointSelected(d) ? 5.5 : 2.6))
        .attr("fill", (d) => (
            d.Valence === null
                ? "#9ca3af"
                : VALENCE_COLOR_SCALE(Number(d.Valence))
        ))
        .attr("opacity", (d) => (isPointSelected(d) ? 1 : DEFAULT_POINT_OPACITY))
        .attr("stroke", (d) => (isPointSelected(d) ? "#111827" : DEFAULT_POINT_STROKE))
        .attr("stroke-width", (d) => (isPointSelected(d) ? 1.4 : DEFAULT_POINT_STROKE_WIDTH))
        .attr("cursor", "pointer")
        .on("mouseover", function (event, d) {
            d3.select(this).attr("r", 6).attr("opacity", 1);

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Participant:</strong> ${d.Participant_label}<br>
                    <strong>Trial:</strong> ${d.Trial}<br>
                    <strong>Split:</strong> ${d.Split}<br>
                    <strong>Valence:</strong> ${d.Valence ?? "N/A"}<br>
                    <strong>Arousal:</strong> ${d.Arousal ?? "N/A"}<br>
                    <strong>Dominance:</strong> ${d.Dominance ?? "N/A"}<br>
                    <strong>Liking:</strong> ${d.Liking ?? "N/A"}<br>
                    <strong>Ventanas agregadas:</strong> ${d.NumWindowsAggregated}<br>
                    <strong>Proyección:</strong> ${d.projection_method}
                `)
                .style("left", `${event.pageX + 14}px`)
                .style("top", `${event.pageY - 18}px`);
        })
        .on("mouseout", function (event, d) {
            d3.select(this)
                .attr("r", isPointSelected(d) ? 5.5 : 2.6)
                .attr("opacity", isPointSelected(d) ? 1 : DEFAULT_POINT_OPACITY);

            tooltip.style("opacity", 0);
        })
        .on("click", function (_, d) {
            if (onPointClick) {
                onPointClick(d);
            }
        });

    const zoomBehavior = d3
        .zoom()
        .scaleExtent([1, 12])
        .translateExtent([
            [-plotWidth * 0.5, -plotHeight * 0.5],
            [plotWidth * 1.5, plotHeight * 1.5],
        ])
        .extent([[0, 0], [plotWidth, plotHeight]])
        .on("zoom", (event) => {
            const transform = event.transform;

            pointsGroup.attr("transform", transform);

            // Ejes re-escalados con el mismo transform que ya se le aplicó
            // a los puntos -- quedan mostrando los valores x/y reales de lo
            // que se ve en pantalla, no los del rango original sin zoom.
            const rescaledXScale = transform.rescaleX(xScale);
            const rescaledYScale = transform.rescaleY(yScale);

            xAxisGroup.call(d3.axisBottom(rescaledXScale).ticks(4).tickSize(3));
            yAxisGroup.call(d3.axisLeft(rescaledYScale).ticks(4).tickSize(3));

            // El grosor de trazo/radio no debería "engordar" visualmente al
            // hacer zoom -- se compensa dividiendo por la escala actual.
            const inverseScale = 1 / transform.k;

            pointSelection
                .attr("stroke-width", (d) => (
                    (isPointSelected(d) ? 1.4 : DEFAULT_POINT_STROKE_WIDTH) * inverseScale
                ));
        });

    svg.call(zoomBehavior);
}
