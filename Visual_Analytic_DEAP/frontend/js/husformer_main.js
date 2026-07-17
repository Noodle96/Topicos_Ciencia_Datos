import {
    fetchHusformerTrialProjection,
    fetchHusformerTrialClusters,
    fetchHusformerTrialAttention,
    fetchH2ParticipantProfiles,
    fetchTrialSignals,
} from "./api.js";

import {
    renderHusformerA1Chart,
} from "./charts/husformer_a1_chart.js";

import {
    renderHusformerA2Chart,
    getClusterColor,
    NOISE_CLUSTER_COLOR,
} from "./charts/husformer_a2_chart.js";

import {
    renderHusformerA3Panel,
} from "./charts/husformer_a3_panel.js";

import {
    renderHusformerB1Chart,
} from "./charts/husformer_b1_chart.js";

import {
    renderHusformerB2Chart,
} from "./charts/husformer_b2_chart.js";

import {
    renderHusformerB3SignalChart,
} from "./charts/husformer_b3_chart.js";

/**
 * Construye la clave única de un trial (participante+trial). Duplicada a
 * propósito en husformer_a1_chart.js/husformer_a2_chart.js (una línea; este
 * frontend no tiene ningún módulo de utilidades compartidas todavía, no se
 * justifica crear uno solo por esto).
 */
function getTrialKey(point) {
    return `${point.Participant_id}_${point.Trial}`;
}

// Trials actualmente seleccionados -- COMPARTIDO entre A1 y A2 (el mismo
// Map, no una copia): clickear un punto en cualquiera de los dos paneles
// alterna su selección y se refleja en el otro, además de en A3. Map<key,
// point> en vez de un único trial (2026-07-07, pensado para A3 -- selección
// múltiple). Un click en un punto alterna su membresía; un click en el
// fondo (de cualquiera de los dos paneles) limpia todo.
let selectedTrials = new Map();

// Transform de zoom/pan de A1 y A2 -- SEPARADOS a propósito (cada panel
// puede estar en un nivel de zoom distinto en un momento dado, no están
// visualmente enlazados por zoom, solo comparten el mismo layout de puntos
// en su estado "sin zoom"). Mismo mecanismo que ya existía para A1: se
// guarda acá y se reaplica en cada render para no perderlo en cada
// re-render completo del SVG.
let currentZoomTransform = null;
let currentA2ZoomTransform = null;

// Filtros de resaltado de A1 (2026-07-07). "" = sin filtro. AND entre sí,
// ORTOGONALES a selectedTrials -- ver husformer_a1_chart.js.
let participantFilter = "";
let trialFilter = "";

// Método de proyección -- COMPARTIDO entre A1 y A2 (2026-07-15): A2
// reutiliza el mismo layout de puntos que A1 (mismas coordenadas x/y),
// coloreado por cluster en vez de por Valencia, así que ambos paneles
// SIEMPRE deben mostrar la misma proyección -- si no, comparar posiciones
// entre A1 y A2 dejaría de tener sentido (ver nota en husformer_trial_
// service.py y en index.html). Antes existía un DEFAULT_PROJECTION_METHOD
// usado solo por A1; ahora es un único estado compartido, con dos grupos de
// botones (uno por panel) que se mantienen sincronizados en la UI.
const DEFAULT_PROJECTION_METHOD = "pca";
let currentProjectionMethod = DEFAULT_PROJECTION_METHOD;

// Cache de los puntos ya cargados (posición 2D + VAD, de A1) -- permite
// re-renderizar ambos paneles sin volver a pedirlos al backend.
let latestPoints = null;

// Presets fijos de clustering (mismos valores que en el backend --
// husformer_trial_service.py VALID_KMEANS_K / VALID_HDBSCAN_MIN_CLUSTER_SIZE
// -- y en index.html). "specification by selection" (Cap. 5 de Aigner,
// Tominski 2011): el usuario elige de una colección curada, no un valor
// libre.
const DEFAULT_CLUSTER_METHOD = "kmeans";
const KMEANS_DEFAULT_K = 3;
const HDBSCAN_DEFAULT_MIN_CLUSTER_SIZE = 5;

