import {
    fetchHusformerTrialProjection,
    fetchHusformerTrialClusters,
    fetchHusformerTrialAttention,
    fetchHusformerWindowCrossAttention,
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
    renderHusformerB3Chart,
    buildB3Series,
} from "./charts/husformer_b3_chart.js";

import {
    renderHusformerC1Chart,
} from "./charts/husformer_c1_chart.js";

import {
    EEG_REGION_GROUPS,
    EEG_HEMISPHERE_GROUPS,
    EOG_GROUPS,
    EMG_GROUPS,
    GSR_GROUPS,
    AUTONOMIC_GROUPS,
    findB3Group,
    MAX_SIMULTANEOUS_SIGNALS,
    DEFAULT_B3_GROUP_IDS,
    getSignalColor,
} from "./husformer_b3_channel_groups.js";

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

// Handles devueltos por renderHusformerB1Chart/B2Chart/B3Chart (2026-07-17,
// sincronización bidireccional B1/B2 <-> B3, a pedido de Russell) -- cada
// chart expone { highlightWindow(windowIndex), clearHighlight() } para que
// OTRO panel pueda resaltar una ventana en él sin reconstruir su SVG
// entero. Se reasignan en cada render (el chart viejo ya no existe en el
// DOM), y pueden ser null si el panel está en estado vacío/cargando (esos
// casos retornan null en vez de un handle) -- por eso todo acceso usa `?.`.
let activeB1B2Handle = null;
let activeB3Handle = null;

