import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";
import { VALENCE_COLOR_SCALE } from "./husformer_a1_chart.js";

// Tamaño del nodo -- canal ÁREA, codifica el GRADO del nodo en esta red
// (2026-07-22, reemplaza |valencia - 5|, que resultaba redundante con el
// color -- el propio color divergente ya muestra "qué tan extremo" es un
// trial vía cuán saturado se ve). Adaptación fiel del mapa de enfermedades
// de Goh et al. (NYT 2008): ahí el tamaño = cantidad de genes asociados,
// que determina cuántas conexiones POTENCIALES tiene esa enfermedad. Acá,
// tamaño = conexiones REALES en esta red -- cada trial tiene como mínimo
// sus propios top_k_neighbors (los que él mismo eligió), más cuantos otros
// lo eligieron a él de vuelta. Nodo grande = firma de fusión "típica"
// (muchos otros se le parecen); nodo en el mínimo = firma "rara" que nadie
// más reconoció como parecida -- candidato a investigar como caso atípico.
// Dominio dinámico (no fijo) -- se ajusta al mín/máx real de ESTE grafo en
// renderHusformerA3NetworkChart, mismo criterio que la escala de color de
// B1 (Aigner Cap. 4, expansión del rango de valores).
const NODE_RADIUS_SCALE = d3.scaleSqrt().range([2.5, 11]);

const MAX_SELECTED_TRIALS = 4;

let clipIdCounter = 0;

/**
 * Renderiza A3 (mapa de patrones de fusión cross-modal entre trials, Vista
 * A -- 2026-07-22, reemplaza el panel de perfil de cuestionario).
 *
 * INSPIRACIÓN Y ADAPTACIÓN -- mapa de enfermedades y genes compartidos del
 * NYT (2008, Goh et al., "diseasome"), visto en la actividad de clase sobre
 * Marks and Channels: ahí, nodo = enfermedad, arista = gen compartido,
 * tamaño = cantidad de genes asociados (que en la práctica determina
 * cuántas conexiones POTENCIALES tiene esa enfermedad con las demás),
 * color = categoría médica. Acá: nodo = trial, arista = firma de atención
 * cross-modal parecida (top-k vecinos, NO todos los pares posibles -- ver
 * compute_trial_pattern_network en el backend para la justificación
 * completa), tamaño = GRADO REAL del nodo en esta red (adaptación fiel del
 * ejemplo -- ya no cantidad potencial de conexiones, sino la cantidad
 * real que tiene acá), color = valencia (reusa la MISMA escala divergente
 * azul-naranja de A1, Share Encoding -- Munzner Cap. 12.3.1).
 *
 * ⚠️ Corrección de diseño (2026-07-22): la primera versión usaba el tamaño
 * para |valencia - 5| (qué tan extrema es la valencia) -- Russell notó que
 * esto era REDUNDANTE con el color: la escala divergente ya muestra "qué
 * tan extremo" vía cuán saturado se ve (cerca de 5 = pálido, cerca de 1/9 =
 * vívido), así que el tamaño repetía la misma información dos veces. Se
 * cambió a grado de conexión -- no redundante con color (una cosa es la
 * valencia reportada, otra distinta es qué tan típica/rara es la firma de
 * fusión), y es además la adaptación más fiel al propio ejemplo del mapa
 * de enfermedades que lo inspiró.
 *
 * Igual que en el mapa de enfermedades, la POSICIÓN de cada nodo es
 * resultado de un layout de fuerza (d3-force) -- NO codifica ningún
 * atributo elegido, es la misma "trampa" de los node-link diagrams que ya
 * identificamos en la actividad de clase: agrupa visualmente lo conectado,
 * pero no es un canal real.
 *
 * ¿Qué canales visuales se utilizan?
 * - El canal color (hue, escala divergente) codifica el atributo valencia
 *   reportada del trial.
 * - El canal área (tamaño del nodo) codifica el atributo grado del nodo
 *   (cantidad de conexiones) en esta red de similitud.
 * - La posición NO codifica ningún atributo -- es resultado del layout de
 *   fuerza (simulación física), no una decisión de codificación.
 *
 * ¿Qué marcas se utilizan?
 * - Una marca de tipo punto representa el ítem trial.
 * - Una marca de tipo línea (de conexión) representa el ítem relación de
 *   similitud de firma de atención cross-modal entre dos trials.
 *
 * SIMULACIÓN CORRIDA DE UNA (no animada tick a tick): con 1280 nodos,
 * re-renderizar en cada tick de la simulación sería lento -- se corren
 * ~300 ticks de forma síncrona ANTES de dibujar nada, y se pinta una sola
 * vez con las posiciones ya estables (mismo patrón recomendado en la
 * documentación de d3-force para grafos con muchos nodos).
 */