let currentClusterMethod = DEFAULT_CLUSTER_METHOD;
let currentClusterParam = KMEANS_DEFAULT_K;

// Cluster resaltado en el desplegable de A2 ("Resaltar:") -- null = "Todos"
// (sin resaltado, todos los puntos en nivel DEFAULT). Se resetea a null
// cada vez que cambia el método o el preset, porque los IDs de cluster de
// una corrida no tienen ninguna relación necesaria con los de otra (p.ej.
// "cluster 2" con k=6 no es "el mismo grupo" que "cluster 2" con k=12).
let currentSelectedClusterId = null;

// Última respuesta de /trial-clusters -- { method, param_name, param_value,
// num_clusters, has_noise, points: [{Participant_id, Trial, cluster}] }.
let latestClusterData = null;

// requestId evita una condición de carrera real: si el usuario aprieta
// varios presets de clustering rápido, cada uno dispara un fetch -- sin
// esto, una respuesta vieja que llega tarde podría pisar el render de una
// elección más reciente.
let a2RequestId = 0;

// BUG evitado (mismo que ya existía en A1, ver notas de 2026-07-07): un
// ResizeObserver por panel para que el primer render mida el tamaño real
// del contenedor (no el de respaldo chico) apenas System Overview deja de
// estar oculto, sin depender de que el usuario haga click primero.
let resizeObserverA1 = null;
let lastObservedWidthA1 = 0;
let lastObservedHeightA1 = 0;

let resizeObserverA2 = null;
let lastObservedWidthA2 = 0;
let lastObservedHeightA2 = 0;

// A3 -- perfil de cuestionario del participante (ver notas extensas en
// versiones anteriores de este archivo / estado_proyecto.md). A1 y A2
// seleccionan TRIALS, el perfil es por PARTICIPANTE -- se deduplica.
function getSelectedParticipantTrialCounts() {
    const counts = new Map();

    selectedTrials.forEach((point) => {
        const label = point.Participant_label;
        counts.set(label, (counts.get(label) ?? 0) + 1);
    });

    return counts;
}

let a3RequestId = 0;

async function renderA3() {
    const trialCounts = getSelectedParticipantTrialCounts();
    const participantLabels = Array.from(trialCounts.keys());

    a3RequestId += 1;
    const requestId = a3RequestId;

    function removeParticipant(participantLabel) {
        Array.from(selectedTrials.entries()).forEach(([key, point]) => {
            if (point.Participant_label === participantLabel) {
                selectedTrials.delete(key);
            }
        });

        renderA1();
        renderA2();
        renderA3();
    }

    if (participantLabels.length === 0) {
        renderHusformerA3Panel({
            containerId: "a3-chart",
            profileData: null,
            participantTrialCounts: trialCounts,
            onRemoveParticipant: removeParticipant,
        });
        return;
    }

    const profileData = await fetchH2ParticipantProfiles(participantLabels);

    if (requestId !== a3RequestId) {
        return;
    }

    renderHusformerA3Panel({
        containerId: "a3-chart",
        profileData,
        participantTrialCounts: trialCounts,
        onRemoveParticipant: removeParticipant,
    });
}

// ============================================================
// Vista B -- B1 (heatmap modalidad x tiempo). B1 es un DRILL-DOWN de un
// solo trial a la vez, no una vista coordinada por selección múltiple como
// A1/A2/A3 -- por eso tiene su propio estado, separado de selectedTrials.
//
// Decisión confirmada con Russell (2026-07-15): el trial que se muestra en
// B1 es el ÚLTIMO CLICKEADO en A1/A2, sin importar si ese click lo agregó o
// lo quitó de selectedTrials (la selección múltiple de A1/A2/A3 sirve para
// comparar VARIOS trials en A3; B1 en cambio investiga UNO en profundidad).
// Por eso `lastClickedTrial` es independiente de selectedTrials: un click
// en el fondo (handleBackgroundClick, que limpia selectedTrials) NO lo
// resetea -- B1 sigue mostrando el último trial clickeado como contexto,
// incluso si ya no está seleccionado en A1/A2.
// ============================================================
let lastClickedTrial = null;

