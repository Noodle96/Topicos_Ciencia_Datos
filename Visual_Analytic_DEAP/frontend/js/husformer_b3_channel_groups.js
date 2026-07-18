/**
 * Definiciones de "grupos seleccionables" para el selector de B3
 * (2026-07-17, rediseño a pedido de Russell -- reemplaza el selector de
 * 44 canales individuales).
 *
 * Por qué agrupar en vez de listar 44 canales: Munzner Cap. 12 (12.5.2,
 * Javed et al. 2010) -- superponer líneas "funciona bien con pocos ítems
 * (una docena es manejable) pero no escala a cientos", y T5 es una tarea
 * de precisión (encontrar UN pico puntual), no de overview -- conviene un
 * límite chico, no grande. Los 32 canales de EEG en particular no tienen
 * sentido como 32 opciones sueltas para alguien que no sea especialista en
 * montajes de electrodos -- se agrupan por REGIÓN ANATÓMICA (Frontal,
 * Central, Temporal, Parietal, Occipital) y, alternativamente, por
 * HEMISFERIO (Izquierdo, Derecho, Línea media) -- ambos esquemas
 * disponibles a la vez, el usuario elige de cuál partir. Cada grupo se
 * PROMEDIA en vivo a partir de sus canales reales (ver husformer_main.js,
 * loadAndRenderB3) -- no hay agregación precomputada.
 *
 * EOG/EMG/GSR/Resp+Plet+Temp NO se agrupan más allá de la modalidad
 * misma -- son pocos canales (4, 4, 1 y 3 respectivamente), listarlos
 * sueltos no genera el problema de escala que sí tiene EEG.
 */

export const EEG_REGION_GROUPS = [
    { id: "eeg_frontal", label: "Frontal", modalityKey: "modality_1", channels: ["Fp1", "Fp2", "AF3", "AF4", "F3", "F4", "F7", "F8", "Fz"] },
    { id: "eeg_central", label: "Central", modalityKey: "modality_1", channels: ["FC5", "FC1", "FC6", "FC2", "C3", "C4", "Cz"] },
    { id: "eeg_temporal", label: "Temporal", modalityKey: "modality_1", channels: ["T7", "T8"] },
    { id: "eeg_parietal", label: "Parietal", modalityKey: "modality_1", channels: ["CP5", "CP1", "CP6", "CP2", "P3", "P4", "P7", "P8", "Pz"] },
    { id: "eeg_occipital", label: "Occipital", modalityKey: "modality_1", channels: ["PO3", "PO4", "O1", "O2", "Oz"] },
];

// Hemisferio usa una MODALITYKEY DISTINTA ("modality_1h", no "modality_1")
// -- 2026-07-17, corrección a pedido de Russell: al variar solo luminancia
// dentro de la misma familia azul, Región y Hemisferio se confundían entre
// sí, sobre todo con la selección por defecto (Frontal + Izquierdo activos
// a la vez). Se le da a Hemisferio su propia familia de color (cian, no
// azul) -- distinguible por HUE, no solo por luminancia, que es el canal
// correcto para distinguir CATEGORÍAS (Munzner Cap. 5, "los categóricos
// deben mostrarse con canales de identidad" -- Región vs. Hemisferio son
// dos esquemas de agrupamiento distintos, categóricamente separados, no
// solo dos variantes de intensidad de lo mismo). El costo es que
// Hemisferio ya no comparte el azul exacto de la línea de EEG en B1/B2
// (Región sí lo sigue haciendo) -- trade-off aceptado explícitamente por
// Russell a cambio de que Región/Hemisferio dejen de confundirse.
export const EEG_HEMISPHERE_GROUPS = [
    { id: "eeg_left", label: "Izquierdo", modalityKey: "modality_1h", channels: ["Fp1", "AF3", "F3", "F7", "FC5", "FC1", "C3", "T7", "CP5", "CP1", "P3", "P7", "PO3", "O1"] },
    { id: "eeg_right", label: "Derecho", modalityKey: "modality_1h", channels: ["Fp2", "AF4", "F4", "F8", "FC6", "FC2", "C4", "T8", "CP6", "CP2", "P4", "P8", "PO4", "O2"] },
    { id: "eeg_midline", label: "Línea media", modalityKey: "modality_1h", channels: ["Fz", "Cz", "Pz", "Oz"] },
];

export const EOG_GROUPS = [
    { id: "eog_exg1", label: "EXG1", modalityKey: "modality_2", channels: ["EXG1"] },
    { id: "eog_exg2", label: "EXG2", modalityKey: "modality_2", channels: ["EXG2"] },
    { id: "eog_exg3", label: "EXG3", modalityKey: "modality_2", channels: ["EXG3"] },
    { id: "eog_exg4", label: "EXG4", modalityKey: "modality_2", channels: ["EXG4"] },
];

