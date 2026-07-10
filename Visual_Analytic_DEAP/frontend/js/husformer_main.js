import {
    fetchHusformerTrialProjection,
} from "./api.js";

import {
    renderHusformerA1Chart,
} from "./charts/husformer_a1_chart.js";

import {
    renderHusformerA3Panel,
} from "./charts/husformer_a3_panel.js";

/**
 * Construye la clave única de un trial (participante+trial). Duplicada a
 * propósito en husformer_a1_chart.js (una línea; este frontend no tiene
 * ningún módulo de utilidades compartidas todavía, no se justifica crear
 * uno solo por esto).
 */
function getTrialKey(point) {
    return `${point.Participant_id}_${point.Trial}`;
}

// Trials actualmente seleccionados en A1 -- Map<key, point> en vez de un
// único trial (2026-07-07, decisión tomada pensando en A3: la Sección 5
// diseña A3 explícitamente para SELECCIÓN MÚLTIPLE -- comparar varios
// trials a la vez -- así que el modelo de estado se adelanta a eso ahora
// para no tener que reescribirlo cuando se construya A3. Un click en un
// punto alterna su membresía (agrega/quita); un click en el fondo limpia
// todo. Cuando exista Vista B, probablemente consuma solo "el último
// agregado" o requiera su propia noción de trial activo -- no resuelto
// todavía, revisar cuando se llegue a B.
let selectedTrials = new Map();

// Transform de zoom/pan actual (objeto d3.ZoomTransform, o null = todavía
// sin zoom). BUG corregido (2026-07-07, reportado por Russell): cada
// interacción (seleccionar un punto, limpiar selección, redimensionar)
// dispara renderA1(), que reconstruye el SVG entero -- incluyendo un
// d3.zoom() nuevo que arranca sin zoom si no se le indica lo contrario. Se
// guarda acá y se le pasa de vuelta al chart como `initialZoomTransform`
// en cada render para que lo mantenga. Se limpia explícitamente solo
// cuando cambia el método de proyección (si cambian las coordenadas x/y,
// mantener el mismo zoom en píxeles ya no tiene sentido).
let currentZoomTransform = null;

// Filtros de resaltado (2026-07-07, a pedido de Russell). "" = sin filtro
// (Todos = reset). Se combinan con AND en el chart (isPointDimmed): si
// ambos están activos, solo el punto que matchea los dos queda sin
// atenuar. Son ORTOGONALES a selectedTrials -- un filtro atenúa/resalta
// por atributo (participante/trial), la selección marca puntos puntuales
// clickeados; pueden estar activos los dos a la vez (la selección gana
// visualmente, ver husformer_a1_chart.js).
let participantFilter = "";
let trialFilter = "";

// Método de proyección por defecto para A1. Decisión resuelta (2026-07-07):
// selector lineal estilo EvoAir dentro del propio panel A1 (ver
// #husformer-a1-projection-control en index.html), no un <select> nativo.
const DEFAULT_PROJECTION_METHOD = "pca";

// Cache de los puntos ya cargados -- permite re-renderizar (por resize/
// cambio de visibilidad) sin volver a pedirlos al backend.
let latestPoints = null;
let latestProjectionMethod = DEFAULT_PROJECTION_METHOD;

// BUG encontrado (2026-07-07, el mismo que ya existía en Tarea1): initApp()
// llama a initializeHusformerView() al arrancar la app, cuando System
// Overview todavía tiene "hidden-view" (display:none). Un elemento con
// display:none mide clientWidth/clientHeight = 0, así que el primer render
// usa el tamaño de respaldo chico (360x260, ver husformer_a1_chart.js). El
// chart recién se vuelve a dibujar -- con el tamaño real y grande del panel
// -- la próxima vez que algo dispara un re-render (ej. un click), lo que se
// percibe como "se agranda de golpe" al hacer click. No es que el click
// cause el bug: el click solo es la primera oportunidad en la que el
// código vuelve a medir el contenedor, y para entonces la pestaña ya está
// visible.
//
// FIX: un ResizeObserver sobre #a1-chart. Un elemento display:none que pasa
// a visible SÍ dispara ResizeObserver (su tamaño cambia de 0x0 al tamaño
// real), así que re-renderiza automáticamente en el momento correcto, sin
// depender de que el usuario haga click primero, y sin acoplarse a
// view_navigation.js. Bonus: también corrige el tamaño si la ventana se
// redimensiona.
let resizeObserver = null;
let lastObservedWidth = 0;
let lastObservedHeight = 0;