// Última respuesta de /trial-attention -- { participant_id, trial, split,
// num_windows, modality_labels, windows: [...] }.
let latestB1Data = null;

// Misma protección de condición de carrera que a2RequestId/a3RequestId (ver
// notas arriba): clickear varios trials rápido no debe dejar B1 mostrando
// una respuesta vieja que llegó tarde.
let b1RequestId = 0;

let resizeObserverB1 = null;
let lastObservedWidthB1 = 0;
let lastObservedHeightB1 = 0;

// Modo de vista de B1 -- "heatmap" (default) o "lines" (2026-07-17, fusión
// B1+B2 en un solo panel a pedido de Russell: eran dos idioms del MISMO
// dato ocupando dos espacios, con un selector arriba pasan a ocupar uno
// solo -- ver #husformer-b1-view-control en index.html). El panel B2
// original (frontend/js/charts/husformer_b2_chart.js) NO se eliminó -- se
// sigue usando tal cual, solo que renderizado adentro de #b1-chart cuando
// este modo está activo, en vez de tener su propio contenedor/observer.
const DEFAULT_B1_VIEW_MODE = "heatmap";
let currentB1ViewMode = DEFAULT_B1_VIEW_MODE;

function renderB1() {
    if (currentB1ViewMode === "heatmap") {
        renderHusformerB1Chart({
            containerId: "b1-chart",
            activeTrial: lastClickedTrial,
            attentionData: latestB1Data,
        });
    } else {
        renderHusformerB2Chart({
            containerId: "b1-chart",
            activeTrial: lastClickedTrial,
            attentionData: latestB1Data,
        });
    }

    renderB1Context();
}

/**
 * Actualiza el label de trial activo (compartido por ambos modos) y
 * alterna cuál de las dos leyendas se ve -- la de color dinámico (heatmap)
 * o la categórica fija (líneas), nunca las dos a la vez.
 */
function renderB1Context() {
    const label = document.getElementById("husformer-b1-trial-label");
    const heatmapLegend = document.getElementById("husformer-b1-legend");
    const linesLegend = document.getElementById("husformer-b2-legend");

    heatmapLegend.classList.toggle("husformer-b1-legend-hidden", currentB1ViewMode !== "heatmap");
    linesLegend.classList.toggle("husformer-b1-legend-hidden", currentB1ViewMode !== "lines");

    if (!lastClickedTrial) {
        label.textContent = "";
        heatmapLegend.innerHTML = "";
        return;
    }

    label.textContent = `${lastClickedTrial.Participant_label} · Trial ${lastClickedTrial.Trial}`;

    if (currentB1ViewMode !== "heatmap") {
        return;
    }

    if (!latestB1Data || !latestB1Data.windows || latestB1Data.windows.length === 0) {
        heatmapLegend.innerHTML = "";
        return;
    }

    // Los 5 valores de una ventana son PORCENTAJE de dominancia (0-100,
    // suman 100 dentro de la ventana) -- ver husformer_attention_service.py.
    const modalityKeys = Object.keys(latestB1Data.modality_labels);
    const allValues = latestB1Data.windows.flatMap((w) => modalityKeys.map((key) => w[key]));
    const minValue = Math.min(...allValues);
    const maxValue = Math.max(...allValues);

    heatmapLegend.innerHTML = `
        <span class="husformer-b1-legend-label">% Dominancia</span>
        <div class="husformer-b1-legend-bar"></div>
        <div class="husformer-b1-legend-ticks">
            <span>${minValue.toFixed(1)}%</span>
            <span>${maxValue.toFixed(1)}%</span>
        </div>
    `;
}

