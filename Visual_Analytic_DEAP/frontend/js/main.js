import { fetchEmotionSpace, fetchTrialSignals, fetchH2Relationships } from "./api.js";


import {
    renderEmotionSpaceChart,
} from "./charts/emotion_space_chart.js";

import {
    renderSignalTimeseriesChart,
    CHANNEL_COLORS,
} from "./charts/signal_timeseries_chart.js";

import {
    renderSummaryMetricsChart,
} from "./charts/summary_metrics_chart.js";

import { renderH2CorrelationMatrix } from "./charts/h2_correlation_matrix_chart.js";

let selectedTrial = null;
let normalizeSignals = false;

let activeChannels = [
    "Fp1",
    "Fp2",
    "Fz",
    "EXG1",
    "EXG5",
    "GSR1",
    "Resp",
];

const channelGroups = [
    {
        name: "EEG izquierdo",
        channels: [
            "Fp1", "AF3", "F7", "F3", "FC1", "FC5", "T7",
            "C3", "CP1", "CP5", "P7", "P3", "PO3", "O1",
        ],
    },
    {
        name: "EEG derecho",
        channels: [
            "Fp2", "AF4", "F8", "F4", "FC2", "FC6", "T8",
            "C4", "CP2", "CP6", "P8", "P4", "PO4", "O2",
        ],
    },
    {
        name: "EEG línea media",
        channels: [
            "Fz", "Cz", "Pz", "Oz",
        ],
    },
    {
        name: "EOG",
        channels: [
            "EXG1", "EXG2", "EXG3", "EXG4",
        ],
    },
    {
        name: "EMG",
        channels: [
            "EXG5", "EXG6", "EXG7", "EXG8",
        ],
    },
    {
        name: "Periféricas",
        channels: [
            "GSR1", "Resp", "Plet", "Temp",
        ],
    },
];

/**
 * Renderiza el selector de canales agrupado por modalidad/anatomía.
 *
 * Cada grupo aparece en la zona superior de Signal Exploration View.
 * Si no hay espacio horizontal, los grupos pasan automáticamente
 * a una nueva fila mediante flex-wrap.
 */
function renderChannelSelector() {
    const container = document.getElementById("channel-selector-container");

    container.innerHTML = "";

    channelGroups.forEach((group) => {
        const groupWrapper = document.createElement("div");
        groupWrapper.className = "channel-group";

        const groupTitle = document.createElement("div");
        groupTitle.className = "channel-group-title";
        groupTitle.textContent = group.name;

        const groupChannels = document.createElement("div");
        groupChannels.className = "channel-group-items";

        group.channels.forEach((channel) => {
            const wrapper = document.createElement("label");
            wrapper.className = "channel-checkbox-item";

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.checked = activeChannels.includes(channel);

            checkbox.addEventListener("change", async () => {
                if (checkbox.checked) {
                    if (!activeChannels.includes(channel)) {
                        activeChannels.push(channel);
                    }
                } else {
                    activeChannels = activeChannels.filter(
                        (activeChannel) => activeChannel !== channel
                    );
                }

                if (selectedTrial) {
                    await loadAndRenderTrialSignals(selectedTrial);
                }

                renderChannelSelector();
            });

            const label = document.createElement("span");
            label.className = "channel-label";
            label.style.color = CHANNEL_COLORS[channel] ?? "#111827";
            label.textContent = channel;

            wrapper.appendChild(checkbox);
            wrapper.appendChild(label);
            groupChannels.appendChild(wrapper);
        });

        groupWrapper.appendChild(groupTitle);
        groupWrapper.appendChild(groupChannels);

        container.appendChild(groupWrapper);
    });
}

async function loadAndRenderTrialSignals(trialData) {
    const signalContainer = document.getElementById("signal-tracks-container");
    signalContainer.classList.toggle(
        "normalized-mode",
        normalizeSignals
    );

    signalContainer.classList.toggle(
        "raw-mode",
        !normalizeSignals
    );
    const signalData = await fetchTrialSignals({
        participant: trialData.Participant_id,
        trial: trialData.Trial,
        channels: activeChannels,
    });

    renderSignalTimeseriesChart({
        containerId: "signal-tracks-container",
        signalData,
        activeChannels,
        normalizeSignals,
    });

    renderSummaryMetricsChart({
        containerId: "summary-metrics-container",
        signalData,
        activeChannels,
    });
}

/**
 * Renderiza la información detallada del punto seleccionado.
 *
 * En esta tarjeta no se muestra thumbnail para ahorrar espacio,
 * pero sí se muestran los metadatos del estímulo:
 * Lastfm_tag, Artist y Title.
 */
function renderSelectedTrialInfo(trialData) {
    const container = document.getElementById(
        "selected-trial-info"
    );

    container.innerHTML = `
        <p><strong>Participant:</strong> S${String(trialData.Participant_id).padStart(2, "0")}</p>
        <p><strong>Experiment:</strong> ${trialData.Experiment_id}</p>
        <p><strong>Trial:</strong> ${trialData.Trial}</p>
        <p><strong>Lastfm tag:</strong> ${trialData.Lastfm_tag ?? "N/A"}</p>
        <p><strong>Artist:</strong> ${trialData.Artist ?? "N/A"}</p>
        <p><strong>Title:</strong> ${trialData.Title ?? "N/A"}</p>
        <p><strong>Valence:</strong> ${trialData.Valence}</p>
        <p><strong>Arousal:</strong> ${trialData.Arousal}</p>
        <p><strong>Dominance:</strong> ${trialData.Dominance}</p>
        <p><strong>Liking:</strong> ${trialData.Liking}</p>
        <p><strong>Familiarity:</strong> ${trialData.Familiarity ?? "N/A"}</p>
    `;

    selectedTrial = trialData;

    loadAndRenderTrialSignals(trialData);
}


async function updateEmotionSpace() {
    const participant =
        document.getElementById("participant-select").value;

    const experiment =
        document.getElementById("experiment-select").value;

    const xVariable =
        document.getElementById("x-axis-select").value;

    const yVariable =
        document.getElementById("y-axis-select").value;

    const data = await fetchEmotionSpace({
        xVariable,
        yVariable,
        participant,
        experiment,
    });

    // console.log("Emotion Space response:", data);

    renderEmotionSpaceChart({
        containerId: "emotion-space-chart",
        points: data.points,
        xVariable,
        yVariable,
        onPointClick: renderSelectedTrialInfo,
    });
}


function initApp() {
    document
        .getElementById("update-chart-button")
        .addEventListener("click", updateEmotionSpace);

    updateEmotionSpace();
    renderChannelSelector();
    setupNormalizeToggle();
}

function setupNormalizeToggle() {
    const checkbox = document.getElementById(
        "normalize-toggle"
    );

    checkbox.addEventListener("change", async () => {
        normalizeSignals = checkbox.checked;

        if (selectedTrial) {
            await loadAndRenderTrialSignals(
                selectedTrial
            );
        }
    });
}


initApp();