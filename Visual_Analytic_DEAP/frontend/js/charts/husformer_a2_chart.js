import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// Escala de color CATEGÓRICA para clusters -- a diferencia de A1 (Valencia,
// escala DIVERGENTE porque es un atributo cuantitativo con punto medio
// significativo), el cluster es un atributo CATEGÓRICO sin orden implícito,
// así que corresponde un canal de identidad (hue), no de magnitud -- mismo
// principio de expresividad ya aplicado en A1/A3 (Cap. 5 de Munzner).
//
// d3.schemeSet3 (paleta cualitativa de ColorBrewer, 12 colores) se eligió
// porque el preset más grande de KMeans es k=12 -- justo en el límite
// superior de bins categóricos discriminables en regiones pequeñas no
// contiguas (6-12 bins, Cap. 10 de Munzner). Nota honesta: Set3 es la
// paleta categórica estándar de ColorBrewer, pero no está curada
// específicamente para daltonismo como sí lo está la escala divergente de
// A1 -- si en algún momento se detecta un problema real de accesibilidad
// con k=12, revisar contra un simulador de daltonismo (recomendación
// explícita del Cap. 10 de Munzner, sección 10.3.4).
const CLUSTER_COLOR_SCALE = d3.scaleOrdinal(d3.schemeSet3).domain(d3.range(12));

// Ruido (label -1, solo HDBSCAN) -- mismo gris neutro ya usado en A1 para
// "sin valor" (Valence === null), por consistencia visual dentro del CMV.
const NOISE_CLUSTER_COLOR = "#9ca3af";

export function getClusterColor(clusterId) {
    return clusterId === -1 ? NOISE_CLUSTER_COLOR : CLUSTER_COLOR_SCALE(clusterId);
}

export { NOISE_CLUSTER_COLOR };

const DEFAULT_POINT_OPACITY = 0.97;
const DEFAULT_POINT_RADIUS = 2.6;

// Puntos que NO pertenecen al cluster elegido en el desplegable (ver
// selectedClusterId más abajo) -- mismos niveles de contraste que A1 para
// mantener el mismo lenguaje visual dentro del CMV.
const DIMMED_POINT_OPACITY = 0.08;
const DIMMED_POINT_RADIUS = 1.4;

const HIGHLIGHTED_POINT_OPACITY = 1;
const HIGHLIGHTED_POINT_RADIUS = 3.4;

const DEFAULT_POINT_STROKE = "rgba(17, 24, 39, 0.35)";
const DEFAULT_POINT_STROKE_WIDTH = 0.6;
const SELECTED_POINT_STROKE_WIDTH = 1.4;
const SELECTED_POINT_RADIUS = 5.5;

let zoomIdCounter = 0;

/**
 * Construye la clave única de un trial -- duplicada a propósito (ver la
 * misma nota en husformer_a1_chart.js/husformer_main.js).
 */
function getTrialKey(point) {
    return `${point.Participant_id}_${point.Trial}`;
}

/**
 * Renderiza el sub-panel A2 (mismo layout de puntos que A1 -- misma
 * proyección PCA/UMAP/t-SNE compartida, ver husformer_main.js -- pero
 * coloreado por cluster en vez de por Valencia).
 *
 * `points` ya viene fusionado por husformer_main.js: cada elemento tiene
 * los mismos campos que un punto de A1 (x, y, Participant_id, Trial, ...)
 * MÁS `cluster` (int, -1 = ruido solo para HDBSCAN) agregado desde
 * /api/husformer/trial-clusters.
 *
 * `selectedClusterId`: null = "Todos" (sin resaltado por cluster, todos los
 * puntos en nivel DEFAULT); un número = solo ese cluster queda resaltado,
 * el resto se atenúa -- mismo mecanismo de precedencia visual que los
 * filtros de A1 (isPointDimmed/isPointHighlighted), pero la condición es
 * "pertenece al cluster elegido" en vez de "matchea el filtro de
 * participante/trial".
 *
 * `selectedTrials` es el MISMO Map compartido con A1 (no una copia) --
 * clickear un punto en A2 alterna su selección igual que en A1, y esa
 * selección se refleja en A3 también (linked highlighting/compound
 * brushing entre las tres vistas coordinadas de Vista A, Cap. 12 de
 * Munzner / Cap. 5 de Aigner).
 */