/**
 * Pide al backend la serie temporal de dominancia de modalidad del trial
 * dado (husformer_attention_service.py, calculado al vuelo -- mismo patrón
 * que loadAndRenderClusters de A2) y renderiza B1 (en el modo activo).
 */
async function loadAndRenderB1(trialPoint) {
    lastClickedTrial = trialPoint;

    b1RequestId += 1;
    const requestId = b1RequestId;

    // Render inmediato en estado "Cargando..." -- el fetch puede tardar
    // unos milisegundos, sin esto B1 se quedaría mostrando el trial
    // ANTERIOR mientras carga el nuevo, lo cual es confuso.
    latestB1Data = null;
    renderB1();

    const data = await fetchHusformerTrialAttention({
        participantId: trialPoint.Participant_id,
        trial: trialPoint.Trial,
    });

    if (requestId !== b1RequestId) {
        return;
    }

    latestB1Data = data;
    renderB1();
}

/**
 * Botones "Heatmap"/"Líneas" -- mismo patrón que setupProjectionControls de
 * A1/A2 (botones excluyentes, no checkboxes).
 */
function setupB1ViewToggle() {
    const buttons = document.querySelectorAll(
        "#husformer-b1-view-control .husformer-a1-projection-option"
    );

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            const viewMode = button.dataset.viewMode;

            if (viewMode === currentB1ViewMode) {
                return;
            }

            currentB1ViewMode = viewMode;

            buttons.forEach((otherButton) => {
                otherButton.classList.toggle("active", otherButton === button);
            });

            renderB1();
        });
    });
}

function observeB1Container() {
    const container = document.getElementById("b1-chart");

    if (!container || resizeObserverB1) {
        return;
    }

    resizeObserverB1 = new ResizeObserver((entries) => {
        const { width, height } = entries[0].contentRect;

        if (width === lastObservedWidthB1 && height === lastObservedHeightB1) {
            return;
        }

        lastObservedWidthB1 = width;
        lastObservedHeightB1 = height;

        if (width > 0 && height > 0) {
            renderB1();
        }
    });

    resizeObserverB1.observe(container);
}

// ============================================================
// B3 -- señal cruda (un canal, seleccionable) + atención (B2 reutilizado
// sin modificar) apilados, ver husformer_b3_chart.js para la justificación
// completa (juxtapose, no dual-axis).
// ============================================================
const DEFAULT_B3_CHANNEL = "Fz";
let currentB3Channel = DEFAULT_B3_CHANNEL;

// Respuesta cruda de /api/trial-signals para el canal activo -- distinta
// de latestB1Data (que es la atención, ya cargada aparte).
let latestB3SignalData = null;
let b3RequestId = 0;

let resizeObserverB3Signal = null;
let lastObservedWidthB3Signal = 0;
let lastObservedHeightB3Signal = 0;

let resizeObserverB3Attention = null;
let lastObservedWidthB3Attention = 0;
let lastObservedHeightB3Attention = 0;

function renderB3() {
    const label = document.getElementById("husformer-b3-trial-label");
    label.textContent = lastClickedTrial
        ? `${lastClickedTrial.Participant_label} · Trial ${lastClickedTrial.Trial}`
        : "";

    renderHusformerB3SignalChart({
        containerId: "b3-signal-chart",
        activeTrial: lastClickedTrial,
        signalData: latestB3SignalData,
        channelName: currentB3Channel,
    });

    // Panel de atención -- MISMO renderer que el modo Líneas de B1/B2, sin
    // tocarlo, reutilizando latestB1Data (ya cargado por loadAndRenderB1,
    // mismo trial). No hace falta pedirle nada nuevo al backend para esto.
    renderHusformerB2Chart({
        containerId: "b3-attention-chart",
        activeTrial: lastClickedTrial,
        attentionData: latestB1Data,
    });
}

