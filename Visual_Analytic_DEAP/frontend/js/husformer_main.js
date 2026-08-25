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

// B2 -- señal cruda comparada, reetiquetado del antiguo B3 el 2026-07-22
// (el B2 original de líneas superpuestas se descartó el mismo día). Los archivos
// siguen llamándose husformer_b3_chart.js / husformer_b3_channel_groups.js
// -- no fue posible renombrarlos (sandbox sin acceso a shell en el momento
// del cambio) -- pero todo lo exportado/expuesto ya dice B2.
import {
    renderHusformerB2Chart,
    buildB2Series,
} from "./charts/husformer_b3_chart.js";

// C1/C2 -- Vista C, SEGUNDO rediseño el mismo día (2026-07-22, a pedido de
// Russell): el primer rediseño (Small Multiples por selectedTrials,
// husformer_c1_small_multiples_chart.js / husformer_c2_vad_chart.js -- ver
// esos archivos, NO borrados) no le convenció -- quería algo anclado a una
// ACCIÓN sobre B2 (la señal cruda), no a la selección de A1/A2. C1 vuelve a
// ser el original (matriz de UNA ventana puntual, revivido tal cual estaba,
// solo cambia el disparador: antes hover en B1, ahora hover en B2). C2 es
// nuevo: señal real + dominancia de atención juxtapuestas, misma ventana de
// tiempo, mismo disparador.
import {
    renderHusformerC1Chart,
} from "./charts/husformer_c1_chart.js";

import {
    renderHusformerC2SignalAttentionChart,
} from "./charts/husformer_c2_signal_attention_overlay_chart.js";

