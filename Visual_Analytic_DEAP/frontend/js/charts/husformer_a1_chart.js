import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// Escala de color de Valencia -- AZUL-NARANJA divergente, NO rojo-verde.
// Corrección (2026-07-07): la versión original usaba RdYlGn, que es
// prácticamente ilegible para daltonismo rojo-verde (~8% de hombres), la
// forma más común de daltonismo -- un problema de accesibilidad conocido en
// visualización de datos, no una preferencia estética. Azul y naranja son
// casi complementarios y se distinguen bien bajo cualquier tipo de visión
// del color, por eso es la sustitución estándar recomendada para pares
// rojo-verde. Los 3 colores están hardcodeados (no un interpolador nombrado
// de d3) para que coincidan exactamente con el degradado CSS de la leyenda
// (.husformer-a1-legend-bar en layout.css) -- si se cambia uno, hay que
// cambiar el otro a mano.
// Colores subidos de intensidad (2026-07-07, a pedido de Russell) respecto
// a la primera versión (#2166ac/#f7f7f7/#e08214, tonos ColorBrewer más
// apagados) -- mismo par azul-naranja colorblind-safe, versión más vívida/
// saturada. DEBEN coincidir a mano con el degradado CSS de la leyenda
// (.husformer-a1-legend-bar en layout.css) -- si se cambia uno, cambiar el
// otro.
const VALENCE_LOW_COLOR = "#1d4ed8";   // valencia baja (~1) -- azul vívido
const VALENCE_MID_COLOR = "#f3f4f6";   // valencia media (~5) -- gris casi blanco
const VALENCE_HIGH_COLOR = "#ea580c";  // valencia alta (~9) -- naranja vívido

const VALENCE_COLOR_SCALE = d3
    .scaleDiverging()
    .domain([1, 5, 9])
    .interpolator(
        d3.interpolateRgbBasis([
            VALENCE_LOW_COLOR,
            VALENCE_MID_COLOR,
            VALENCE_HIGH_COLOR,
        ])
    );

// Opacidad/trazo por defecto -- subida de nuevo (2026-07-07, segunda vuelta
// de "más intensidad": 0.75 -> 0.92 -> 0.97 ahora). DIMMED_POINT_OPACITY es
// NUEVO: nivel de atenuación para puntos que no matchean un filtro activo
// de participante/trial (ver isPointDimmed más abajo) -- previamente no
// existía un tercer nivel de opacidad, solo seleccionado/normal.
const DEFAULT_POINT_OPACITY = 0.97;
const DIMMED_POINT_OPACITY = 0.15;
const DEFAULT_POINT_STROKE = "rgba(17, 24, 39, 0.35)";
const DEFAULT_POINT_STROKE_WIDTH = 0.6;
const SELECTED_POINT_STROKE_WIDTH = 1.4;
const DEFAULT_POINT_RADIUS = 2.6;
const DIMMED_POINT_RADIUS = 1.7;
const SELECTED_POINT_RADIUS = 5.5;

let zoomIdCounter = 0;

/**
 * Construye la clave única de un trial (participante+trial) -- se usa para
 * indexar el Set/Map de selección múltiple. Duplicada intencionalmente en
 * husformer_main.js (es una sola línea; no se justifica un módulo de
 * utilidades compartido todavía en este frontend, que no tiene ese patrón
 * en ningún otro lado).
 */
function getTrialKey(point) {
    return `${point.Participant_id}_${point.Trial}`;
}

/**
 * Renderiza el sub-panel A1 (proyección 2D de last_hs agregado por trial).
 *
 * Sin título ni ejes descriptivos dentro del SVG -- decisión de diseño
 * (Russell, 2026-07-07): los paneles del CMV de Husformer usan solo un chip
 * corto ("A1") fuera del chart, no texto adicional que ocupe espacio. Los
 * ticks numéricos de los ejes se mantienen (orientación mínima), pero sin
 * etiquetas de eje ni título de proyección. La leyenda de color SÍ es una
 * excepción justificada a "sin texto": sin ella, la escala de color no se
 * puede interpretar -- ver `.husformer-a1-legend` en index.html/layout.css
 * (HTML/CSS, fuera de este archivo, no del SVG).
 *
 * Zoom: rueda del mouse hacia arriba acerca, hacia abajo aleja de vuelta
 * hasta el tamaño original (scaleExtent mínimo = 1). Pan por arrastre
 * incluido como complemento natural. Los ejes se RE-ESCALAN en cada evento
 * de zoom con `transform.rescaleX/rescaleY` -- quedan matemáticamente
 * sincronizados con lo que se ve (corrección pedida por Russell el
 * 2026-07-07, ver historial en estado_proyecto.md).
 *
 * Selección múltiple (2026-07-07): `selectedTrials` es un Map<string,
 * point> (clave = getTrialKey), no un único trial -- decisión tomada
 * pensando en A3 (comparación de VARIOS trials a la vez, según la
 * Sección 5). Un click en un punto alterna su membresía en el Map (lo
 * agrega si no estaba, lo quita si ya estaba) -- la lógica de qué hacer con
 * el click vive en husformer_main.js (este componente solo reporta el
 * evento vía onPointClick), este chart solo LEE el Map para decidir cómo
 * dibujar. Un click en el fondo (fuera de cualquier punto) limpia toda la
 * selección, vía onBackgroundClick.
 *
 * Filtros de resaltado (2026-07-07): `participantFilter`/`trialFilter` son
 * valores sueltos (no arrays -- son selects de un solo valor, "" = sin
 * filtro = Todos, que es el reset). Se combinan con AND: si ambos están
 * activos, solo el punto que matchea los dos queda sin atenuar. Un punto
 * "atenuado" baja de opacidad/radio (DIMMED_POINT_OPACITY/RADIUS) en vez de
 * ocultarse -- se mantiene visible a propósito, para no perder el contexto
 * de "dónde está esto respecto a todo lo demás", que es justo el tipo de
 * pregunta que estos filtros buscan responder (T1/G1).
 *
 * PRECEDENCIA VISUAL (de mayor a menor prioridad): seleccionado (click) >
 * atenuado (no matchea el filtro) > normal. Un punto seleccionado se ve
 * seleccionado SIEMPRE, incluso si un filtro activo lo dejaría atenuado --
 * la selección es una acción más deliberada e individual del usuario que un
 * filtro global, así que gana.
 */