export const EMG_GROUPS = [
    { id: "emg_exg5", label: "EXG5", modalityKey: "modality_3", channels: ["EXG5"] },
    { id: "emg_exg6", label: "EXG6", modalityKey: "modality_3", channels: ["EXG6"] },
    { id: "emg_exg7", label: "EXG7", modalityKey: "modality_3", channels: ["EXG7"] },
    { id: "emg_exg8", label: "EXG8", modalityKey: "modality_3", channels: ["EXG8"] },
];

export const GSR_GROUPS = [
    { id: "gsr_gsr1", label: "GSR1", modalityKey: "modality_4", channels: ["GSR1"] },
];

export const AUTONOMIC_GROUPS = [
    { id: "auto_resp", label: "Resp", modalityKey: "modality_5", channels: ["Resp"] },
    { id: "auto_plet", label: "Plet", modalityKey: "modality_5", channels: ["Plet"] },
    { id: "auto_temp", label: "Temp", modalityKey: "modality_5", channels: ["Temp"] },
];

// Todas las opciones seleccionables, en un solo array (usado para
// resolver un id -> definición completa, y para armar el fetch combinado).
export const ALL_B3_GROUPS = [
    ...EEG_REGION_GROUPS,
    ...EEG_HEMISPHERE_GROUPS,
    ...EOG_GROUPS,
    ...EMG_GROUPS,
    ...GSR_GROUPS,
    ...AUTONOMIC_GROUPS,
];

export function findB3Group(groupId) {
    return ALL_B3_GROUPS.find((group) => group.id === groupId);
}

// Máximo de señales simultáneas -- Munzner Cap. 10 (límite práctico de
// bins categóricos discriminables, 6-12) combinado con el hallazgo de
// Javed et al. 2010 (Cap. 12.5.2: superponer escala mal más allá de una
// docena, y T5 es una tarea de precisión que se beneficia de MENOS líneas,
// no más) -- 6 es un techo conservador para que la comparación puntual siga
// siendo legible.
export const MAX_SIMULTANEOUS_SIGNALS = 6;

// Selección por defecto al abrir B3 (2026-07-17, a pedido de Russell) --
// una señal de cada una de las 6 familias de color/modalidad, para que la
// primera impresión del panel ya muestre una comparación representativa
// entre TODAS las modalidades a la vez, no solo EEG. Coincide exactamente
// con MAX_SIMULTANEOUS_SIGNALS (las 6 quedan activas de entrada).
export const DEFAULT_B3_GROUP_IDS = [
    "eeg_frontal",
    "eeg_left",
    "eog_exg1",
    "emg_exg5",
    "gsr_gsr1",
    "auto_resp",
];

// Rampas de color explícitas por familia (2026-07-17, reemplaza el cálculo
// dinámico anterior con d3.color().brighter()/darker()) -- a pedido de
// Russell: "en alguno no veo la diferencia". El cálculo dinámico anterior
// podía producir pasos demasiado sutiles (sobre todo yéndose hacia
// colores muy claros, que pierden contraste contra el fondo blanco del
// panel). Acá los tonos están elegidos a mano (escala Tailwind 300/400/
// 600/800/900 de cada hue), con saltos de luminosidad grandes y
// verificables, no calculados sobre la marcha.
const COLOR_RAMPS = {
    modality_1: ["#2563eb", "#1e3a8a", "#60a5fa", "#1e40af", "#93c5fd"],  // EEG Región -- azul
    modality_1h: ["#0891b2", "#164e63", "#67e8f9", "#155e75", "#a5f3fc"], // EEG Hemisferio -- cian (hue distinto a azul, no solo más claro/oscuro)
    modality_2: ["#dc2626", "#7f1d1d", "#f87171", "#991b1b", "#fca5a5"], // EOG -- rojo
    modality_3: ["#16a34a", "#14532d", "#4ade80", "#166534", "#86efac"], // EMG -- verde
    modality_4: ["#d97706", "#78350f", "#fbbf24", "#92400e", "#fcd34d"], // GSR -- ámbar
    modality_5: ["#9333ea", "#581c87", "#c084fc", "#6b21a8", "#e9d5ff"], // Resp+Plet+Temp -- púrpura
};

/**
 * Color de una señal específica dentro de su familia de modalidad --
 * ÍNDICE 0 siempre es el tono "base" de esa familia; los siguientes
 * índices van tomando los demás tonos de la rampa (definidos a mano para
 * garantizar contraste real entre pasos, ver COLOR_RAMPS). Si se
 * selecciona más señales de una modalidad que tonos tiene la rampa
 * (raro, dado el tope de MAX_SIMULTANEOUS_SIGNALS=6 compartido entre
 * TODAS las modalidades), se cicla desde el principio.
 */
export function getSignalColor(modalityKey, indexWithinModality) {
    const ramp = COLOR_RAMPS[modalityKey] ?? ["#111827"];
    return ramp[indexWithinModality % ramp.length];
}