import {
    EEG_REGION_GROUPS,
    EEG_HEMISPHERE_GROUPS,
    EOG_GROUPS,
    EMG_GROUPS,
    GSR_GROUPS,
    AUTONOMIC_GROUPS,
    findB2Group,
    MAX_SIMULTANEOUS_SIGNALS,
    DEFAULT_B2_GROUP_IDS,
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

// A3 -- comparación de PERFIL DE CUESTIONARIO de los participantes de los
// trials seleccionados en A1/A2 (gramática visual LineUp -- ver
// husformer_a3_panel.js). Vuelto a este diseño el 2026-07-22: la sesión
// había probado un mapa de red de patrones de fusión (attn_cross_summary,
// similitud coseno entre trials) en su lugar, pero Russell decidió
// descartarlo y volver al perfil de cuestionario -- ver
// husformer_a3_resumen_implementacion.md para el historial completo.
//
// A diferencia del mapa de red (dataset completo, independiente de la
// selección), A3 depende DIRECTAMENTE de `selectedTrials` -- la misma
// selección compartida de A1/A2, no una propia. Se re-pide cada vez que la
// selección cambia (ver loadAndRenderA3Profiles, llamada desde
// handlePointToggle/handleBackgroundClick/handleRemoveParticipant).
let latestA3ProfileData = null;
let a3RequestId = 0;

/**
 * Cuenta cuántos trials seleccionados pertenecen a cada participante --
 * insumo del panel LineUp (label "P01 (3)" = 3 trials de P01 en la
 * selección actual).
 */
function getParticipantTrialCounts() {
    const counts = new Map();

    selectedTrials.forEach((point) => {
        counts.set(point.Participant_id, (counts.get(point.Participant_id) ?? 0) + 1);
    });

    return counts;
}

/**
 * Botón "×" de una fila de A3 -- quita TODOS los trials de ese participante
 * de la selección compartida (no solo uno), y re-renderiza A1/A2/A3.
 */
function handleRemoveParticipant(participantId) {
    Array.from(selectedTrials.entries())
        .filter(([, point]) => point.Participant_id === participantId)
        .forEach(([key]) => selectedTrials.delete(key));

    renderA1();
    renderA2();
    loadAndRenderA3Profiles();
}

function renderA3() {
    renderHusformerA3Panel({
        containerId: "a3-chart",
        profileData: latestA3ProfileData,
        participantTrialCounts: getParticipantTrialCounts(),
        onRemoveParticipant: handleRemoveParticipant,
    });
}

/**
 * Pide al backend (reutiliza /api/h2/participant-profiles, cero backend
 * nuevo) el perfil de los participantes con AL MENOS un trial en
 * `selectedTrials`. Mismo patrón de guard de condición de carrera que
 * a2RequestId/b1RequestId/c1RequestId.
 */
async function loadAndRenderA3Profiles() {
    a3RequestId += 1;
    const requestId = a3RequestId;

    const participantIds = Array.from(
        new Set(Array.from(selectedTrials.values()).map((point) => point.Participant_id))
    );

    if (participantIds.length === 0) {
        latestA3ProfileData = null;
        renderA3();
        return;
    }

    const data = await fetchH2ParticipantProfiles(participantIds);

    if (requestId !== a3RequestId) {
        return;
    }

    latestA3ProfileData = data;
    renderA3();
}

let resizeObserverA3 = null;
let lastObservedWidthA3 = 0;
let lastObservedHeightA3 = 0;

function observeA3Container() {
    const container = document.getElementById("a3-chart");

    if (!container || resizeObserverA3) {
        return;
    }

    resizeObserverA3 = new ResizeObserver((entries) => {
        const { width, height } = entries[0].contentRect;

        if (width === lastObservedWidthA3 && height === lastObservedHeightA3) {
            return;
        }

        lastObservedWidthA3 = width;
        lastObservedHeightA3 = height;

        if (width > 0 && height > 0) {
            renderA3();
        }
    });

    resizeObserverA3.observe(container);
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

// Handles devueltos por renderHusformerB1Chart/B2Chart (2026-07-17,
// sincronización bidireccional B1 <-> B2, a pedido de Russell) -- cada
// chart expone { highlightWindow(windowIndex), clearHighlight() } para que
// OTRO panel pueda resaltar una ventana en él sin reconstruir su SVG
// entero. Se reasignan en cada render (el chart viejo ya no existe en el
// DOM), y pueden ser null si el panel está en estado vacío/cargando (esos
// casos retornan null en vez de un handle) -- por eso todo acceso usa `?.`.
let activeB1Handle = null;
let activeB2Handle = null;

function renderB1() {
    // Hover en B1 sigue sincronizando el resaltado con B2 (linked
    // highlighting, sin reconstruir el SVG de ninguno de los dos --
    // Becker & Cleveland 1987, Munzner Cap. 12.3.3). Ya NO dispara nada
    // hacia Vista C (2026-07-22, a pedido de Russell): C1/C2 dependen de
    // selectedTrials (selección de A1/A2), no de una ventana puntual de B1
    // -- ese mecanismo (selectedWindowIndex/handleWindowSelect) se retiró
    // junto con el C1 original.
    const onHoverWindowChange = (windowIndex) => {
        if (windowIndex === null) {
            activeB2Handle?.clearHighlight();
        } else {
            activeB2Handle?.highlightWindow(windowIndex);
        }
    };

    activeB1Handle = renderHusformerB1Chart({
        containerId: "b1-chart",
        activeTrial: lastClickedTrial,
        attentionData: latestB1Data,
        onHoverWindowChange,
    });

    renderB1Context();
}

/**
 * Actualiza el label de trial activo y la leyenda de color de B1 (dinámica,
 * min/max del trial actual).
 */
function renderB1Context() {
    const label = document.getElementById("husformer-b1-trial-label");
    const heatmapLegend = document.getElementById("husformer-b1-legend");

    if (!lastClickedTrial) {
        label.textContent = "";
        heatmapLegend.innerHTML = "";
        return;
    }

    label.textContent = `${lastClickedTrial.Participant_label} · Trial ${lastClickedTrial.Trial}`;

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
// Vista C -- C1 (matriz 5x5 cross-modal de UNA ventana puntual, revivida) y
// C2 (señal real + dominancia de atención juxtapuestas), SEGUNDO rediseño
// el mismo día (2026-07-22) -- ambos disparados por HOVER en B2, no por la
// selección de A1/A2 (primer rediseño, descartado por Russell).
//
// hoveredB2WindowIndex es el estado nuevo: la ventana de 1s que el mouse
// está sobrevolando en B2 en este momento. null = todavía no hubo hover en
// esta sesión de trial activo.
// ============================================================
let hoveredB2WindowIndex = null;

// Última respuesta de /window-cross-attention -- { participant_id, trial,
// window_index, window_start_sec, split, modality_labels, matrix: 5x5 }.
let latestC1Data = null;
let c1RequestId = 0;

let resizeObserverC1 = null;
let lastObservedWidthC1 = 0;
let lastObservedHeightC1 = 0;

let resizeObserverC2 = null;
let lastObservedWidthC2 = 0;
let lastObservedHeightC2 = 0;

function renderC1() {
    renderHusformerC1Chart({
        containerId: "c1-chart",
        activeTrial: lastClickedTrial,
        selectedWindowIndex: hoveredB2WindowIndex,
        crossAttentionData: latestC1Data,
    });
}

/**
 * Pide al backend la matriz cross-modal de la ventana hovereada en B2 --
 * mismo patrón que loadAndRenderC1 en su versión original (fetch al vuelo,
 * guard de condición de carrera con requestId).
 */
async function loadAndRenderC1() {
    c1RequestId += 1;
    const requestId = c1RequestId;

    latestC1Data = null;
    renderC1();

    const data = await fetchHusformerWindowCrossAttention({
        participantId: lastClickedTrial.Participant_id,
        trial: lastClickedTrial.Trial,
        windowIndex: hoveredB2WindowIndex,
    });

    if (requestId !== c1RequestId) {
        return;
    }

    latestC1Data = data;
    renderC1();
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

/**
 * C2 -- sin fetch propio: reutiliza `latestB2RawResponse` (señal cruda ya
 * cargada por B2, sin normalizar) y `latestB1Data.windows` (% de dominancia
 * ya cargado por B1) -- ambos ya están en memoria cuando hay hover en B2,
 * así que renderC2 es puramente síncrono.
 */
function renderC2() {
    const activeModalities = getSelectedB2GroupsWithColor().reduce((accumulated, group) => {
        // Deduplicar por modalidad -- si hay dos grupos de la misma
        // modalidad activos (ej. EEG Región + EEG Hemisferio), sus canales
        // se promedian JUNTOS en una sola tarjeta, no una por grupo (C2
        // trabaja al nivel de modalidad, igual que la dominancia de B1).
        const baseModalityKey = group.modalityKey.replace(/h$/, ""); // modality_1h -> modality_1
        const existing = accumulated.find((entry) => entry.modalityKey === baseModalityKey);

        if (existing) {
            existing.channels.push(...group.channels);
        } else {
            // modality_labels viene de la misma respuesta que ya cargó B1
            // ({modality_1: "EEG", ...}) -- única fuente de verdad, evita
            // duplicar el mapeo modalidad->nombre acá.
            accumulated.push({
                modalityKey: baseModalityKey,
                label: latestB1Data?.modality_labels?.[baseModalityKey] ?? baseModalityKey,
                channels: [...group.channels],
                color: getSignalColor(baseModalityKey, 0),
            });
        }

        return accumulated;
    }, []);

    renderHusformerC2SignalAttentionChart({
        containerId: "c2-chart",
        activeTrial: lastClickedTrial,
        hoveredWindowIndex: hoveredB2WindowIndex,
        activeModalities,
        rawSignalResponse: latestB2RawResponse,
        b1Windows: latestB1Data?.windows,
    });
}

function observeC2Container() {
    const container = document.getElementById("c2-chart");

    if (!container || resizeObserverC2) {
        return;
    }

    resizeObserverC2 = new ResizeObserver((entries) => {
        const { width, height } = entries[0].contentRect;

        if (width === lastObservedWidthC2 && height === lastObservedHeightC2) {
            return;
        }

        lastObservedWidthC2 = width;
        lastObservedHeightC2 = height;

        if (width > 0 && height > 0) {
            renderC2();
        }
    });

    resizeObserverC2.observe(container);
}

/**
 * Handler único para el hover en B2 -- actualiza el estado compartido y
 * dispara C1 (fetch) + C2 (síncrono). Mismo guard que el mecanismo
 * original de B1->C1: `windowIndex === null` (mouse salió de B2) no limpia
 * nada -- C1/C2 se quedan mostrando la última ventana (sticky), y
 * `windowIndex === hoveredB2WindowIndex` evita un fetch redundante en cada
 * `mousemove` dentro de la misma ventana.
 */
function handleB2WindowHover(windowIndex) {
    if (windowIndex === null || windowIndex === hoveredB2WindowIndex) {
        return;
    }

    hoveredB2WindowIndex = windowIndex;
    loadAndRenderC1();
    renderC2();
}

// ============================================================
// B2 -- comparación de señales crudas normalizadas (rediseño 2026-07-17,
// ver husformer_b3_chart.js / husformer_b3_channel_groups.js). Selección
// MÚLTIPLE de grupos (no un canal suelto), hasta MAX_SIMULTANEOUS_SIGNALS
// a la vez. Ya NO muestra atención acá -- B1 está siempre visible al
// lado, mostrarla de nuevo era redundante (ver corrección en el .md).
// Panel propio restaurado el 2026-07-22 (antes compartía temporalmente
// espacio con la prueba del grafo de A3, ver husformer_a3_resumen_
// implementacion.md).
// ============================================================

// IDs de los grupos actualmente seleccionados, en orden de selección
// (Set preserva orden de inserción en JS) -- el orden importa para que el
// color de cada señal sea estable mientras no cambie la selección.
// Arranca con DEFAULT_B2_GROUP_IDS (2026-07-17, a pedido de Russell: una
// señal de cada una de las 6 familias, para que la primera impresión del
// panel ya muestre una comparación representativa entre modalidades).
let selectedB2GroupIds = new Set(DEFAULT_B2_GROUP_IDS);

// Respuesta cruda de /api/trial-signals -- incluye TODOS los canales que
// hacen falta para promediar los grupos actualmente seleccionados (un solo
// fetch combinado, no uno por grupo).
let latestB2RawResponse = null;
let b2RequestId = 0;

let resizeObserverB2 = null;
let lastObservedWidthB2 = 0;
let lastObservedHeightB2 = 0;

// Transform de zoom de B2 -- SOLO zoom/pan en X (ver husformer_b3_
// chart.js). Se persiste acá para sobrevivir a re-renders (resize, cambio
// de selección de señales), mismo patrón que currentZoomTransform de A1 y
// el de B1. null = sin zoom (vista completa 0-60s).
let currentB2ZoomTransform = null;

/**
 * Arma la lista de series (una por grupo seleccionado, promediada y
 * normalizada) a partir de la respuesta cruda ya cargada, y renderiza B2.
 * Separado de loadAndRenderB2 porque cambiar CUÁLES colores usa cada
 * chip activo (getSignalColor) no necesita un fetch nuevo -- solo
 * reconstruir las series con el mismo dato ya en memoria.
 */
function renderB2() {
    const label = document.getElementById("husformer-b2-trial-label");
    label.textContent = lastClickedTrial
        ? `${lastClickedTrial.Participant_label} · Trial ${lastClickedTrial.Trial}`
        : "";

    const selectedGroups = getSelectedB2GroupsWithColor();

    // Tres estados posibles cuando hay trial activo: sin grupos elegidos
    // ([] -- "elegí algo"), esperando el fetch (null -- "cargando"), o ya
    // con datos (array de series). Si no hay trial activo, el valor no
    // importa -- renderHusformerB2Chart revisa activeTrial primero.
    let seriesList = null;

    if (lastClickedTrial && selectedGroups.length === 0) {
        seriesList = [];
    } else if (lastClickedTrial && latestB2RawResponse) {
        seriesList = buildB2Series(latestB2RawResponse, selectedGroups);
    }

    activeB2Handle = renderHusformerB2Chart({
        containerId: "b2-chart",
        activeTrial: lastClickedTrial,
        seriesList,
        initialZoomTransform: currentB2ZoomTransform,
        onZoomChange: (transform) => {
            currentB2ZoomTransform = transform;
        },
        onHoverWindowChange: (windowIndex) => {
            if (windowIndex === null) {
                activeB1Handle?.clearHighlight();
            } else {
                activeB1Handle?.highlightWindow(windowIndex);
            }

            // Dispara C1/C2 (2026-07-22, segundo rediseño de Vista C -- ver
            // handleB2WindowHover) -- mismo guard de "null no limpia nada"
            // que ya usa el resaltado de B1 arriba.
            handleB2WindowHover(windowIndex);
        },
    });

    renderB2SelectorUI();
}

/**
 * Resuelve los grupos seleccionados (definición completa + color final),
 * asignando el color según su posición ENTRE los grupos de la misma
 * modalidad ya seleccionados -- ver getSignalColor en husformer_b3_
 * channel_groups.js.
 */
function getSelectedB2GroupsWithColor() {
    const countByModality = new Map();

    return Array.from(selectedB2GroupIds)
        .map((groupId) => findB2Group(groupId))
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
async function loadAndRenderB2(trialPoint) {
    lastClickedTrial = trialPoint;

    // La ventana hovereada (si había una) pertenece al trial ANTERIOR -- se
    // limpia junto con el cambio de trial (mismo momento en que B2 se
    // recarga). C1/C2 vuelven a su estado vacío hasta el próximo hover.
    hoveredB2WindowIndex = null;
    latestC1Data = null;
    renderC1();
    renderC2();

    b2RequestId += 1;
    const requestId = b2RequestId;

    latestB2RawResponse = null;
    renderB2();

    const selectedGroups = getSelectedB2GroupsWithColor();

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

    if (requestId !== b2RequestId) {
        return;
    }

    latestB2RawResponse = data;
    renderB2();
}

/**
 * Alterna un grupo dentro/fuera de la selección -- respeta el tope
 * MAX_SIMULTANEOUS_SIGNALS (Munzner Cap. 10, límite práctico de bins
 * categóricos discriminables + Cap. 12.5.2, Javed et al. 2010). Si ya no
 * hay ningún trial clickeado todavía, solo actualiza la selección (sin
 * fetch) -- el fetch se dispara recién cuando haya un trial activo.
 */
function toggleB2Group(groupId) {
    if (selectedB2GroupIds.has(groupId)) {
        selectedB2GroupIds.delete(groupId);
    } else {
        if (selectedB2GroupIds.size >= MAX_SIMULTANEOUS_SIGNALS) {
            return;
        }
        selectedB2GroupIds.add(groupId);
    }

    if (lastClickedTrial) {
        loadAndRenderB2(lastClickedTrial);
    } else {
        renderB2SelectorUI();
    }
}

/**
 * Construye el selector de chips agrupados por modalidad -- EEG con dos
 * esquemas (Región / Hemisferio), el resto de las modalidades con sus
 * canales individuales (pocos, no hace falta agruparlos más). Se
 * reconstruye en cada render de B2 (barato, son ~20 botones) para que el
 * estado activo/deshabilitado siempre refleje selectedB2GroupIds.
 */
function renderB2SelectorUI() {
    const container = document.getElementById("husformer-b2-selector");
    container.innerHTML = "";

    const atCap = selectedB2GroupIds.size >= MAX_SIMULTANEOUS_SIGNALS;

    // Mismo color que va a usar el chart -- reutiliza getSelectedB2Groups
    // WithColor en vez de recalcular el índice por modalidad acá también
    // (única fuente de verdad para "qué color le toca a cada grupo activo").
    const colorByGroupId = new Map(
        getSelectedB2GroupsWithColor().map((group) => [group.id, group.color])
    );

    // Punto de color por grupo (2026-07-17, a pedido de Russell -- "que se
    // note la diferencia"): color BASE de la modalidad (índice 0, sin
    // importar si hay algo seleccionado todavía), mismo share encoding que
    // ya usan los chips activos y el heatmap de B1.
    function buildRow(label, groups, modalityKey) {
        const row = document.createElement("div");
        row.className = "husformer-b2-selector-row";

        const rowLabel = document.createElement("span");
        rowLabel.className = "husformer-b2-selector-group-label";

        const dot = document.createElement("span");
        dot.className = "husformer-b2-selector-group-dot";
        dot.style.background = getSignalColor(modalityKey, 0);
        rowLabel.appendChild(dot);

        rowLabel.appendChild(document.createTextNode(label));
        row.appendChild(rowLabel);

        groups.forEach((group) => {
            const isActive = selectedB2GroupIds.has(group.id);

            const button = document.createElement("button");
            button.type = "button";
            button.className = `husformer-b2-chip${isActive ? " active" : ""}`;
            button.textContent = group.label;
            button.disabled = !isActive && atCap;

            if (isActive) {
                button.style.setProperty("--chip-color", colorByGroupId.get(group.id));
            }

            button.addEventListener("click", () => toggleB2Group(group.id));
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
 * Vuelve la vista de B2 al trial completo (0-60s) -- 2026-07-17, a pedido
 * de Russell. Aclarado explícitamente con él: esto SOLO resetea el zoom,
 * no la selección de señales (son dos estados independientes) -- ver
 * husformer_b3_resumen_implementacion.md. El doble-click sobre el chart
 * hace lo mismo (implementado directo en husformer_b3_chart.js), este
 * botón es el mecanismo DESCUBRIBLE -- un doble-click no tiene ninguna
 * pista visual de que existe, a diferencia de un botón.
 */
function resetB2Zoom() {
    currentB2ZoomTransform = null;
    renderB2();
}

function setupB2ChannelControl() {
    renderB2SelectorUI();

    const resetButton = document.getElementById("husformer-b2-reset-zoom");
    resetButton.addEventListener("click", resetB2Zoom);
}

function observeB2Container() {
    const container = document.getElementById("b2-chart");

    if (!container || resizeObserverB2) {
        return;
    }

    resizeObserverB2 = new ResizeObserver((entries) => {
        const { width, height } = entries[0].contentRect;

        if (width === lastObservedWidthB2 && height === lastObservedHeightB2) {
            return;
        }

        lastObservedWidthB2 = width;
        lastObservedHeightB2 = height;

        if (width > 0 && height > 0) {
            renderB2();
        }
    });

    resizeObserverB2.observe(container);
}

// Handlers de selección/fondo COMPARTIDOS entre A1 y A2 -- clickear un punto
// (o el fondo) en cualquiera de los dos paneles re-renderiza AMBOS paneles
// (compound brushing/linked highlighting entre vistas coordinadas, Cap. 12
// de Munzner / Cap. 5 de Aigner). A3 vuelve a depender de selectedTrials
// (revertido el 2026-07-22 al perfil de cuestionario) -- se re-pide en cada
// cambio de selección vía loadAndRenderA3Profiles().
function handlePointToggle(point) {
    const key = getTrialKey(point);

    if (selectedTrials.has(key)) {
        selectedTrials.delete(key);
    } else {
        selectedTrials.set(key, point);
    }

    renderA1();
    renderA2();
    loadAndRenderA3Profiles();

    // Drill-down a Vista B -- ver nota extensa arriba de lastClickedTrial.
    // Se dispara SIEMPRE que se clickea un punto (agregar o quitar de la
    // selección), independientemente del resultado en selectedTrials.
    loadAndRenderB1(point);

    // lastClickedTrial recién queda actualizado DESPUÉS de loadAndRenderB1
    // (es quien lo asigna) -- por eso B2 se dispara con `point` directo, no
    // con la variable, para no depender del orden de ejecución async.
    loadAndRenderB2(point);
}

function handleBackgroundClick() {
    if (selectedTrials.size === 0) {
        return;
    }

    selectedTrials.clear();
    renderA1();
    renderA2();
    loadAndRenderA3Profiles();
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
    setupB2ChannelControl();
    observeA1Container();
    observeA2Container();
    observeA3Container();
    observeB1Container();
    observeB2Container();
    observeC1Container();
    observeC2Container();

    // A1/A2 dependen de fetches asíncronos independientes (proyección y
    // clustering respectivamente) -- se piden en paralelo; cada uno
    // renderiza lo que puede en cuanto llega, y renderA2() se completa solo
    // cuando AMBOS ya están disponibles (ver guard al inicio de renderA2).
    loadAndRenderProjection();
    loadAndRenderClusters();

    // A3 arranca sin selección (nadie ha clickeado nada todavía en A1/A2) --
    // muestra el estado vacío ("Selecciona uno o más trials..."), sin
    // fetch, hasta el primer click (ver loadAndRenderA3Profiles).
    renderA3();

    // B1 arranca sin trial activo (nadie ha clickeado nada todavía) -- solo
    // muestra el estado vacío ("Selecciona un trial en Vista A"), sin
    // fetch, hasta el primer click en A1/A2 (ver loadAndRenderB1).
    renderB1();

    // C1/C2 arrancan sin trial activo ni hover todavía -- estado vacío
    // hasta el primer hover en B2 (ver handleB2WindowHover).
    renderC1();
    renderC2();

    // B2 igual -- estado vacío hasta el primer click (ver loadAndRenderB2).
    renderB2();
}