export function renderHusformerA1Chart({
    containerId,
    points,
    projectionMethod,
    selectedTrials,
    onPointClick,
    onBackgroundClick,
    initialZoomTransform,
    onZoomChange,
    participantFilter,
    trialFilter,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-a1-tooltip").remove();

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

    // Rectángulo de fondo -- capa fija (no se mueve con el pan/zoom, a
    // diferencia de los puntos) que captura clicks en área vacía para
    // limpiar la selección. fill="transparent" (no "none") para que SÍ
    // reciba eventos de puntero pero sin pintar nada visible.
    plotGroup
        .append("rect")
        .attr("class", "husformer-a1-background")
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
        return selection.has(getTrialKey(point));
    }

    function isPointDimmed(point) {
        if (!participantFilter && !trialFilter) {
            return false;
        }

        const matchesParticipant = !participantFilter
            || Number(point.Participant_id) === Number(participantFilter);

        const matchesTrial = !trialFilter
            || Number(point.Trial) === Number(trialFilter);

        return !(matchesParticipant && matchesTrial);
    }

    function radiusFor(point) {
        if (isPointSelected(point)) return SELECTED_POINT_RADIUS;
        if (isPointDimmed(point)) return DIMMED_POINT_RADIUS;
        return DEFAULT_POINT_RADIUS;
    }

    function opacityFor(point) {
        if (isPointSelected(point)) return 1;
        if (isPointDimmed(point)) return DIMMED_POINT_OPACITY;
        return DEFAULT_POINT_OPACITY;
    }

    const pointSelection = pointsGroup
        .selectAll(".husformer-a1-point")
        .data(points)
        .enter()
        .append("circle")
        .attr("class", "husformer-a1-point")
        .attr("cx", (d) => xScale(Number(d.x)))
        .attr("cy", (d) => yScale(Number(d.y)))
        .attr("r", (d) => radiusFor(d))
        .attr("fill", (d) => (
            d.Valence === null
                ? "#9ca3af"
                : VALENCE_COLOR_SCALE(Number(d.Valence))
        ))
        .attr("opacity", (d) => opacityFor(d))
        .attr("stroke", (d) => (isPointSelected(d) ? "#111827" : DEFAULT_POINT_STROKE))
        .attr("stroke-width", (d) => (
            isPointSelected(d) ? SELECTED_POINT_STROKE_WIDTH : DEFAULT_POINT_STROKE_WIDTH
        ))
        .attr("cursor", "pointer")
        .on("mouseover", function (event, d) {
            d3.select(this).attr("r", Math.max(radiusFor(d), 6)).attr("opacity", 1);

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
                .attr("r", radiusFor(d))
                .attr("opacity", opacityFor(d));

            tooltip.style("opacity", 0);
        })
        .on("click", function (event, d) {
            // husformer-a1-background es un elemento HERMANO (no ancestro)
            // de los círculos, así que su listener de "click" no se
            // dispara por esto de todas formas -- stopPropagation() se deja
            // igual como medida defensiva, por si en el futuro algún
            // ancestro (svg, body) llega a escuchar clicks delegados.
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
                    (isPointSelected(d) ? SELECTED_POINT_STROKE_WIDTH : DEFAULT_POINT_STROKE_WIDTH)
                    * inverseScale
                ));

            // Le avisa a husformer_main.js cuál es el transform actual, para
            // que lo guarde y lo pueda devolver como initialZoomTransform la
            // próxima vez que este chart se vuelva a renderizar desde cero
            // (ver corrección de bug más abajo).
            if (onZoomChange) {
                onZoomChange(transform);
            }
        });

    svg.call(zoomBehavior);

    // BUG corregido (2026-07-07, reportado por Russell): esta función
    // reconstruye el SVG completo en cada render -- incluyendo un
    // d3.zoom() nuevo que arranca en su transform por defecto (sin zoom).
    // Como CUALQUIER interacción (seleccionar un punto, limpiar la
    // selección, redimensionar la ventana) dispara un re-render completo
    // vía renderA1() en husformer_main.js, el zoom se perdía cada vez que
    // pasaba cualquiera de esas cosas -- no solo al seleccionar un punto,
    // aunque fue ahí donde Russell lo notó primero.
    //
    // FIX: si el caller (husformer_main.js) ya tiene guardado un transform
    // de una interacción anterior, se lo pasamos acá como
    // `initialZoomTransform` y lo re-aplicamos de inmediato con
    // `zoomBehavior.transform`, que dispara el mismo handler "zoom" de
    // arriba sincrónicamente -- reutiliza exactamente la misma lógica de
    // reposicionamiento, no hay caminos de código separados que puedan
    // desincronizarse entre sí.
    if (initialZoomTransform) {
        svg.call(zoomBehavior.transform, initialZoomTransform);
    }
}
