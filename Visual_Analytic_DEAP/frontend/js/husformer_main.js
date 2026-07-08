import {
    fetchHusformerTrialProjection,
} from "./api.js";

import {
    renderHusformerA1Chart,
} from "./charts/husformer_a1_chart.js";

// Trial actualmente seleccionado en A1 -- se resalta en el propio A1 y,
// cuando Vista B exista, va a ser lo que dispare la carga de su dinámica
// temporal (interacción "Clicking: A -> B", ver 05_diseno_visual.tex).
let selectedTrial = null;

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

function renderA1() {
    if (!latestPoints) {
        return;
    }

    renderHusformerA1Chart({
        containerId: "a1-chart",
        points: latestPoints,
        projectionMethod: latestProjectionMethod,
        selectedTrial,
        onPointClick: (point) => {
            selectedTrial = point;
            renderA1();
        },
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

            // Al cambiar de proyección se pierde el sentido de mantener el
            // zoom/selección anterior (las coordenadas x/y son otras) --
            // loadAndRenderA1 recrea el chart desde cero, lo cual ya
            // resetea el zoom automáticamente.
            loadAndRenderA1(method);
        });
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
    observeA1Container();
    loadAndRenderA1();
}