/**
 * Pide la señal cruda del canal activo para el trial dado -- fetch
 * INDEPENDIENTE del de atención (latestB1Data), porque es un endpoint y un
 * dato distintos (/api/trial-signals, no /api/husformer/trial-attention).
 */
async function loadAndRenderB3(trialPoint) {
    b3RequestId += 1;
    const requestId = b3RequestId;

    latestB3SignalData = null;
    renderB3();

    const data = await fetchTrialSignals({
        participant: trialPoint.Participant_id,
        trial: trialPoint.Trial,
        channels: [currentB3Channel],
    });

    if (requestId !== b3RequestId) {
        return;
    }

    latestB3SignalData = data;
    renderB3();
}

function setupB3ChannelControl() {
    const select = document.getElementById("husformer-b3-channel-select");

    select.addEventListener("change", () => {
        currentB3Channel = select.value;

        if (lastClickedTrial) {
            loadAndRenderB3(lastClickedTrial);
        }
    });
}

function observeB3SignalContainer() {
    const container = document.getElementById("b3-signal-chart");

    if (!container || resizeObserverB3Signal) {
        return;
    }

    resizeObserverB3Signal = new ResizeObserver((entries) => {
        const { width, height } = entries[0].contentRect;

        if (width === lastObservedWidthB3Signal && height === lastObservedHeightB3Signal) {
            return;
        }

        lastObservedWidthB3Signal = width;
        lastObservedHeightB3Signal = height;

        if (width > 0 && height > 0) {
            renderB3();
        }
    });

    resizeObserverB3Signal.observe(container);
}

function observeB3AttentionContainer() {
    const container = document.getElementById("b3-attention-chart");

    if (!container || resizeObserverB3Attention) {
        return;
    }

    resizeObserverB3Attention = new ResizeObserver((entries) => {
        const { width, height } = entries[0].contentRect;

        if (width === lastObservedWidthB3Attention && height === lastObservedHeightB3Attention) {
            return;
        }

        lastObservedWidthB3Attention = width;
        lastObservedHeightB3Attention = height;

        if (width > 0 && height > 0) {
            renderB3();
        }
    });

    resizeObserverB3Attention.observe(container);
}

// Handlers de selección/fondo COMPARTIDOS entre A1 y A2 -- clickear un punto
// (o el fondo) en cualquiera de los dos paneles re-renderiza los TRES
// paneles de Vista A (compound brushing/linked highlighting entre vistas
// coordinadas, Cap. 12 de Munzner / Cap. 5 de Aigner).
function handlePointToggle(point) {
    const key = getTrialKey(point);

    if (selectedTrials.has(key)) {
        selectedTrials.delete(key);
    } else {
        selectedTrials.set(key, point);
    }

    renderA1();
    renderA2();
    renderA3();

    // Drill-down a Vista B -- ver nota extensa arriba de lastClickedTrial.
    // Se dispara SIEMPRE que se clickea un punto (agregar o quitar de la
    // selección), independientemente del resultado en selectedTrials.
    loadAndRenderB1(point);

    // lastClickedTrial recién queda actualizado DESPUÉS de loadAndRenderB1
    // (es quien lo asigna) -- por eso B3 se dispara con `point` directo, no
    // con la variable, para no depender del orden de ejecución async.
    loadAndRenderB3(point);
}

function handleBackgroundClick() {
    if (selectedTrials.size === 0) {
        return;
    }

    selectedTrials.clear();
    renderA1();
    renderA2();
    renderA3();
}

function renderA1() {
    if (!latestPoints) {
        return;
    }

    renderHusformerA1Chart({
        containerId: "a1-chart",
        points: latestPoints,
        projectionMethod: currentProjectionMethod,
        selectedTrials,
        onPointClick: handlePointToggle,
        onBackgroundClick: handleBackgroundClick,
        initialZoomTransform: currentZoomTransform,
        onZoomChange: (transform) => {
            currentZoomTransform = transform;
        },
        participantFilter,
        trialFilter,
    });
}

