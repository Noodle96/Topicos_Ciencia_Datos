import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

/**
 * Renderiza C1 -- Small Multiples de la matriz de atención cross-modal
 * promedio (attn_cross_summary, 5x5), UNA por trial actualmente
 * seleccionado en A1/A2 (rediseño 2026-07-22, reemplaza el C1 original de
 * UNA ventana puntual disparada por hover en B1).
 *
 * Justificación (Munzner Cap. 12.4, Small Multiples): juxtaponer la MISMA
 * codificación repetida por ítem es el idiom correcto cuando se quiere
 * comparar varios casos directamente entre sí, en vez de examinarlos de a
 * uno recordando el anterior (Cap. 6.5, "Eyes Beat Memory"). Cada matriz
 * usa la MISMA escala de color (dominio global, no por matriz) -- sin esto,
 * dos matrices con colores parecidos podrían representar magnitudes
 * distintas, invalidando la comparación visual (Aigner Cap. 4, 4.2.2:
 * tareas de comparación requieren escala compartida).
 *
 * Mismo colormap secuencial Plasma que B1/C1-original (share encoding,
 * Munzner Cap. 12.3.1) -- el usuario ya aprendió a leer "color = intensidad
 * de atención" ahí.
 */
const CROSS_ATTENTION_COLOR_INTERPOLATOR = d3.interpolatePlasma;

const CELL_SIZE = 16;
const CELL_GAP = 1;
const CARD_PADDING = 6;
const AXIS_LABEL_SPACE = 34;

function computeGlobalDomain(trialsData) {
    let min = Infinity;
    let max = -Infinity;

    trialsData.forEach((trialEntry) => {
        trialEntry.matrix.forEach((row) => {
            row.forEach((value) => {
                if (value < min) min = value;
                if (value > max) max = value;
            });
        });
    });

    if (!Number.isFinite(min) || !Number.isFinite(max)) {
        return [0, 1];
    }

    return [min, max];
}

function renderTrialCard({ container, trialEntry, modalityKeys, colorScale, tooltip }) {
    const matrixSize = modalityKeys.length * (CELL_SIZE + CELL_GAP) - CELL_GAP;
    const width = matrixSize + AXIS_LABEL_SPACE;
    const height = matrixSize + AXIS_LABEL_SPACE;

    const card = container
        .append("div")
        .attr("class", "husformer-c1-card");

    card
        .append("div")
        .attr("class", "husformer-c1-card-label")
        .text(`S${String(trialEntry.participant_id).padStart(2, "0")} · Trial ${trialEntry.trial}`);

    const svg = card
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const plotGroup = svg
        .append("g")
        .attr("transform", `translate(${AXIS_LABEL_SPACE}, ${AXIS_LABEL_SPACE})`);

    modalityKeys.forEach((rowKey, rowIndex) => {
        modalityKeys.forEach((colKey, colIndex) => {
            const value = trialEntry.matrix[rowIndex][colIndex];

            plotGroup
                .append("rect")
                .attr("x", colIndex * (CELL_SIZE + CELL_GAP))
                .attr("y", rowIndex * (CELL_SIZE + CELL_GAP))
                .attr("width", CELL_SIZE)
                .attr("height", CELL_SIZE)
                .attr("fill", colorScale(value))
                .on("mousemove", (event) => {
                    tooltip
                        .style("opacity", 1)
                        .html(`
                            <strong>${rowKey} -> ${colKey}</strong>
                            Trial: S${String(trialEntry.participant_id).padStart(2, "0")} · ${trialEntry.trial}<br/>
                            Peso: ${value.toFixed(4)}
                        `)
                        .style("left", `${event.pageX + 12}px`)
                        .style("top", `${event.pageY - 16}px`);
                })
                .on("mouseleave", () => {
                    tooltip.style("opacity", 0);
                });
        });
    });

    // Eje de filas (módulo que pregunta) -- solo en la primera columna del
    // Small Multiples tendría sentido mostrarlo una vez, pero repetirlo en
    // cada card evita ambigüedad al leer una tarjeta aislada (podrían
    // desplazarse horizontalmente si hay muchas seleccionadas).
    plotGroup
        .selectAll(".husformer-c1-row-label")
        .data(modalityKeys)
        .join("text")
        .attr("class", "husformer-c1-axis-label")
        .attr("x", -4)
        .attr("y", (_, index) => index * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2)
        .attr("text-anchor", "end")
        .attr("dominant-baseline", "middle")
        .text((label) => label);

    plotGroup
        .selectAll(".husformer-c1-col-label")
        .data(modalityKeys)
        .join("text")
        .attr("class", "husformer-c1-axis-label")
        .attr(
            "transform",
            (_, index) => `translate(${index * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2}, -4) rotate(-45)`
        )
        .attr("text-anchor", "start")
        .text((label) => label);
}

export function renderHusformerC1SmallMultiplesChart({ containerId, trialsData, modalityLabels }) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-c1-tooltip").remove();

    if (!trialsData) {
        container.innerHTML = '<div class="husformer-b1-empty">Cargando...</div>';
        return;
    }

    if (trialsData.length === 0) {
        container.innerHTML = '<div class="husformer-b1-empty">Selecciona uno o más trials en Vista A para comparar su matriz de fusión cross-modal.</div>';
        return;
    }

    const modalityKeys = Object.values(modalityLabels ?? {});
    const domain = computeGlobalDomain(trialsData);
    const colorScale = d3.scaleSequential(CROSS_ATTENTION_COLOR_INTERPOLATOR).domain(domain);

    const scrollRow = d3
        .select(container)
        .append("div")
        .attr("class", "husformer-c1-scroll-row");

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "husformer-c1-tooltip")
        .style("opacity", 0);

    trialsData.forEach((trialEntry) => {
        renderTrialCard({ container: scrollRow, trialEntry, modalityKeys, colorScale, tooltip });
    });
}
