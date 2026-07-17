import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

let clipIdCounter = 0;

/**
 * Extrae, de la respuesta de /api/trial-signals, los puntos de UN canal
 * reubicados en el mismo eje temporal que usan B1/B2 (window_start_sec,
 * relativo al inicio de la fase "During" -- los 60s de estímulo).
 *
 * ALINEACIÓN CRÍTICA (2026-07-17, verificado leyendo el pipeline antes de
 * implementar, no asumido): /api/trial-signals (backend/services/
 * signal_service.py, usado por H1/Tarea1) devuelve tiempos relativos al
 * REGISTRO COMPLETO del participante (incluye fases Before/During/After).
 * En cambio, `window_start_sec` de attn_final_summary (husformer_
 * attention_service.py, el dato que consume B1/B2) es relativo SOLO al
 * inicio de la fase During -- confirmado en preprocess_representation_
 * inputs.py: "Extraer 60 segundos de During desde el archivo BDF original".
 * Sin corregir este offset, la señal cruda de B3 quedaría desplazada
 * respecto a la atención de B2 -- exactamente el tipo de error que
 * invalidaría T5 (relacionar picos de atención con eventos en la señal),
 * el propósito entero de este panel. Se resta el `start` de la fase
 * "During" (viene en signalResponse.phases) a cada timestamp, y se recorta
 * a[0, ~60s] para quedar en el mismo rango que B1/B2.
 */
function extractDuringPhaseSamples(signalResponse, channelName) {
    const duringPhase = signalResponse.phases.find((phase) => phase.name === "During");

    if (!duringPhase) {
        return [];
    }

    const rawSamples = signalResponse.signals[channelName] ?? [];

    return rawSamples
        .map((sample) => ({
            time: sample.time - duringPhase.start,
            value: sample.value,
        }))
        .filter((sample) => (
            sample.time >= 0
            && sample.time <= (duringPhase.end - duringPhase.start)
            && sample.value !== null
        ));
}

/**
 * Renderiza el panel superior de B3: la señal fisiológica cruda de UN canal
 * seleccionado, a lo largo de toda la fase During del trial (0 a ~60s,
 * mismo rango que el panel de atención de abajo, que reutiliza
 * husformer_b2_chart.js sin modificarlo).
 *
 * JUXTAPOSE, no superimpose (Munzner Cap. 12.5.2, hallazgo de Javed et al.
 * 2010): "superponer es mejor para comparaciones LOCALES (un punto
 * temporal específico); juxtaponer es mejor para tareas GLOBALES
 * DISPERSAS, especialmente con más series" -- T5 (relacionar picos de
 * atención con eventos en la señal a lo largo de TODO el trial) es una
 * tarea global dispersa, no un chequeo puntual. Argumento adicional (Cap.
 * 12.2): superimponer tiene un límite duro de capas (2 muy viable, 3 con
 * cuidado) -- el panel de atención ya tiene 5 líneas, agregar la señal
 * cruda encima en el mismo eje sería inviable. Por eso este panel vive
 * SEPARADO, apilado arriba del panel de atención, compartiendo el eje X
 * (tiempo) -- "Share Navigation: Synchronize" (Cap. 12.3.3) es el target a
 * futuro (zoom sincronizado entre ambos), no implementado en esta primera
 * versión (ver "Qué NO está resuelto" en el .md).
 */
export function renderHusformerB3SignalChart({ containerId, activeTrial, signalData, channelName }) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    d3.select(".husformer-b3-tooltip").remove();

    if (!activeTrial) {
        container.innerHTML = '<div class="husformer-b1-empty">Selecciona un trial en Vista A</div>';
        return;
    }

    if (!signalData) {
        container.innerHTML = '<div class="husformer-b1-empty">Cargando...</div>';
        return;
    }

    const samples = extractDuringPhaseSamples(signalData, channelName);

    if (samples.length === 0) {
        container.innerHTML = '<div class="husformer-b1-empty">Sin datos para este canal.</div>';
        return;
    }

    const width = container.clientWidth || 360;
    const height = container.clientHeight || 140;

    const margin = {
        top: 8,
        right: 10,
        bottom: 18,
        left: 44, // ancho fijo compartido con husformer_b2_chart.js NO es
                  // necesario pixel-perfecto acá (son 2 SVGs separados,
                  // ver nota en el .md) -- se deja consistente a ojo.
    };

    const svg = d3
        .select(container)
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const plotWidth = width - margin.left - margin.right;
    const plotHeight = height - margin.top - margin.bottom;

    clipIdCounter += 1;
    const clipId = `husformer-b3-clip-${clipIdCounter}`;

    svg
        .append("clipPath")
        .attr("id", clipId)
        .append("rect")
        .attr("width", Math.max(plotWidth, 0))
        .attr("height", Math.max(plotHeight, 0));

    const plotGroup = svg
        .append("g")
        .attr("transform", `translate(${margin.left}, ${margin.top})`);

    const xScale = d3
        .scaleLinear()
        .domain(d3.extent(samples, (d) => d.time))
        .range([0, plotWidth]);

    const yScale = d3
        .scaleLinear()
        .domain(d3.extent(samples, (d) => d.value))
        .nice()
        .range([plotHeight, 0]);

    plotGroup
        .append("g")
        .attr("transform", `translate(0, ${plotHeight})`)
        .attr("font-size", "8px")
        .call(
            d3.axisBottom(xScale).ticks(6).tickSize(3).tickFormat((sec) => `${Math.round(sec)}s`)
        );

    plotGroup
        .append("g")
        .attr("font-size", "8px")
        .call(d3.axisLeft(yScale).ticks(3).tickSize(3));

    const lineGenerator = d3
        .line()
        .x((d) => xScale(d.time))
        .y((d) => yScale(d.value));

    plotGroup
        .append("g")
        .attr("clip-path", `url(#${clipId})`)
        .append("path")
        .attr("fill", "none")
        .attr("stroke", "#0f172a")
        .attr("stroke-width", 1)
        .attr("d", lineGenerator(samples));

    // Guía vertical + tooltip -- mismo patrón que B2 (bisector sobre el
    // punto más cercano en X).
    const hoverLine = plotGroup
        .append("line")
        .attr("y1", 0)
        .attr("y2", plotHeight)
        .attr("stroke", "#111827")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "3,3")
        .style("opacity", 0)
        .style("pointer-events", "none");

    const tooltip = d3
        .select("body")
        .append("div")
        .attr("class", "husformer-b3-tooltip")
        .style("opacity", 0);

    const bisectTime = d3.bisector((d) => d.time).left;

    plotGroup
        .append("rect")
        .attr("width", plotWidth)
        .attr("height", plotHeight)
        .attr("fill", "transparent")
        .on("mousemove", function (event) {
            const [mouseX] = d3.pointer(event, this);
            const hoveredTime = xScale.invert(mouseX);

            let index = bisectTime(samples, hoveredTime);
            index = Math.max(0, Math.min(samples.length - 1, index));

            const activeSample = samples[index];

            hoverLine
                .attr("x1", xScale(activeSample.time))
                .attr("x2", xScale(activeSample.time))
                .style("opacity", 1);

            tooltip
                .style("opacity", 1)
                .html(`
                    <strong>Canal: ${channelName}</strong><br>
                    Tiempo: ${activeSample.time.toFixed(1)}s<br>
                    Valor: ${activeSample.value.toFixed(2)}
                `)
                .style("left", `${event.pageX + 14}px`)
                .style("top", `${event.pageY - 18}px`);
        })
        .on("mouseleave", () => {
            hoverLine.style("opacity", 0);
            tooltip.style("opacity", 0);
        });
}
