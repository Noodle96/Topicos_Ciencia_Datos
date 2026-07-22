import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

// Mismo orden fijo que B1/B2 y que MODALITY_LABELS en
// husformer_attention_service.py.
const MODALITY_KEYS = ["modality_1", "modality_2", "modality_3", "modality_4", "modality_5"];

// Mismo colormap secuencial que B1 (Plasma) -- mismo tipo de dato (peso de
// atención, magnitud sin signo, sin punto de divergencia significativo), ver
// justificación completa en husformer_b1_chart.js. Se reutiliza el MISMO
// idiom visual (heatmap + Plasma) a propósito -- C1 es un "zoom" sobre una
// sola columna de B1 (una ventana puntual), compartir el lenguaje visual
// ayuda a leer C1 como una continuación de B1, no como una vista nueva sin
// relación (Share Encoding, Munzner Cap. 12.3.1).
const ATTENTION_COLOR_INTERPOLATOR = d3.interpolatePlasma;

/**
 * Renderiza C1 (matriz 5x5 de atención cross-modal de una ventana puntual,
 * Vista C).
 *
 * ESTRUCTURA -- igual que B1, matriz de dos claves (Munzner 7.3/7.5.2,
 * Matrix Alignment), pero acá AMBOS ejes son la misma categoría (modalidad),
 * no modalidad x tiempo: fila = módulo de atención cruzada que "pregunta"
 * (trans_m{i}_all), columna = modalidad fuente atendida. Es la matriz
 * attn_cross_summary CRUDA de una sola ventana -- a diferencia de B1/B2, acá
 * NO se promedia sobre ningún eje ni se reescala a porcentaje: C1 expone
 * exactamente "quién le presta atención a quién" en ese instante, que es la
 * información que B1/B2 esconden al promediar attn_final_summary sobre el
 * eje query (T4, dominancia agregada) en vez de attn_cross_summary (T6,
 * detalle fila x columna).
 *
 * QUÉ VENTANA SE MUESTRA -- C1 depende de HOVER en B1/B2 (principal) o click
 * (secundario, sigue funcionando) -- ver husformer_main.js, handleWindowSelect.
 * Cambiado de click-only a hover el 2026-07-22, a pedido de Russell: las
 * matrices cambian poco entre ventanas consecutivas, y click obligaba a un
 * click por ventana para notar la diferencia -- con hover, "barrer" el mouse
 * por B1/B2 actualiza C1 en tiempo real. Una vez que el mouse sale de B1/B2,
 * C1 se queda mostrando la ÚLTIMA ventana (sticky, no vuelve a vacío) --
 * revertir a vacío en cada mouseout haría imposible mirar C1 con calma.
 * Mientras tanto (antes del primer hover) muestra un estado vacío pidiendo
 * esa interacción.
 *
 * SIN ZOOM/SELECCIÓN PROPIA -- C1 es la vista de detalle MÁS profunda de
 * este drill-down (Vista A -> B -> C), no hay una Vista D más allá; su único
 * mecanismo de detalle-bajo-demanda es el tooltip (mismo patrón que B1).
 */