export function renderHusformerA2Chart({
    containerId,
    points,
    selectedTrials,
    selectedClusterId,
    onPointClick,
    onBackgroundClick,
    initialZoomTransform,
    onZoomChange,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-a2-tooltip").remove();

    if (!points || points.length === 0) {
        container.innerHTML = "<p>No points available.</p>";
        return;
    }

    const selection = selectedTrials ?? new Map();

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

    zoomIdCounter += 1;
    const clipId = `husformer-a2-clip-${zoomIdCounter}`;

    svg
        .append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("width", plotWidth)
        .attr("height", plotHeight);

    const plotGroup = svg
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    plotGroup
        .append("rect")
        .attr("class", "husformer-a2-background")
        .attr("width", plotWidth)
        .attr("height", plotHeight)
        .attr("fill", "transparent")
        .on("click", () => {
            if (onBackgroundClick) {
                onBackgroundClick();
            }
        });

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

    const xAxisGroup = plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .attr("font-size", "8px")
        .call(d3.axisBottom(xScale).ticks(4).tickSize(3));

    const yAxisGroup = plotGroup
        .append("g")
        .attr("font-size", "8px")
        .call(d3.axisLeft(yScale).ticks(4).tickSize(3));

    const pointsGroup = plotGroup
        .append("g")
        .attr("clip-path", `url(#${clipId})`)
        .append("g")
        .attr("class", "husformer-a2-points-group");

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "husformer-a2-tooltip")
        .style("opacity", 0);

    function isPointSelected(point) {
        return selection.has(getTrialKey(point));
    }

    function isClusterFilterActive() {
        return selectedClusterId !== null && selectedClusterId !== undefined;
    }

    function isPointDimmed(point) {
        if (!isClusterFilterActive()) {
            return false;
        }

        return Number(point.cluster) !== Number(selectedClusterId);
    }

    function isPointHighlighted(point) {
        return isClusterFilterActive() && !isPointDimmed(point);
    }

    function radiusFor(point) {
        if (isPointSelected(point)) return SELECTED_POINT_RADIUS;
        if (isPointDimmed(point)) return DIMMED_POINT_RADIUS;
        if (isPointHighlighted(point)) return HIGHLIGHTED_POINT_RADIUS;
        return DEFAULT_POINT_RADIUS;
    }

    function opacityFor(point) {
        if (isPointSelected(point)) return 1;
        if (isPointDimmed(point)) return DIMMED_POINT_OPACITY;
        if (isPointHighlighted(point)) return HIGHLIGHTED_POINT_OPACITY;
        return DEFAULT_POINT_OPACITY;
    }

    const pointSelection = pointsGroup
        .selectAll(".husformer-a2-point")
        .data(points)
        .enter()
        .append("circle")
        .attr("class", "husformer-a2-point")
        .attr("cx", (d) => xScale(Number(d.x)))
        .attr("cy", (d) => yScale(Number(d.y)))
        .attr("r", (d) => radiusFor(d))
        .attr("fill", (d) => getClusterColor(Number(d.cluster)))
        .attr("opacity", (d) => opacityFor(d))
        .attr("stroke", (d) => (isPointSelected(d) ? "#111827" : DEFAULT_POINT_STROKE))
        .attr("stroke-width", (d) => (
            isPointSelected(d) ? SELECTED_POINT_STROKE_WIDTH : DEFAULT_POINT_STROKE_WIDTH
        ))
        .attr("cursor", "pointer")
        .on("mouseover", function (event, d) {
            d3.select(this).attr("r", Math.max(radiusFor(d), 6)).attr("opacity", 1);

            const clusterLabel = Number(d.cluster) === -1 ? "Ruido (-1)" : `Cluster ${d.cluster}`;

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Participant:</strong> ${d.Participant_label}<br>
                    <strong>Trial:</strong> ${d.Trial}<br>
                    <strong>${clusterLabel}</strong>
                `)
                .style("left", `${event.pageX + 14}px`)
                .style("top", `${event.pageY - 18}px`);
        })
        .on("mouseout", function (event, d) {
            d3.select(this)
                .attr("r", radiusFor(d))
                .attr("opacity", opacityFor(d));

            tooltip.style("opacity", 0);
        })
        .on("click", function (event, d) {
            event.stopPropagation();

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

            const rescaledXScale = transform.rescaleX(xScale);
            const rescaledYScale = transform.rescaleY(yScale);

            xAxisGroup.call(d3.axisBottom(rescaledXScale).ticks(4).tickSize(3));
            yAxisGroup.call(d3.axisLeft(rescaledYScale).ticks(4).tickSize(3));

            const inverseScale = 1 / transform.k;

            pointSelection
                .attr("stroke-width", (d) => (
                    (isPointSelected(d) ? SELECTED_POINT_STROKE_WIDTH : DEFAULT_POINT_STROKE_WIDTH)
                    * inverseScale
                ));

            if (onZoomChange) {
                onZoomChange(transform);
            }
        });

    svg.call(zoomBehavior);

    if (initialZoomTransform) {
        svg.call(zoomBehavior.transform, initialZoomTransform);
    }
}