/**
 * Fusiona latestPoints (posición 2D + VAD, de A1) con latestClusterData
 * (etiqueta de cluster, de /trial-clusters) por clave de trial, y renderiza
 * A2. Si falta cualquiera de los dos insumos todavía (primer render, antes
 * de que ambos fetches terminen), no hace nada -- se vuelve a llamar en
 * cuanto el segundo insumo llega.
 */
function renderA2() {
    if (!latestPoints || !latestClusterData) {
        return;
    }

    const clusterByTrialKey = new Map(
        latestClusterData.points.map((point) => [getTrialKey(point), point.cluster])
    );

    const mergedPoints = latestPoints
        .filter((point) => clusterByTrialKey.has(getTrialKey(point)))
        .map((point) => ({
            ...point,
            cluster: clusterByTrialKey.get(getTrialKey(point)),
        }));

    renderHusformerA2Chart({
        containerId: "a2-chart",
        points: mergedPoints,
        selectedTrials,
        selectedClusterId: currentSelectedClusterId,
        onPointClick: handlePointToggle,
        onBackgroundClick: handleBackgroundClick,
        initialZoomTransform: currentA2ZoomTransform,
        onZoomChange: (transform) => {
            currentA2ZoomTransform = transform;
        },
    });

    renderA2Legend();
}

/**
 * Reconstruye el desplegable "Resaltar:" de A2 según num_clusters/has_noise
 * de la última respuesta de clustering, y la leyenda de color debajo del
 * chart (ambas dependen del preset activo, a diferencia de la leyenda fija
 * de Valencia en A1).
 */
function populateClusterSelect() {
    const select = document.getElementById("husformer-a2-cluster-select");
    select.innerHTML = '<option value="">Todos</option>';

    if (!latestClusterData) {
        return;
    }

    for (let clusterId = 0; clusterId < latestClusterData.num_clusters; clusterId += 1) {
        const option = document.createElement("option");
        option.value = String(clusterId);
        option.textContent = `Cluster ${clusterId}`;
        select.appendChild(option);
    }

    if (latestClusterData.has_noise) {
        const noiseOption = document.createElement("option");
        noiseOption.value = "-1";
        noiseOption.textContent = "Ruido (-1)";
        select.appendChild(noiseOption);
    }
}

function renderA2Legend() {
    const legend = document.getElementById("husformer-a2-legend");
    legend.innerHTML = "";

    if (!latestClusterData) {
        return;
    }

    for (let clusterId = 0; clusterId < latestClusterData.num_clusters; clusterId += 1) {
        const item = document.createElement("div");
        item.className = "husformer-a2-legend-item";

        const swatch = document.createElement("span");
        swatch.className = "husformer-a2-legend-swatch";
        swatch.style.background = getClusterColor(clusterId);

        const label = document.createElement("span");
        label.textContent = String(clusterId);

        item.appendChild(swatch);
        item.appendChild(label);
        legend.appendChild(item);
    }

    if (latestClusterData.has_noise) {
        const item = document.createElement("div");
        item.className = "husformer-a2-legend-item";

        const swatch = document.createElement("span");
        swatch.className = "husformer-a2-legend-swatch";
        swatch.style.background = NOISE_CLUSTER_COLOR;

        const label = document.createElement("span");
        label.textContent = "ruido";

        item.appendChild(swatch);
        item.appendChild(label);
        legend.appendChild(item);
    }
}

async function loadAndRenderProjection(method = currentProjectionMethod) {
    const data = await fetchHusformerTrialProjection({
        method,
    });

    latestPoints = data.points;
    currentProjectionMethod = method;

    renderA1();
    renderA2();
}

