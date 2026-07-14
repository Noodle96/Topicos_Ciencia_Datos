import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

/**
 * Renderiza el sub-panel A3 -- comparación de perfil de participante,
 * reformulado (2026-07-08) con gramática visual inspirada en LineUp
 * (Gratzl, Lex, Gehlenborg, Pfister & Streit, 2013, IEEE TVCG 19(12):
 * 2277-2286, Best Paper Award IEEE InfoVis 2013): una tabla compacta donde
 * cada fila es un ítem (acá, un participante) y cada celda es una barra,
 * no texto -- atributos categóricos como segmento de color (mismo color =
 * misma categoría, DENTRO de esa columna), atributos numéricos como barra
 * horizontal proporcional al valor normalizado.
 *
 * Decisión de alcance (2026-07-08, Russell): A3 ya NO compara Valencia/
 * Activación/Dominancia/Liking (eso ya está codificado por color y tooltip
 * en A1, mostrarlo de nuevo en texto no aportaba nada -- primera versión
 * de A3, descartada). En su lugar compara atributos de CUESTIONARIO del
 * participante (género, lateralidad manual, consumo de alcohol/cafeína,
 * edad, horas de sueño, etc.), como apoyo complementario a T1: una vez
 * identificado un trial/participante atípico en A1, A3 ayuda a explorar si
 * comparte rasgos demográficos con otros seleccionados -- ver justificación
 * completa en 05_diseno_visual.tex.
 *
 * NO llama al backend directamente -- reutiliza el mismo dato
 * (`profileData`) que ya devuelve `/api/h2/participant-profiles`
 * (fetchH2ParticipantProfiles en api.js), el mismo endpoint que usa la
 * vista de perfiles de H2. Cero backend nuevo. `husformer_main.js` hace el
 * fetch y pasa `profileData` ya resuelto.
 */
const CATEGORICAL_COLOR_SCHEME = d3.schemeTableau10;

/**
 * Construye una escala de color ordinal para UN atributo categórico
 * puntual (ej. Gender) -- las escalas NO se comparten entre atributos
 * distintos, cada columna tiene su propio dominio de categorías.
 */
function buildCategoricalColorScale(profileData, attribute) {
    const values = Array.from(
        new Set(
            profileData.records
                .map((record) => record.categorical[attribute])
                .filter((value) => value !== null)
        )
    );

    return d3.scaleOrdinal().domain(values).range(CATEGORICAL_COLOR_SCHEME);
}

function findNumericRange(profileData, attribute) {
    return profileData.numeric_ranges.find(
        (range) => range.attribute === attribute
    );
}

/**
 * `common_patterns` viene del backend como oraciones tipo "All selected
 * participants share Gender: F." -- alcanza con revisar si el nombre del
 * atributo aparece ahí para saber si TODA la selección actual comparte ese
 * valor (no hace falta re-derivarlo en el frontend).
 */
function isCommonPattern(profileData, attribute) {
    return profileData.common_patterns.some((sentence) =>
        sentence.includes(`share ${attribute}:`)
    );
}

function buildHeaderRow(profileData) {
    const headerRow = document.createElement("tr");

    const participantHeaderCell = document.createElement("th");
    participantHeaderCell.className = "husformer-a3-sticky-col";
    participantHeaderCell.textContent = "Participante";
    headerRow.appendChild(participantHeaderCell);

    const allAttributes = [
        ...profileData.categorical_attributes,
        ...profileData.numeric_attributes,
    ];

    allAttributes.forEach((attribute) => {
        const th = document.createElement("th");
        th.className = "husformer-a3-attr-col";

        if (isCommonPattern(profileData, attribute)) {
            th.classList.add("husformer-a3-common-col");
        }

        const label = document.createElement("span");
        label.className = "husformer-a3-attr-label";
        label.textContent = attribute;
        label.title = attribute;
        th.appendChild(label);

        headerRow.appendChild(th);
    });

    return headerRow;
}