export function renderHusformerC1Chart({
    containerId,
    activeTrial,
    selectedWindowIndex,
    crossAttentionData,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-c1-tooltip").remove();

    if (!activeTrial) {
        container.innerHTML = '<div class="husformer-b1-empty">Selecciona un trial en Vista A</div>';
        return null;
    }

    if (selectedWindowIndex === null || selectedWindowIndex === undefined) {
        container.innerHTML = '<div class="husformer-b1-empty">Pasá el mouse sobre una ventana en B1/B2</div>';
        return null;
    }

    if (!crossAttentionData || !crossAttentionData.matrix) {
        container.innerHTML = '<div class="husformer-b1-empty">Cargando...</div>';
        return null;
    }

    const matrix = crossAttentionData.matrix; // (5, 5) -- fila=query, columna=fuente
    const modalityLabels = crossAttentionData.modality_labels;

    const width = container.clientWidth || 320;
    const height = container.clientHeight || 260;

    const margin = {
        top: 10,
        right: 10,
        bottom: 56, // labels largos ("Resp+Plet+Temp") rotados abajo
        left: 92, // mismo ancho que B1 -- cabe "Resp+Plet+Temp"
    };

    const svg = d3
        .select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    const plotGroup = svg
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3
        .scaleBand()
        .domain(MODALITY_KEYS)
        .range([0, Math.max(plotWidth, 0)])
        .padding(0.06);

    const yScale = d3
        .scaleBand()
        .domain(MODALITY_KEYS)
        .range([0, Math.max(plotHeight, 0)])
        .padding(0.06);

    const cellData = [];
    MODALITY_KEYS.forEach((queryKey, rowIndex) => {
        MODALITY_KEYS.forEach((sourceKey, colIndex) => {
            cellData.push({
                queryKey,
                sourceKey,
                queryLabel: modalityLabels[queryKey],
                sourceLabel: modalityLabels[sourceKey],
                value: matrix[rowIndex][colIndex],
            });
        });
    });

    // Dominio de color dinámico sobre ESTA matriz (mismo principio que B1 --
    // Aigner Cap. 4, expansión del rango de valores -- pero acá el "trial"
    // completo de referencia es una sola ventana de 5x5=25 valores, no 60
    // columnas).
    const [minValue, maxValue] = d3.extent(cellData, (d) => d.value);
    const colorScale = d3
        .scaleSequential(ATTENTION_COLOR_INTERPOLATOR)
        .domain([minValue, maxValue]);

    plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .attr("font-size", "8px")
        .call(d3.axisBottom(xScale).tickSize(3).tickFormat((key) => modalityLabels[key]))
        .selectAll("text")
        .attr("transform", "rotate(-30)")
        .style("text-anchor", "end");

    plotGroup
        .append("g")
        .attr("font-size", "8px")
        .call(d3.axisLeft(yScale).tickSize(3).tickFormat((key) => modalityLabels[key]));

    // Etiquetas de eje -- "Fuente" (columnas, quién es atendido) y "Pregunta"
    // (filas, quién atiende) -- sin esto, dos ejes categóricos idénticos (las
    // mismas 5 modalidades en ambos) serían ambiguos sobre cuál es cuál.
    svg
        .append("text")
        .attr("x", margin.left + plotWidth / 2)
        .attr("y", height - 4)
        .attr("text-anchor", "middle")
        .attr("font-size", "8px")
        .attr("fill", "#6b7280")
        .text("Modalidad fuente (atendida)");

    svg
        .append("text")
        .attr("transform", "rotate(-90)")
        .attr("x", -(margin.top + plotHeight / 2))
        .attr("y", 10)
        .attr("text-anchor", "middle")
        .attr("font-size", "8px")
        .attr("fill", "#6b7280")
        .text("Módulo que pregunta");

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "husformer-b1-tooltip husformer-c1-tooltip")
        .style("opacity", 0);

    plotGroup
        .selectAll(".husformer-c1-cell")
        .data(cellData)
        .enter()
        .append("rect")
        .attr("class", "husformer-c1-cell")
        .attr("x", (d) => xScale(d.sourceKey))
        .attr("y", (d) => yScale(d.queryKey))
        .attr("width", xScale.bandwidth())
        .attr("height", yScale.bandwidth())
        .attr("fill", (d) => colorScale(d.value))
        .on("mouseover", function (event, d) {
            d3.select(this).attr("stroke", "#111827").attr("stroke-width", 1.6);

            tooltip
                .style("opacity", 1)
                .html(`
                    <div class="husformer-b1-tooltip-row husformer-b1-tooltip-row-active">
                        <span>${d.queryLabel} → ${d.sourceLabel}</span>
                        <span>${d.value.toFixed(4)}</span>
                    </div>
                `)
                .style("left", `${event.pageX + 14}px`)
                .style("top", `${event.pageY - 18}px`);
        })
        .on("mouseout", function () {
            d3.select(this).attr("stroke", "none");
            tooltip.style("opacity", 0);
        });

    return null;
}