/**
 * Pide el clustering al vuelo al backend (KMeans o HDBSCAN, ver
 * husformer_trial_service.py) y renderiza A2 con el resultado. NO se
 * precomputa ni se cachea en disco -- cada cambio de método/preset dispara
 * un request nuevo (decisión confirmada con Russell, 2026-07-15: KMeans/
 * HDBSCAN sobre 1280x40 floats es prácticamente instantáneo).
 */
async function loadAndRenderClusters(method = currentClusterMethod, paramValue = currentClusterParam) {
    a2RequestId += 1;
    const requestId = a2RequestId;

    const data = await fetchHusformerTrialClusters({
        method,
        paramValue,
    });

    if (requestId !== a2RequestId) {
        return;
    }

    latestClusterData = data;
    currentClusterMethod = method;
    currentClusterParam = paramValue;

    populateClusterSelect();
    renderA2();
}

/**
 * Sincroniza los botones de proyección de AMBOS paneles (A1 y A2) con el
 * estado compartido `currentProjectionMethod` -- llamada tanto al cambiar
 * desde A1 como desde A2, para que el panel que NO originó el cambio
 * también actualice qué botón se ve activo.
 */
function updateProjectionButtonsUI(method) {
    document
        .querySelectorAll(
            "#husformer-a1-projection-control .husformer-a1-projection-option, "
            + "#husformer-a2-projection-control .husformer-a1-projection-option"
        )
        .forEach((button) => {
            button.classList.toggle("active", button.dataset.method === method);
        });
}

function handleProjectionChange(method) {
    if (method === currentProjectionMethod) {
        return;
    }

    updateProjectionButtonsUI(method);

    // Al cambiar de proyección, el zoom en píxeles de AMBOS paneles ya no
    // tiene sentido (las coordenadas x/y son otras) -- se resetean acá. La
    // selección SÍ se mantiene (mismos trials, solo cambia dónde caen en el
    // plano 2D). El cluster resaltado en A2 tampoco se resetea: la etiqueta
    // de cluster de cada trial es estable sin importar la proyección (se
    // calcula sobre el vector de 40-dim, no sobre x/y -- ver
    // husformer_trial_service.py).
    currentZoomTransform = null;
    currentA2ZoomTransform = null;

    loadAndRenderProjection(method);
}

function setupProjectionControls() {
    document
        .querySelectorAll(
            "#husformer-a1-projection-control .husformer-a1-projection-option, "
            + "#husformer-a2-projection-control .husformer-a1-projection-option"
        )
        .forEach((button) => {
            button.addEventListener("click", () => {
                handleProjectionChange(button.dataset.method);
            });
        });
}

function setupFilterControls() {
    const participantSelect = document.getElementById(
        "husformer-a1-participant-filter"
    );
    const trialSelect = document.getElementById(
        "husformer-a1-trial-filter"
    );

    participantSelect.addEventListener("change", () => {
        participantFilter = participantSelect.value;
        renderA1();
    });

    trialSelect.addEventListener("change", () => {
        trialFilter = trialSelect.value;
        renderA1();
    });
}

/**
 * Controles de A2: selector de método (KMeans/HDBSCAN), las dos filas de
 * presets (solo una visible a la vez, según el método activo), y el
 * desplegable de resaltado de cluster.
 */
