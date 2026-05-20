import { fetchH2Relationships, fetchH2TimeseriesPair, fetchH2LocalRelationship, } from "./api.js";

import {
    renderH2CorrelationMatrix,
} from "./charts/h2_correlation_matrix_chart.js";

import {
    renderH2TimeseriesPairChart,
} from "./charts/h2_timeseries_pair_chart.js";


function getH2SelectedParticipant() {
    return Number(
        document.getElementById("h2-participant-select").value
    );
}


function getH2SelectedExperiment() {
    return Number(
        document.getElementById("h2-experiment-select").value
    );
}

function renderH2LocalRelationship(localData) {
    const container = document.getElementById(
        "h2-local-relationship"
    );

    const globalCorrelation =
        localData.global_correlation === null
            ? "N/A"
            : localData.global_correlation.toFixed(4);

    const localCorrelation =
        localData.local_correlation === null
            ? "N/A"
            : localData.local_correlation.toFixed(4);

    container.innerHTML = `
        <p><strong>EEG:</strong> ${localData.eeg_channel}</p>
        <p><strong>Peripheral:</strong> ${localData.peripheral_channel}</p>
        <p><strong>Window:</strong> ${localData.start_sec.toFixed(2)}s – ${localData.end_sec.toFixed(2)}s</p>
        <p><strong>Samples:</strong> ${localData.sample_count}</p>
        <p><strong>Global Pearson:</strong> ${globalCorrelation}</p>
        <p><strong>Local Pearson:</strong> ${localCorrelation}</p>
    `;
}

async function handleH2CellClick(cell) {
    const relationContainer = document.getElementById(
        "h2-selected-relation-text"
    );

    const correlationText =
        cell.correlation === null
            ? "N/A"
            : cell.correlation.toFixed(4);

    relationContainer.innerHTML = `
        <strong>EEG:</strong> ${cell.eeg_channel}<br>
        <strong>Peripheral:</strong> ${cell.peripheral_channel}<br>
        <strong>Pearson:</strong> ${correlationText}
    `;

    const participant = getH2SelectedParticipant();
    const experiment = getH2SelectedExperiment();

    const pairData = await fetchH2TimeseriesPair({
        participant,
        experiment,
        eeg: cell.eeg_channel,
        peripheral: cell.peripheral_channel,
    });

        renderH2TimeseriesPairChart({
            containerId: "h2-timeseries-pair",
            pairData,
            onBrushEnd: async ({ startSec, endSec }) => {
                const localData = await fetchH2LocalRelationship({
                    participant,
                    experiment,
                    eeg: cell.eeg_channel,
                    peripheral: cell.peripheral_channel,
                    startSec,
                    endSec,
                });

                renderH2LocalRelationship(localData);
            },
        });

    document.getElementById("h2-local-relationship").innerHTML = `
        Select a temporal window to calculate local correlation.
    `;
}


export async function updateH2Relationships() {
    const participant = getH2SelectedParticipant();
    const experiment = getH2SelectedExperiment();

    const data = await fetchH2Relationships(
        participant,
        experiment
    );

    renderH2CorrelationMatrix({
        containerSelector: "#h2-correlation-matrix",
        data,
        onCellClick: handleH2CellClick,
    });
}


export function initializeH2View() {
    const updateButton = document.getElementById(
        "h2-update-button"
    );

    updateButton.addEventListener(
        "click",
        updateH2Relationships
    );

    updateH2Relationships();
}