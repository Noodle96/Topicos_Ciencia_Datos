import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

/**
 * Renderiza C2 -- comparación de VAD (Valencia/Activación/Dominancia/
 * Liking) autorreportado, UNA tarjeta por trial actualmente seleccionado en
 * A1/A2 (nuevo, 2026-07-22 -- ver husformer_a3_resumen_implementacion.md
 * Sección 4 / conversación de diseño de Vista C).
 *
 * Mismo idiom de Small Multiples que C1 (una tarjeta por trial, mismo
 * orden), a propósito: C1 y C2 muestran DOS aspectos distintos de los
 * MISMOS trials -- alinear su arreglo espacial ayuda a cruzar visualmente
 * "esta firma de fusión" con "este estado afectivo reportado" (Munzner Cap.
 * 12.3.1, Share Encoding -- comparten arreglo aunque no comparten canal de
 * codificación en sí).
 *
 * Justificación de fondo (G3 -- "relacionar los patrones de atención con...
 * el conocimiento del dominio"): si C1 muestra que dos trials tienen
 * firmas de fusión visualmente distintas, C2 permite chequear si también
 * difieren en VAD (relación esperada) o si son similares en VAD a pesar de
 * fusionar distinto (relación NO esperada, caso interesante a investigar).
 * Tapa además un hueco documentado en A1 (Valencia es el único VAD con
 * canal visual propio ahí -- Activación/Dominancia/Liking solo estaban en
 * el tooltip).
 */
const VAD_SCALE_MIN = 1;
const VAD_SCALE_MAX = 9;

// Un color por dimensión, fijo -- NO se reutilizan los colores de modalidad
// (EEG/EOG/etc.) para no sugerir una asociación falsa entre "modalidad
// fisiológica" y "dimensión VAD", que son conceptos distintos.
const VAD_DIMENSIONS = [
    { key: "Valence", label: "Valencia", color: "#ea580c" },
    { key: "Arousal", label: "Activación", color: "#0891b2" },
    { key: "Dominance", label: "Dominancia", color: "#7c3aed" },
    { key: "Liking", label: "Liking", color: "#16a34a" },
];

const BAR_HEIGHT = 12;
const BAR_GAP = 4;
const BAR_MAX_WIDTH = 90;
const LABEL_WIDTH = 60;
const CARD_PADDING = 6;

function renderTrialCard({ container, trialEntry, xScale, tooltip }) {
    const width = LABEL_WIDTH + BAR_MAX_WIDTH + 30;
    const height = VAD_DIMENSIONS.length * (BAR_HEIGHT + BAR_GAP);

    const card = container
        .append("div")
        .attr("class", "husformer-c2-card");

    card
        .append("div")
        .attr("class", "husformer-c2-card-label")
        .text(`S${String(trialEntry.participant_id).padStart(2, "0")} · Trial ${trialEntry.trial}`);

    const svg = card
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    VAD_DIMENSIONS.forEach((dimension, index) => {
        const value = trialEntry[dimension.key];
        const rowY = index * (BAR_HEIGHT + BAR_GAP);

        const row = svg.append("g").attr("transform", `translate(0, ${rowY})`);

        row
            .append("text")
            .attr("class", "husformer-c2-bar-label")
            .attr("x", LABEL_WIDTH - 4)
            .attr("y", BAR_HEIGHT / 2)
            .attr("text-anchor", "end")
            .attr("dominant-baseline", "middle")
            .text(dimension.label);

        row
            .append("rect")
            .attr("class", "husformer-c2-bar-track")
            .attr("x", LABEL_WIDTH)
            .attr("y", 0)
            .attr("width", BAR_MAX_WIDTH)
            .attr("height", BAR_HEIGHT);

        if (value !== null && value !== undefined) {
            row
                .append("rect")
                .attr("x", LABEL_WIDTH)
                .attr("y", 0)
                .attr("width", Math.max(2, xScale(value)))
                .attr("height", BAR_HEIGHT)
                .attr("fill", dimension.color)
                .on("mousemove", (event) => {
                    tooltip
                        .style("opacity", 1)
                        .html(`
                            <strong>${dimension.label}</strong>
                            Trial: S${String(trialEntry.participant_id).padStart(2, "0")} · ${trialEntry.trial}<br/>
                            Valor: ${value.toFixed(1)} / 9
                        `)
                        .style("left", `${event.pageX + 12}px`)
                        .style("top", `${event.pageY - 16}px`);
                })
                .on("mouseleave", () => {
                    tooltip.style("opacity", 0);
                });

            row
                .append("text")
                .attr("x", LABEL_WIDTH + BAR_MAX_WIDTH + 4)
                .attr("y", BAR_HEIGHT / 2)
                .attr("dominant-baseline", "middle")
                .attr("class", "husformer-c2-bar-value")
                .text(value.toFixed(1));
        } else {
            row
                .append("text")
                .attr("x", LABEL_WIDTH + 4)
                .attr("y", BAR_HEIGHT / 2)
                .attr("dominant-baseline", "middle")
                .attr("class", "husformer-c2-bar-na")
                .text("—");
        }
    });
}

export function renderHusformerC2VadChart({ containerId, trialsData }) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-c2-tooltip").remove();

    if (!trialsData) {
        container.innerHTML = '<div class="husformer-b1-empty">Cargando...</div>';
        return;
    }

    if (trialsData.length === 0) {
        container.innerHTML = '<div class="husformer-b1-empty">Selecciona uno o más trials en Vista A para comparar su VAD autorreportado.</div>';
        return;
    }

    const xScale = d3
        .scaleLinear()
        .domain([VAD_SCALE_MIN, VAD_SCALE_MAX])
        .range([0, BAR_MAX_WIDTH])
        .clamp(true);

    const scrollRow = d3
        .select(container)
        .append("div")
        .attr("class", "husformer-c2-scroll-row");

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "husformer-c2-tooltip")
        .style("opacity", 0);

    trialsData.forEach((trialEntry) => {
        renderTrialCard({ container: scrollRow, trialEntry, xScale, tooltip });
    });
}