function setupA2Controls() {
    const methodButtons = document.querySelectorAll(
        "#husformer-a2-cluster-control .husformer-a2-method-option"
    );
    const kmeansPresetRow = document.getElementById("husformer-a2-preset-row-kmeans");
    const hdbscanPresetRow = document.getElementById("husformer-a2-preset-row-hdbscan");
    const clusterSelect = document.getElementById("husformer-a2-cluster-select");

    function activePresetRow() {
        return currentClusterMethod === "kmeans" ? kmeansPresetRow : hdbscanPresetRow;
    }

    function setActivePresetButton(row, paramValue) {
        row.querySelectorAll(".husformer-a2-preset-option").forEach((button) => {
            button.classList.toggle(
                "active",
                Number(button.dataset.paramValue) === paramValue
            );
        });
    }

    methodButtons.forEach((button) => {
        button.addEventListener("click", () => {
            const method = button.dataset.method;

            if (method === currentClusterMethod) {
                return;
            }

            methodButtons.forEach((otherButton) => {
                otherButton.classList.toggle("active", otherButton === button);
            });

            kmeansPresetRow.classList.toggle("husformer-a2-preset-row-hidden", method !== "kmeans");
            hdbscanPresetRow.classList.toggle("husformer-a2-preset-row-hidden", method !== "hdbscan");

            const defaultParam = method === "kmeans"
                ? KMEANS_DEFAULT_K
                : HDBSCAN_DEFAULT_MIN_CLUSTER_SIZE;

            setActivePresetButton(method === "kmeans" ? kmeansPresetRow : hdbscanPresetRow, defaultParam);

            currentSelectedClusterId = null;
            clusterSelect.value = "";

            loadAndRenderClusters(method, defaultParam);
        });
    });

    [kmeansPresetRow, hdbscanPresetRow].forEach((row) => {
        row.querySelectorAll(".husformer-a2-preset-option").forEach((button) => {
            button.addEventListener("click", () => {
                const paramValue = Number(button.dataset.paramValue);

                if (paramValue === currentClusterParam && row === activePresetRow()) {
                    return;
                }

                setActivePresetButton(row, paramValue);

                currentSelectedClusterId = null;
                clusterSelect.value = "";

                loadAndRenderClusters(currentClusterMethod, paramValue);
            });
        });
    });

    clusterSelect.addEventListener("change", () => {
        currentSelectedClusterId = clusterSelect.value === "" ? null : Number(clusterSelect.value);
        renderA2();
    });
}

function observeA1Container() {
    const container = document.getElementById("a1-chart");

    if (!container || resizeObserverA1) {
        return;
    }

    resizeObserverA1 = new ResizeObserver((entries) => {
        const { width, height } = entries[0].contentRect;

        if (width === lastObservedWidthA1 && height === lastObservedHeightA1) {
            return;
        }

        lastObservedWidthA1 = width;
        lastObservedHeightA1 = height;

        if (width > 0 && height > 0) {
            renderA1();
        }
    });

    resizeObserverA1.observe(container);
}

function observeA2Container() {
    const container = document.getElementById("a2-chart");

    if (!container || resizeObserverA2) {
        return;
    }

    resizeObserverA2 = new ResizeObserver((entries) => {
        const { width, height } = entries[0].contentRect;

        if (width === lastObservedWidthA2 && height === lastObservedHeightA2) {
            return;
        }

        lastObservedWidthA2 = width;
        lastObservedHeightA2 = height;

        if (width > 0 && height > 0) {
            renderA2();
        }
    });

    resizeObserverA2.observe(container);
}

export function initializeHusformerView() {
    setupProjectionControls();
    setupFilterControls();
    setupA2Controls();
    setupB1ViewToggle();
    setupB3ChannelControl();
    observeA1Container();
    observeA2Container();
    observeB1Container();
    observeB3SignalContainer();
    observeB3AttentionContainer();

    // A1/A2 dependen de fetches asíncronos independientes (proyección y
    // clustering respectivamente) -- se piden en paralelo; cada uno
    // renderiza lo que puede en cuanto llega, y renderA2() se completa solo
    // cuando AMBOS ya están disponibles (ver guard al inicio de renderA2).
    loadAndRenderProjection();
    loadAndRenderClusters();

    // A3 no depende de ningún fetch (solo de selectedTrials, que arranca
    // vacío) -- se puede renderizar de una vez.
    renderA3();

    // B1 arranca sin trial activo (nadie ha clickeado nada todavía) -- solo
    // muestra el estado vacío ("Selecciona un trial en Vista A"), sin
    // fetch, hasta el primer click en A1/A2 (ver loadAndRenderB1).
    renderB1();

    // B3 igual -- estado vacío hasta el primer click (ver loadAndRenderB3).
    renderB3();
}
