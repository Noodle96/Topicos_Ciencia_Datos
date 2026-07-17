import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

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

// Mismos 5 colores categóricos que ya usa husformer_b2_chart.js para las 5
// modalidades -- reutilizados a propósito (Munzner Cap. 12.3.1, "share
// encoding"): una línea azul acá debe poder conectarse visualmente con la
// línea azul de EEG en el panel de atención de B1/B2, sin necesitar una
// leyenda nueva que aprender.
const MODALITY_BASE_COLORS = {
    modality_1: "#2563eb", // EEG
    modality_2: "#dc2626", // EOG
    modality_3: "#16a34a", // EMG
    modality_4: "#d97706", // GSR
    modality_5: "#9333ea", // Resp+Plet+Temp
};

export const EEG_REGION_GROUPS = [
    { id: "eeg_frontal", label: "Frontal", modalityKey: "modality_1", channels: ["Fp1", "Fp2", "AF3", "AF4", "F3", "F4", "F7", "F8", "Fz"] },
    { id: "eeg_central", label: "Central", modalityKey: "modality_1", channels: ["FC5", "FC1", "FC6", "FC2", "C3", "C4", "Cz"] },
    { id: "eeg_temporal", label: "Temporal", modalityKey: "modality_1", channels: ["T7", "T8"] },
    { id: "eeg_parietal", label: "Parietal", modalityKey: "modality_1", channels: ["CP5", "CP1", "CP6", "CP2", "P3", "P4", "P7", "P8", "Pz"] },
    { id: "eeg_occipital", label: "Occipital", modalityKey: "modality_1", channels: ["PO3", "PO4", "O1", "O2", "Oz"] },
];

export const EEG_HEMISPHERE_GROUPS = [
    { id: "eeg_left", label: "Izquierdo", modalityKey: "modality_1", channels: ["Fp1", "AF3", "F3", "F7", "FC5", "FC1", "C3", "T7", "CP5", "CP1", "P3", "P7", "PO3", "O1"] },
    { id: "eeg_right", label: "Derecho", modalityKey: "modality_1", channels: ["Fp2", "AF4", "F4", "F8", "FC6", "FC2", "C4", "T8", "CP6", "CP2", "P4", "P8", "PO4", "O2"] },
    { id: "eeg_midline", label: "Línea media", modalityKey: "modality_1", channels: ["Fz", "Cz", "Pz", "Oz"] },
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

/**
 * Color de una señal específica dentro de su familia de modalidad -- todas
 * las señales de EEG comparten la base azul, pero se distinguen entre sí
 * variando la luminancia/saturación (d3.color().brighter/darker), no el
 * hue -- así una selección múltiple de sub-grupos de EEG (ej. Frontal +
 * Occipital) se sigue leyendo como "la misma modalidad, dos partes
 * distintas", no como colores arbitrarios sin relación.
 */
export function getSignalColor(modalityKey, indexWithinModality) {
    const baseColor = d3.color(MODALITY_BASE_COLORS[modalityKey] ?? "#111827");

    if (indexWithinModality === 0) {
        return baseColor.formatHex();
    }

    // Alterna oscurecer/aclarar para maximizar la distancia perceptual
    // entre selecciones consecutivas de la misma modalidad, en vez de ir
    // siempre en una sola dirección (que agotaría el rango de color rápido).
    const step = Math.ceil(indexWithinModality / 2) * 0.55;
    const adjusted = indexWithinModality % 2 === 1
        ? baseColor.darker(step)
        : baseColor.brighter(step);

    return adjusted.formatHex();
}
