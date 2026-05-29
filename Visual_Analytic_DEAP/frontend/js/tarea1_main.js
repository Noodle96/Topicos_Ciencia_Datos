import {
    fetchTarea1Projection,
    fetchH2ParticipantProfiles,
} from "./api.js";

import {
    renderTarea1LatentSpaceChart,
} from "./charts/tarea1_latent_space_chart.js";

import {
    renderH2ParticipantProfiles,
} from "./charts/h2_participant_profile_chart.js";


import {
    fetchTarea1TrialSignals,
} from "./api.js";

import {
    renderTarea1TemporalSignalChart,
    resetTarea1SignalZoom,
} from "./charts/tarea1_temporal_signal_chart.js";

import {
    CHANNEL_COLORS,
} from "./charts/signal_timeseries_chart.js";

let normalizeTarea1Signals = false;


let activeTarea1Channels = [
    "Fp1",
    "Fp2",
    "Fz",
    "EXG1",
    "EXG5",
    "GSR1",
    "Resp",
];

const tarea1ChannelGroups = [
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

let currentProjectionData = null;
let selectedParticipants = [];
let selectedPoint = null;


function renderTarea1ChannelSelector() {
    const container = document.getElementById(
        "tarea1-channel-selector-container"
    );

    container.innerHTML = "";

    tarea1ChannelGroups.forEach((group) => {
        const groupWrapper = document.createElement("div");
        groupWrapper.className = "tarea1-channel-group";

        const groupTitle = document.createElement("span");
        groupTitle.className = "tarea1-channel-group-title";
        groupTitle.textContent = group.name;

        groupWrapper.appendChild(groupTitle);

        group.channels.forEach((channel) => {
            const label = document.createElement("label");
            label.className = "tarea1-channel-checkbox-item";

            const checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.checked = activeTarea1Channels.includes(channel);

            checkbox.addEventListener("change", async () => {
                if (checkbox.checked) {
                    if (!activeTarea1Channels.includes(channel)) {
                        activeTarea1Channels.push(channel);
                    }
                } else {
                    activeTarea1Channels = activeTarea1Channels.filter(
                        (activeChannel) => activeChannel !== channel
                    );
                }

                if (selectedPoint) {
                    await loadAndRenderTarea1Signals(selectedPoint);
                }

                renderTarea1ChannelSelector();
            });

            const text = document.createElement("span");
            text.textContent = channel;
            text.style.color = CHANNEL_COLORS[channel] ?? "#111827";
            text.style.fontWeight = "700";

            label.appendChild(checkbox);
            label.appendChild(text);
            groupWrapper.appendChild(label);
        });

        container.appendChild(groupWrapper);
    });
}

function getTarea1ProjectionMethod() {
    return document.getElementById("tarea1-projection-select").value;
}


function getTarea1FilterMode() {
    return document.getElementById("tarea1-filter-mode-select").value;
}


function getTarea1SelectedParticipant() {
    return Number(document.getElementById("tarea1-participant-select").value);
}


function getTarea1SelectedExperiment() {
    return Number(document.getElementById("tarea1-experiment-select").value);
}


function renderSelectedTrialCard(point) {
    const container = document.getElementById("tarea1-selected-trial-info");

    container.innerHTML = `
        <strong>Selected Trial</strong><br>
        Participant: ${point.Participant_label}<br>
        Trial: ${point.Trial}<br>
        Experiment: ${point.Experiment_id}<br>
        Valence: ${point.Valence ?? "N/A"} |
        Arousal: ${point.Arousal ?? "N/A"} |
        Dominance: ${point.Dominance ?? "N/A"} |
        Liking: ${point.Liking ?? "N/A"}
    `;
}


async function updateParticipantProfilePanel() {
    const container = document.getElementById("tarea1-participant-profile");

    if (selectedParticipants.length === 0) {
        container.innerHTML = `
            Select one or more points to compare participant profiles.
        `;
        return;
    }

    const profileData = await fetchH2ParticipantProfiles(
        selectedParticipants
    );

    renderH2ParticipantProfiles({
        containerId: "tarea1-participant-profile",
        profileData,
    });
}


function toggleSelectedParticipant(participantLabel) {
    if (selectedParticipants.includes(participantLabel)) {
        selectedParticipants = selectedParticipants.filter(
            (participant) => participant !== participantLabel
        );
    } else {
        selectedParticipants.push(participantLabel);
    }
}


async function handlePointClick(point) {
    const filterMode = getTarea1FilterMode();

    selectedPoint = point;

    renderSelectedTrialCard(point);

    if (filterMode === "experiment") {
        toggleSelectedParticipant(point.Participant_label);
    } else {
        selectedParticipants = [point.Participant_label];
    }

    await updateParticipantProfilePanel();

    renderCurrentProjection();

    await loadAndRenderTarea1Signals(point);
}


function renderCurrentProjection() {
    if (!currentProjectionData) {
        return;
    }

    renderTarea1LatentSpaceChart({
        containerId: "tarea1-latent-space-chart",
        points: currentProjectionData.points,
        projectionMethod: getTarea1ProjectionMethod(),
        filterMode: getTarea1FilterMode(),
        selectedParticipant: getTarea1SelectedParticipant(),
        selectedExperiment: getTarea1SelectedExperiment(),
        selectedParticipants,
        selectedPoint,
        onPointClick: handlePointClick,
    });
}


async function updateTarea1View() {
    const projectionMethod = getTarea1ProjectionMethod();

    const data = await fetchTarea1Projection({
        method: projectionMethod,
    });

    currentProjectionData = data;

    selectedParticipants = [];
    selectedPoint = null;

    document.getElementById("tarea1-participant-profile").innerHTML = `
        Select one or more points to compare participant profiles.
    `;

    document.getElementById("tarea1-selected-trial-info").innerHTML = `
        Select a point to load trial signals.
    `;

    document.getElementById("tarea1-temporal-signal-container").innerHTML = `
        Temporal signal view will be loaded here.
    `;

    renderCurrentProjection();
}


export function initializeTarea1View() {
    document
        .getElementById("tarea1-update-button")
        .addEventListener("click", updateTarea1View);

    document
        .getElementById("tarea1-projection-select")
        .addEventListener("change", updateTarea1View);

    document
        .getElementById("tarea1-filter-mode-select")
        .addEventListener("change", updateTarea1View);

    document
        .getElementById("tarea1-participant-select")
        .addEventListener("change", updateTarea1View);

    document
        .getElementById("tarea1-experiment-select")
        .addEventListener("change", updateTarea1View);
    document
        .getElementById("tarea1-normalize-toggle")
        .addEventListener("change", async (event) => {
            normalizeTarea1Signals = event.target.checked;

            if (selectedPoint) {
                await loadAndRenderTarea1Signals(selectedPoint);
            }
        });
    document
        .getElementById("tarea1-reset-zoom-button")
        .addEventListener("click", resetTarea1SignalZoom);

    renderTarea1ChannelSelector();
    updateTarea1View();
}


function renderSignalInspector({ channel, channelType, statistics, mode }) {
    const container = document.getElementById(
        "tarea1-signal-inspector-content"
    );

    if (!statistics) {
        container.innerHTML = "No statistics available.";
        return;
    }

    const channelColor = CHANNEL_COLORS[channel] ?? "#111827";

    container.innerHTML = `
        <p><strong>Channel:</strong> <span style="color:${channelColor}; font-weight:700;">${channel}</span></p>
        <p><strong>Type:</strong> ${channelType ?? "N/A"}</p>
        <p><strong>Mode:</strong> ${mode}</p>
        <hr>
        <p><strong>Mean:</strong> <span style="color:${channelColor}; font-weight:700;">${statistics.mean?.toExponential(4) ?? "N/A"}</span></p>
        <p><strong>Std:</strong> <span style="color:${channelColor}; font-weight:700;">${statistics.std?.toExponential(4) ?? "N/A"}</span></p>
        <p><strong>Min:</strong> <span style="color:${channelColor}; font-weight:700;">${statistics.min?.toExponential(4) ?? "N/A"}</span></p>
        <p><strong>Max:</strong> <span style="color:${channelColor}; font-weight:700;">${statistics.max?.toExponential(4) ?? "N/A"}</span></p>
        <p><strong>RMS:</strong> <span style="color:${channelColor}; font-weight:700;">${statistics.rms?.toExponential(4) ?? "N/A"}</span></p>
        <p><strong>Peak-to-peak:</strong> <span style="color:${channelColor}; font-weight:700;">${statistics.peak_to_peak?.toExponential(4) ?? "N/A"}</span></p>
    `;
}

async function loadAndRenderTarea1Signals(point) {
    const signalData = await fetchTarea1TrialSignals({
        participant: point.Participant_id,
        trial: point.Trial,
        channels: activeTarea1Channels,
    });

    const signalContainer = document.getElementById(
        "tarea1-temporal-signal-container"
    );

    signalContainer.classList.toggle(
        "normalized-mode",
        normalizeTarea1Signals
    );

    signalContainer.classList.toggle(
        "raw-mode",
        !normalizeTarea1Signals
    );

    renderTarea1TemporalSignalChart({
        containerId: "tarea1-temporal-signal-container",
        signalData,
        activeChannels: activeTarea1Channels,
        normalizeSignals: normalizeTarea1Signals,
        onSignalHover: renderSignalInspector,
    });
}