// A3 (panel de comparación) lee el mismo Map selectedTrials -- no pide
// nada al backend, así que renderA3() es barato de llamar cada vez que la
// selección cambia. No necesita ResizeObserver (es una <table> HTML, se
// reacomoda sola vía CSS, a diferencia del SVG de A1).
function renderA3() {
    renderHusformerA3Panel({
        containerId: "a3-chart",
        selectedTrials,
        onRemoveTrial: (point) => {
            const key = getTrialKey(point);
            selectedTrials.delete(key);
            renderA1();
            renderA3();
        },
    });
}

function renderA1() {
    if (!latestPoints) {
        return;
    }

    renderHusformerA1Chart({
        containerId: "a1-chart",
        points: latestPoints,
        projectionMethod: latestProjectionMethod,
        selectedTrials,
        onPointClick: (point) => {
            const key = getTrialKey(point);

            if (selectedTrials.has(key)) {
                selectedTrials.delete(key);
            } else {
                selectedTrials.set(key, point);
            }

            renderA1();
            renderA3();
        },
        onBackgroundClick: () => {
            if (selectedTrials.size === 0) {
                return;
            }

            selectedTrials.clear();
            renderA1();
            renderA3();
        },
        initialZoomTransform: currentZoomTransform,
        onZoomChange: (transform) => {
            currentZoomTransform = transform;
        },
        participantFilter,
        trialFilter,
    });
}

async function loadAndRenderA1(projectionMethod = DEFAULT_PROJECTION_METHOD) {
    const data = await fetchHusformerTrialProjection({
        method: projectionMethod,
    });

    latestPoints = data.points;
    latestProjectionMethod = projectionMethod;

    renderA1();
}

function setupProjectionControl() {
    const buttons = document.querySelectorAll(
        "#husformer-a1-projection-control .husformer-a1-projection-option"
    );

    buttons.forEach((button) => {
        button.addEventListener("click", () => {
            const method = button.dataset.method;

            if (method === latestProjectionMethod) {
                return;
            }

            buttons.forEach((otherButton) => {
                otherButton.classList.toggle(
                    "active",
                    otherButton === button
                );
            });

            // Al cambiar de proyección, el zoom en píxeles ya no tiene
            // sentido (las coordenadas x/y son otras) -- se resetea a
            // propósito acá, es la ÚNICA situación donde currentZoomTransform
            // se limpia explícitamente. La selección SÍ se mantiene a
            // propósito (selectedTrials no se toca): sigue siendo el mismo
            // trial/conjunto de trials, solo cambia dónde caen en el plano 2D.
            currentZoomTransform = null;
            loadAndRenderA1(method);
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

function observeA1Container() {
    const container = document.getElementById("a1-chart");

    if (!container || resizeObserver) {
        return;
    }

    resizeObserver = new ResizeObserver((entries) => {
        const { width, height } = entries[0].contentRect;

        if (width === lastObservedWidth && height === lastObservedHeight) {
            return;
        }

        lastObservedWidth = width;
        lastObservedHeight = height;

        if (width > 0 && height > 0) {
            renderA1();
        }
    });

    resizeObserver.observe(container);
}

export function initializeHusformerView() {
    setupProjectionControl();
    setupFilterControls();
    observeA1Container();
    loadAndRenderA1();

    // A3 no depende de latestPoints (solo de selectedTrials, que arranca
    // vacío) -- se puede renderizar de una vez, sin esperar al fetch
    // asíncrono de A1, para mostrar el estado vacío correcto desde el
    // primer instante.
    renderA3();
}