function buildCategoricalCell(profileData, categoricalScales, attribute, record) {
    const td = document.createElement("td");
    td.className = "husformer-a3-attr-col";

    if (isCommonPattern(profileData, attribute)) {
        td.classList.add("husformer-a3-common-col");
    }

    const value = record.categorical[attribute];

    if (value === null) {
        const na = document.createElement("span");
        na.className = "husformer-a3-na";
        na.textContent = "—";
        td.appendChild(na);
        return td;
    }

    const bar = document.createElement("div");
    bar.className = "husformer-a3-cat-bar";
    bar.style.background = categoricalScales[attribute](value);
    bar.title = `${attribute}: ${value}`;
    td.appendChild(bar);

    return td;
}

function buildNumericCell(profileData, attribute, record) {
    const td = document.createElement("td");
    td.className = "husformer-a3-attr-col";

    const value = record.numeric[attribute];
    const range = findNumericRange(profileData, attribute);

    if (value === null || value === undefined || !range || range.range === null) {
        const na = document.createElement("span");
        na.className = "husformer-a3-na";
        na.textContent = "—";
        td.appendChild(na);
        return td;
    }

    // Si todos los seleccionados tienen el mismo valor (range.range === 0),
    // la barra se dibuja llena -- no hay nada que normalizar, y una barra
    // vacía sería engañosa (parecería "valor bajo" cuando en realidad es
    // "todos iguales").
    const ratio = range.range === 0 ? 1 : (value - range.min) / range.range;

    const track = document.createElement("div");
    track.className = "husformer-a3-num-track";

    const fill = document.createElement("div");
    fill.className = "husformer-a3-num-fill";
    fill.style.width = `${Math.max(6, ratio * 100)}%`;
    fill.title = `${attribute}: ${value}`;

    track.appendChild(fill);
    td.appendChild(track);

    return td;
}

function buildParticipantRow({
    profileData,
    categoricalScales,
    record,
    trialCount,
    onRemoveParticipant,
}) {
    const row = document.createElement("tr");

    const participantCell = document.createElement("td");
    participantCell.className = "husformer-a3-sticky-col";

    const label = document.createElement("span");
    label.className = "husformer-a3-participant-label";
    label.textContent = `${record.Participant_id} (${trialCount})`;
    label.title = `${trialCount} trial(s) seleccionado(s) de ${record.Participant_id}`;
    participantCell.appendChild(label);

    const removeButton = document.createElement("button");
    removeButton.className = "husformer-a3-remove-btn";
    removeButton.type = "button";
    removeButton.textContent = "×";
    removeButton.setAttribute(
        "aria-label",
        `Quitar todos los trials de ${record.Participant_id} de la comparación`
    );
    removeButton.addEventListener("click", () => {
        if (onRemoveParticipant) {
            onRemoveParticipant(record.Participant_id);
        }
    });
    participantCell.appendChild(removeButton);

    row.appendChild(participantCell);

    profileData.categorical_attributes.forEach((attribute) => {
        row.appendChild(
            buildCategoricalCell(profileData, categoricalScales, attribute, record)
        );
    });

    profileData.numeric_attributes.forEach((attribute) => {
        row.appendChild(buildNumericCell(profileData, attribute, record));
    });

    return row;
}

export function renderHusformerA3Panel({
    containerId,
    profileData,
    participantTrialCounts,
    onRemoveParticipant,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    if (!profileData || !profileData.records || profileData.records.length === 0) {
        const empty = document.createElement("div");
        empty.className = "husformer-a3-empty";
        empty.textContent = "Selecciona uno o más trials en A1 para comparar el perfil de sus participantes aquí.";
        container.appendChild(empty);
        return;
    }

    const categoricalScales = {};
    profileData.categorical_attributes.forEach((attribute) => {
        categoricalScales[attribute] = buildCategoricalColorScale(profileData, attribute);
    });

    const wrapper = document.createElement("div");
    wrapper.className = "husformer-a3-table-wrapper";

    const table = document.createElement("table");
    table.className = "husformer-a3-lineup-table";

    const thead = document.createElement("thead");
    thead.appendChild(buildHeaderRow(profileData));
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    profileData.records.forEach((record) => {
        const trialCount = participantTrialCounts.get(record.Participant_id) ?? 0;

        tbody.appendChild(
            buildParticipantRow({
                profileData,
                categoricalScales,
                record,
                trialCount,
                onRemoveParticipant,
            })
        );
    });

    table.appendChild(tbody);
    wrapper.appendChild(table);
    container.appendChild(wrapper);
}