function renderB1() {
    // El hover ahora TAMBIÉN maneja C1 (2026-07-22, a pedido de Russell):
    // las matrices cross-modal varían poco entre ventanas consecutivas, y
    // click obligaba a un click por ventana para comparar -- demasiado
    // lento para "barrer" varias ventanas seguidas y notar la diferencia.
    // Con hover, mover el mouse por B1/B2 actualiza C1 en tiempo real, sin
    // clicks. handleWindowSelect ya tiene el guard de "no hacer nada si es
    // la misma ventana o si es null" (ver esa función) -- null pasa cuando
    // el mouse SALE del panel, y ahí C1 se queda mostrando la última
    // ventana (sticky), no vuelve a estado vacío -- si volviera a vacío
    // cada vez que el mouse sale de B1/B2, sería imposible siquiera mirar
    // C1 con calma sin que desaparezca.
    const onHoverWindowChange = (windowIndex) => {
        if (windowIndex === null) {
            activeB3Handle?.clearHighlight();
        } else {
            activeB3Handle?.highlightWindow(windowIndex);
        }

        handleWindowSelect(windowIndex);
    };

    if (currentB1ViewMode === "heatmap") {
        activeB1B2Handle = renderHusformerB1Chart({
            containerId: "b1-chart",
            activeTrial: lastClickedTrial,
            attentionData: latestB1Data,
            onHoverWindowChange,
            onWindowSelect: handleWindowSelect,
            selectedWindowIndex,
        });
    } else {
        activeB1B2Handle = renderHusformerB2Chart({
            containerId: "b1-chart",
            activeTrial: lastClickedTrial,
            attentionData: latestB1Data,
            onHoverWindowChange,
            onWindowSelect: handleWindowSelect,
            selectedWindowIndex,
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

    // La ventana seleccionada (si había una) pertenece al trial ANTERIOR --
    // un window_index de otro trial no tiene ningún significado acá, así
    // que se limpia junto con el cambio de trial (mismo momento en que B1/B2
    // se recargan). C1 vuelve a su estado vacío hasta el próximo click.
    selectedWindowIndex = null;
    latestC1Data = null;
    renderC1();

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
// Vista C -- C1 (matriz 5x5 de atención cross-modal de UNA ventana puntual).
// Drill-down de B1/B2: a diferencia de A->B (que se dispara por CLICK en un
// punto, pero sin necesidad de recordar cuál -- B1 solo necesita "el último
// trial"), B->C necesita saber EXACTAMENTE qué ventana, y esa selección debe
// sobrevivir a que el usuario siga haciendo hover en B1/B2/B3 -- por eso es
// un estado nuevo (selectedWindowIndex), separado de lastClickedTrial y del
// mecanismo de hover ya existente. Decisión de diseño confirmada con Russell
// (2026-07-22): selección por CLICK simple de una ventana (no brushing de un
// rango, que es lo que decía el paper hasta ahora -- Sección 5 actualizada
// para reflejar esto).
// ============================================================
let selectedWindowIndex = null;

// Última respuesta de /window-cross-attention -- { participant_id, trial,
// window_index, window_start_sec, split, modality_labels, matrix: 5x5 }.
let latestC1Data = null;
let c1RequestId = 0;

let resizeObserverC1 = null;
let lastObservedWidthC1 = 0;
let lastObservedHeightC1 = 0;

function renderC1() {
    const label = document.getElementById("husformer-c1-context-label");

    if (!lastClickedTrial || selectedWindowIndex === null) {
        label.textContent = "";
    } else if (latestC1Data) {
        label.textContent = (
            `${lastClickedTrial.Participant_label} · Trial ${lastClickedTrial.Trial} `
            + `· ${latestC1Data.window_start_sec.toFixed(1)}s`
        );
    } else {
        label.textContent = `${lastClickedTrial.Participant_label} · Trial ${lastClickedTrial.Trial}`;
    }

    renderHusformerC1Chart({
        containerId: "c1-chart",
        activeTrial: lastClickedTrial,
        selectedWindowIndex,
        crossAttentionData: latestC1Data,
    });
}

/**
 * Pide al backend la matriz cross-modal de la ventana seleccionada y
 * renderiza C1 -- mismo patrón que loadAndRenderB1 (fetch al vuelo, guard de
 * condición de carrera con requestId, estado "Cargando..." inmediato).
 */
async function loadAndRenderC1() {
    c1RequestId += 1;
    const requestId = c1RequestId;

    latestC1Data = null;
    renderC1();

    const data = await fetchHusformerWindowCrossAttention({
        participantId: lastClickedTrial.Participant_id,
        trial: lastClickedTrial.Trial,
        windowIndex: selectedWindowIndex,
    });

    if (requestId !== c1RequestId) {
        return;
    }

    latestC1Data = data;
    renderC1();
}

/**
 * Ventana activa para C1 -- disparada por HOVER en B1/B2 (principal, desde
 * 2026-07-22) y también por click (se deja funcionando igual, no molesta,
 * útil en touch donde no hay hover real). Dos guards importantes:
 *
 * 1. `windowIndex === null` (el mouse salió de B1/B2, evento de mouseout) --
 *    no hace nada. C1 se queda mostrando la última ventana marcada (sticky),
 *    a propósito: si limpiara la selección cada vez que el mouse sale del
 *    panel, sería imposible mover el mouse hacia C1 para mirarlo de cerca
 *    sin que se vaciara antes de llegar.
 * 2. `windowIndex === selectedWindowIndex` (ya es la ventana mostrada) --
 *    evita un fetch de red redundante. Importante sobre todo para B2, cuyo
 *    hover dispara en cada `mousemove` (muchos eventos por segundo mientras
 *    el mouse se mueve dentro de la MISMA ventana) -- sin este guard,
 *    hacer hover lento dentro de una sola ventana dispararía decenas de
 *    requests idénticos.
 */
function handleWindowSelect(windowIndex) {
    if (windowIndex === null || windowIndex === selectedWindowIndex) {
        return;
    }

    selectedWindowIndex = windowIndex;
    activeB1B2Handle?.updateSelection(windowIndex);
    loadAndRenderC1();
}

function observeC1Container() {
    const container = document.getElementById("c1-chart");

    if (!container || resizeObserverC1) {
        return;
    }

    resizeObserverC1 = new ResizeObserver((entries) => {
        const { width, height } = entries[0].contentRect;

        if (width === lastObservedWidthC1 && height === lastObservedHeightC1) {
            return;
        }

        lastObservedWidthC1 = width;
        lastObservedHeightC1 = height;

        if (width > 0 && height > 0) {
            renderC1();
        }
    });

    resizeObserverC1.observe(container);
}

// ============================================================
// B3 -- comparación de señales crudas normalizadas (rediseño 2026-07-17,
// ver husformer_b3_chart.js / husformer_b3_channel_groups.js). Selección
// MÚLTIPLE de grupos (no un canal suelto), hasta MAX_SIMULTANEOUS_SIGNALS
// a la vez. Ya NO muestra atención acá -- B1/B2 está siempre visible al
// lado, mostrarla de nuevo era redundante (ver corrección en el .md).
// ============================================================

// IDs de los grupos actualmente seleccionados, en orden de selección
// (Set preserva orden de inserción en JS) -- el orden importa para que el
// color de cada señal sea estable mientras no cambie la selección.
// Arranca con DEFAULT_B3_GROUP_IDS (2026-07-17, a pedido de Russell: una
// señal de cada una de las 6 familias, para que la primera impresión del
// panel ya muestre una comparación representativa entre modalidades).
let selectedB3GroupIds = new Set(DEFAULT_B3_GROUP_IDS);

// Respuesta cruda de /api/trial-signals -- incluye TODOS los canales que
// hacen falta para promediar los grupos actualmente seleccionados (un solo
// fetch combinado, no uno por grupo).
let latestB3RawResponse = null;
let b3RequestId = 0;

let resizeObserverB3 = null;
let lastObservedWidthB3 = 0;
let lastObservedHeightB3 = 0;

// Transform de zoom de B3 -- SOLO zoom/pan en X (ver husformer_b3_
// chart.js). Se persiste acá para sobrevivir a re-renders (resize, cambio
// de selección de señales), mismo patrón que currentZoomTransform de A1 y
// el de B1. null = sin zoom (vista completa 0-60s).
let currentB3ZoomTransform = null;

/**
 * Arma la lista de series (una por grupo seleccionado, promediada y
 * normalizada) a partir de la respuesta cruda ya cargada, y renderiza B3.
 * Separado de loadAndRenderB3 porque cambiar CUÁLES colores usa cada
 * chip activo (getSignalColor) no necesita un fetch nuevo -- solo
 * reconstruir las series con el mismo dato ya en memoria.
 */
function renderB3() {
    const label = document.getElementById("husformer-b3-trial-label");
    label.textContent = lastClickedTrial
        ? `${lastClickedTrial.Participant_label} · Trial ${lastClickedTrial.Trial}`
        : "";

    const selectedGroups = getSelectedB3GroupsWithColor();

    // Tres estados posibles cuando hay trial activo: sin grupos elegidos
    // ([] -- "elegí algo"), esperando el fetch (null -- "cargando"), o ya
    // con datos (array de series). Si no hay trial activo, el valor no
    // importa -- renderHusformerB3Chart revisa activeTrial primero.
    let seriesList = null;

    if (lastClickedTrial && selectedGroups.length === 0) {
        seriesList = [];
    } else if (lastClickedTrial && latestB3RawResponse) {
        seriesList = buildB3Series(latestB3RawResponse, selectedGroups);
    }

    activeB3Handle = renderHusformerB3Chart({
        containerId: "b3-chart",
        activeTrial: lastClickedTrial,
        seriesList,
        initialZoomTransform: currentB3ZoomTransform,
        onZoomChange: (transform) => {
            currentB3ZoomTransform = transform;
        },
        onHoverWindowChange: (windowIndex) => {
            if (windowIndex === null) {
                activeB1B2Handle?.clearHighlight();
            } else {
                activeB1B2Handle?.highlightWindow(windowIndex);
            }
        },
    });

    renderB3SelectorUI();
}

/**
 * Resuelve los grupos seleccionados (definición completa + color final),
 * asignando el color según su posición ENTRE los grupos de la misma
 * modalidad ya seleccionados -- ver getSignalColor en husformer_b3_
 * channel_groups.js.
 */
function getSelectedB3GroupsWithColor() {
    const countByModality = new Map();

    return Array.from(selectedB3GroupIds)
        .map((groupId) => findB3Group(groupId))
        .filter((group) => group !== undefined)
        .map((group) => {
            const indexWithinModality = countByModality.get(group.modalityKey) ?? 0;
            countByModality.set(group.modalityKey, indexWithinModality + 1);

            return {
                ...group,
                color: getSignalColor(group.modalityKey, indexWithinModality),
            };
        });
}

/**
 * Pide al backend TODOS los canales que hacen falta para los grupos
 * actualmente seleccionados, en un solo request (la unión de sus listas de
 * canales) -- evita un fetch por grupo cuando hay varios seleccionados.
 */
async function loadAndRenderB3(trialPoint) {
    lastClickedTrial = trialPoint;

    b3RequestId += 1;
    const requestId = b3RequestId;

    latestB3RawResponse = null;
    renderB3();

    const selectedGroups = getSelectedB3GroupsWithColor();

    if (selectedGroups.length === 0) {
        return;
    }

    const allChannels = Array.from(new Set(
        selectedGroups.flatMap((group) => group.channels)
    ));

    const data = await fetchTrialSignals({
        participant: trialPoint.Participant_id,
        trial: trialPoint.Trial,
        channels: allChannels,
    });

    if (requestId !== b3RequestId) {
        return;
    }

    latestB3RawResponse = data;
    renderB3();
}

/**
 * Alterna un grupo dentro/fuera de la selección -- respeta el tope
 * MAX_SIMULTANEOUS_SIGNALS (Munzner Cap. 10, límite práctico de bins
 * categóricos discriminables + Cap. 12.5.2, Javed et al. 2010). Si ya no
 * hay ningún trial clickeado todavía, solo actualiza la selección (sin
 * fetch) -- el fetch se dispara recién cuando haya un trial activo.
 */
function toggleB3Group(groupId) {
    if (selectedB3GroupIds.has(groupId)) {
        selectedB3GroupIds.delete(groupId);
    } else {
        if (selectedB3GroupIds.size >= MAX_SIMULTANEOUS_SIGNALS) {
            return;
        }
        selectedB3GroupIds.add(groupId);
    }

    if (lastClickedTrial) {
        loadAndRenderB3(lastClickedTrial);
    } else {
        renderB3SelectorUI();
    }
}

/**
 * Construye el selector de chips agrupados por modalidad -- EEG con dos
 * esquemas (Región / Hemisferio), el resto de las modalidades con sus
 * canales individuales (pocos, no hace falta agruparlos más). Se
 * reconstruye en cada render de B3 (barato, son ~20 botones) para que el
 * estado activo/deshabilitado siempre refleje selectedB3GroupIds.
 */
function renderB3SelectorUI() {
    const container = document.getElementById("husformer-b3-selector");
    container.innerHTML = "";

    const atCap = selectedB3GroupIds.size >= MAX_SIMULTANEOUS_SIGNALS;

    // Mismo color que va a usar el chart -- reutiliza getSelectedB3Groups
    // WithColor en vez de recalcular el índice por modalidad acá también
    // (única fuente de verdad para "qué color le toca a cada grupo activo").
    const colorByGroupId = new Map(
        getSelectedB3GroupsWithColor().map((group) => [group.id, group.color])
    );

    // Punto de color por grupo (2026-07-17, a pedido de Russell -- "que se
    // note la diferencia"): color BASE de la modalidad (índice 0, sin
    // importar si hay algo seleccionado todavía), mismo share encoding que
    // ya usan los chips activos y las líneas de B1/B2.
    function buildRow(label, groups, modalityKey) {
        const row = document.createElement("div");
        row.className = "husformer-b3-selector-row";

        const rowLabel = document.createElement("span");
        rowLabel.className = "husformer-b3-selector-group-label";

        const dot = document.createElement("span");
        dot.className = "husformer-b3-selector-group-dot";
        dot.style.background = getSignalColor(modalityKey, 0);
        rowLabel.appendChild(dot);

        rowLabel.appendChild(document.createTextNode(label));
        row.appendChild(rowLabel);

        groups.forEach((group) => {
            const isActive = selectedB3GroupIds.has(group.id);

            const button = document.createElement("button");
            button.type = "button";
            button.className = `husformer-b3-chip${isActive ? " active" : ""}`;
            button.textContent = group.label;
            button.disabled = !isActive && atCap;

            if (isActive) {
                button.style.setProperty("--chip-color", colorByGroupId.get(group.id));
            }

            button.addEventListener("click", () => toggleB3Group(group.id));
            row.appendChild(button);
        });

        container.appendChild(row);
    }

    buildRow("EEG · Región:", EEG_REGION_GROUPS, "modality_1");
    buildRow("EEG · Hemisferio:", EEG_HEMISPHERE_GROUPS, "modality_1h");
    buildRow("EOG:", EOG_GROUPS, "modality_2");
    buildRow("EMG:", EMG_GROUPS, "modality_3");
    buildRow("GSR:", GSR_GROUPS, "modality_4");
    buildRow("Resp+Plet+Temp:", AUTONOMIC_GROUPS, "modality_5");
}

/**
 * Vuelve la vista de B3 al trial completo (0-60s) -- 2026-07-17, a pedido
 * de Russell. Aclarado explícitamente con él: esto SOLO resetea el zoom,
 * no la selección de señales (son dos estados independientes) -- ver
 * husformer_b3_resumen_implementacion.md. El doble-click sobre el chart
 * hace lo mismo (implementado directo en husformer_b3_chart.js), este
 * botón es el mecanismo DESCUBRIBLE -- un doble-click no tiene ninguna
 * pista visual de que existe, a diferencia de un botón.
 */
function resetB3Zoom() {
    currentB3ZoomTransform = null;
    renderB3();
}

function setupB3ChannelControl() {
    renderB3SelectorUI();

    const resetButton = document.getElementById("husformer-b3-reset-zoom");
    resetButton.addEventListener("click", resetB3Zoom);
}

function observeB3Container() {
    const container = document.getElementById("b3-chart");

    if (!container || resizeObserverB3) {
        return;
    }

    resizeObserverB3 = new ResizeObserver((entries) => {
        const { width, height } = entries[0].contentRect;

        if (width === lastObservedWidthB3 && height === lastObservedHeightB3) {
            return;
        }

        lastObservedWidthB3 = width;
        lastObservedHeightB3 = height;

        if (width > 0 && height > 0) {
            renderB3();
        }
    });

    resizeObserverB3.observe(container);
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
    observeC1Container();
    observeB3Container();

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

    // C1 arranca sin ventana seleccionada -- estado vacío hasta el primer
    // click en B1/B2 (ver handleWindowSelect).
    renderC1();

    // B3 igual -- estado vacío hasta el primer click (ver loadAndRenderB3).
    renderB3();
}
