import { VALENCE_COLOR_SCALE } from "./husformer_a1_chart.js";

/**
 * Renderiza el sub-panel A3 (comparación explícita de trials seleccionados
 * en A1). Formaliza T2 ("comparar trials/participantes en el espacio de
 * representación fusionada") como una operación explícita -- ver
 * justificación de A3 en 05_diseno_visual.tex.
 *
 * No hace ninguna llamada al backend: todos los datos de los trials
 * seleccionados ya están en memoria (vinieron con la proyección de A1), así
 * que A3 solo lee `selectedTrials` (mismo Map que usa A1) y lo tabula. Es
 * una tabla HTML simple, no un chart D3 -- para un panel de 1/9 de pantalla
 * con hasta ~1280 trials seleccionables, una tabla compacta compara mejor
 * que un gráfico, y no tiene el problema de "tamaño 0 mientras está oculto"
 * que sí tienen los charts SVG (un <table> no necesita medir su
 * contenedor con JS, se reacomoda solo vía CSS normal).
 *
 * El chip de color de cada fila reutiliza VALENCE_COLOR_SCALE de
 * husformer_a1_chart.js -- mismo color que ese mismo trial tiene en A1,
 * para que el "resaltado vinculado" entre A1 y A3 sea visualmente
 * coherente, no solo funcional.
 */
export function renderHusformerA3Panel({
    containerId,
    selectedTrials,
    onRemoveTrial,
}) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    const selection = selectedTrials ?? new Map();

    if (selection.size === 0) {
        const empty = document.createElement("div");
        empty.className = "husformer-a3-empty";
        empty.textContent = "Selecciona uno o más trials en A1 para compararlos aquí.";
        container.appendChild(empty);
        return;
    }

    const wrapper = document.createElement("div");
    wrapper.className = "husformer-a3-table-wrapper";

    const table = document.createElement("table");
    table.className = "husformer-a3-table";

    const thead = document.createElement("thead");
    thead.innerHTML = `
        <tr>
            <th></th>
            <th>Part.</th>
            <th>Trial</th>
            <th>Val</th>
            <th>Aro</th>
            <th>Dom</th>
            <th>Lik</th>
            <th></th>
        </tr>
    `;
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    // Array.from(selection.values()) preserva el orden de inserción del Map
    // -- los trials aparecen en el orden en que se clickearon, no
    // reordenados por participante/trial/valencia.
    Array.from(selection.values()).forEach((point) => {
        const row = document.createElement("tr");

        const colorCell = document.createElement("td");
        const colorChip = document.createElement("span");
        colorChip.className = "husformer-a3-color-chip";
        colorChip.style.background = point.Valence === null
            ? "#9ca3af"
            : VALENCE_COLOR_SCALE(Number(point.Valence));
        colorCell.appendChild(colorChip);
        row.appendChild(colorCell);

        const participantCell = document.createElement("td");
        participantCell.textContent = point.Participant_label;
        row.appendChild(participantCell);

        const trialCell = document.createElement("td");
        trialCell.textContent = point.Trial;
        row.appendChild(trialCell);

        const valenceCell = document.createElement("td");
        valenceCell.textContent = point.Valence ?? "N/A";
        row.appendChild(valenceCell);

        const arousalCell = document.createElement("td");
        arousalCell.textContent = point.Arousal ?? "N/A";
        row.appendChild(arousalCell);

        const dominanceCell = document.createElement("td");
        dominanceCell.textContent = point.Dominance ?? "N/A";
        row.appendChild(dominanceCell);

        const likingCell = document.createElement("td");
        likingCell.textContent = point.Liking ?? "N/A";
        row.appendChild(likingCell);

        const removeCell = document.createElement("td");
        const removeButton = document.createElement("button");
        removeButton.className = "husformer-a3-remove-btn";
        removeButton.type = "button";
        removeButton.textContent = "×";
        removeButton.setAttribute(
            "aria-label",
            `Quitar ${point.Participant_label} / Trial ${point.Trial} de la comparación`
        );
        removeButton.addEventListener("click", () => {
            if (onRemoveTrial) {
                onRemoveTrial(point);
            }
        });
        removeCell.appendChild(removeButton);
        row.appendChild(removeCell);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    wrapper.appendChild(table);
    container.appendChild(wrapper);
}