export function renderHusformerA3NetworkChart({
    containerId,
    networkData,
    selectedTrials,
    onNodeToggle,
    onBackgroundClick,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-a3-tooltip").remove();

    if (!networkData || !networkData.nodes || networkData.nodes.length === 0) {
        container.innerHTML = '<div class="husformer-b1-empty">Cargando...</div>';
        return null;
    }

    const width = container.clientWidth || 360;
    const height = container.clientHeight || 300;

    // d3-force muta los objetos de nodos/aristas (les agrega x/y, etc.) --
    // se clonan livianamente para no pisar networkData entre renders (p.ej.
    // al cambiar de tamaño de panel y volver a llamar a esta función).
    const nodes = networkData.nodes.map((node) => ({ ...node }));
    const edges = networkData.edges.map((edge) => ({ ...edge }));

    // Dominio dinámico del tamaño -- se ajusta al mín/máx real de grado de
    // ESTE grafo (ver justificación completa junto a NODE_RADIUS_SCALE más
    // arriba). Se fija ANTES de armar la simulación porque forceCollide ya
    // necesita el radio real de cada nodo para evitar que se superpongan.
    NODE_RADIUS_SCALE.domain(d3.extent(nodes, (node) => node.degree));

    const simulation = d3
        .forceSimulation(nodes)
        .force(
            "link",
            d3
                .forceLink(edges)
                .id((node) => node.index)
                .distance(18)
                .strength(0.35)
        )
        .force("charge", d3.forceManyBody().strength(-6))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force(
            "collide",
            d3.forceCollide((node) => NODE_RADIUS_SCALE(node.degree) + 1)
        )
        .stop();

    for (let tick = 0; tick < 300; tick += 1) {
        simulation.tick();
    }

    const svg = d3
        .select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    clipIdCounter += 1;
    const clipId = `husformer-a3-clip-${clipIdCounter}`;

    svg
        .append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("width", width)
        .attr("height", height);

    const zoomGroup = svg.append("g").attr("clip-path", `url(#${clipId})`);

    // Rectángulo de fondo transparente -- captura clicks fuera de cualquier
    // nodo para limpiar la selección (mismo patrón que A1/A2).
    zoomGroup
        .append("rect")
        .attr("width", width)
        .attr("height", height)
        .attr("fill", "transparent")
        .on("click", () => {
            if (onBackgroundClick) {
                onBackgroundClick();
            }
        });

    const plotGroup = zoomGroup.append("g");

    const nodeKey = (node) => `${node.participant_id}_${node.trial}`;
    const isSelected = (node) => selectedTrials?.has(nodeKey(node)) ?? false;

    // NOTA (bug real, corregido 2026-07-22): d3.forceLink MUTA edge.source/
    // edge.target -- deja de ser el índice numérico original y pasa a ser
    // el OBJETO de nodo ya resuelto (comportamiento propio de d3-force, no
    // algo opcional). Por eso acá se usa edge.source.x directo, NO
    // nodeByIndex.get(edge.source) -- esa búsqueda con un objeto como clave
    // de un Map indexado por número siempre fallaba en silencio (undefined
    // -> el ?? 0 lo tapaba), dejando todas las aristas colapsadas en (0,0)
    // sin lanzar ningún error visible.
    plotGroup
        .selectAll(".husformer-a3-edge")
        .data(edges)
        .enter()
        .append("line")
        .attr("class", "husformer-a3-edge")
        .attr("x1", (edge) => edge.source.x)
        .attr("y1", (edge) => edge.source.y)
        .attr("x2", (edge) => edge.target.x)
        .attr("y2", (edge) => edge.target.y)
        .attr("stroke", "#9ca3af")
        .attr("stroke-width", 0.6)
        .attr("stroke-opacity", 0.45);

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "husformer-b1-tooltip husformer-a3-tooltip")
        .style("opacity", 0);

    const nodeSelection = plotGroup
        .selectAll(".husformer-a3-node")
        .data(nodes)
        .enter()
        .append("circle")
        .attr("class", "husformer-a3-node")
        .attr("cx", (node) => node.x)
        .attr("cy", (node) => node.y)
        .attr("r", (node) => NODE_RADIUS_SCALE(node.degree))
        .attr("fill", (node) => VALENCE_COLOR_SCALE(node.valence))
        .attr("stroke", (node) => (isSelected(node) ? "#0d9488" : "#ffffff"))
        .attr("stroke-width", (node) => (isSelected(node) ? 2 : 0.6))
        .attr("cursor", "pointer");

    // Hover -- resalta los vecinos DIRECTOS del nodo (mismo espíritu que el
    // resaltado de columna de B1: contorno en el foco, opacidad reducida en
    // el resto, sin tocar el color de relleno que ya codifica valencia).
    // Mismo cuidado que arriba: edge.source/edge.target ya son objetos de
    // nodo (no índices) en este punto, así que se usa .index sobre el
    // objeto ya resuelto.
    const neighborsByIndex = new Map(nodes.map((node) => [node.index, new Set()]));
    edges.forEach((edge) => {
        neighborsByIndex.get(edge.source.index)?.add(edge.target.index);
        neighborsByIndex.get(edge.target.index)?.add(edge.source.index);
    });

    nodeSelection
        .on("mouseover", function (event, node) {
            const neighbors = neighborsByIndex.get(node.index) ?? new Set();

            nodeSelection.attr("opacity", (other) => (
                other.index === node.index || neighbors.has(other.index) ? 1 : 0.25
            ));

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>${node.participant_id ? `Participante ${node.participant_id}` : ""} · Trial ${node.trial}</strong>
                    <div class="husformer-b1-tooltip-row">
                        <span>Valencia</span>
                        <span>${node.valence.toFixed(1)}</span>
                    </div>
                    <div class="husformer-b1-tooltip-row">
                        <span>Conexiones (grado)</span>
                        <span>${node.degree}</span>
                    </div>
                `)
                .style("left", `${event.pageX + 14}px`)
                .style("top", `${event.pageY - 18}px`);
        })
        .on("mouseout", () => {
            nodeSelection.attr("opacity", 1);
            tooltip.style("opacity", 0);
        })
        .on("click", (event, node) => {
            event.stopPropagation();
            if (onNodeToggle) {
                onNodeToggle(node);
            }
        });

    // Zoom/pan -- con 1280 nodos en un panel chico, clickear con precisión
    // sin poder acercarse no es viable. Rango de escala amplio (0.05 a 15)
    // porque el ajuste automático de abajo puede necesitar alejarse mucho
    // más que 1x si el layout de fuerza quedó más grande que el panel.
    const zoomBehavior = d3
        .zoom()
        .scaleExtent([0.01, 15])
        .on("zoom", (event) => {
            plotGroup.attr("transform", event.transform);
        });

    svg.call(zoomBehavior);

    // Encuadre automático (2026-07-22, a pedido de Russell -- el grafo no
    // entraba en el panel sin arrastrar el mouse). Calcula el rectángulo
    // que ocupan TODOS los nodos ya asentados (tras los 300 ticks) y arma
    // una transformación de zoom/pan que lo hace entrar completo en el
    // SVG, con un margen -- se aplica como transform INICIAL sobre el
    // mismo zoomBehavior (no un mecanismo aparte), así el usuario puede
    // seguir haciendo zoom/pan libremente desde ese punto de partida.
    const xExtent = d3.extent(nodes, (node) => node.x);
    const yExtent = d3.extent(nodes, (node) => node.y);
    const contentWidth = Math.max(xExtent[1] - xExtent[0], 1);
    const contentHeight = Math.max(yExtent[1] - yExtent[0], 1);
    const contentCenterX = (xExtent[0] + xExtent[1]) / 2;
    const contentCenterY = (yExtent[0] + yExtent[1]) / 2;

    const fitPadding = 0.85; // deja ~15% de margen alrededor
    const fitScale = Math.min(
        (width / contentWidth) * fitPadding,
        (height / contentHeight) * fitPadding,
        15
    );

    const fitTransform = d3.zoomIdentity
        .translate(width / 2, height / 2)
        .scale(fitScale)
        .translate(-contentCenterX, -contentCenterY);

    svg.call(zoomBehavior.transform, fitTransform);

    return null;
}
