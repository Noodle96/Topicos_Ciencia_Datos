import {
    fetchH2Relationships,
    fetchH2TimeseriesPair,
    fetchEmotionSpace,
    fetchH2ParticipantProfiles,
} from "./api.js";

import {
    renderH2CorrelationMatrix,
} from "./charts/h2_correlation_matrix_chart.js";

import {
    renderH2TimeseriesPairChart,
} from "./charts/h2_timeseries_pair_chart.js";

import {
    renderH2ParticipantProfiles,
} from "./charts/h2_participant_profile_chart.js";

import {
    renderH2EEGSpatialChart,
} from "./charts/h2_eeg_spatial_chart.js";


const CHANNEL_GROUPS = {
    EEG: [
        "Fp1", "AF3", "F7", "F3", "FC1", "FC5", "T7", "C3",
        "CP1", "CP5", "P7", "P3", "Pz", "PO3", "O1", "Oz",
        "O2", "PO4", "P4", "P8", "CP6", "CP2", "C4", "T8",
        "FC6", "FC2", "F4", "F8", "AF4", "Fp2", "Fz", "Cz",
    ],
    EXG: [
        "EXG1", "EXG2", "EXG3", "EXG4",
        "EXG5", "EXG6", "EXG7", "EXG8",
    ],
    PERIPHERAL: [
        "GSR1", "Resp", "Plet", "Temp",
    ],
};

let selectedParticipants = [];
let currentMatrixData = null;


// function renderTarea1ChannelSelector() {
//     const container = document.getElementById(
//         "tarea1-channel-selector-container"
//     );

//     container.innerHTML = "";

//     tarea1ChannelGroups.forEach((group) => {
//         const groupWrapper = document.createElement("div");
//         groupWrapper.className = "tarea1-channel-group";

//         const groupTitle = document.createElement("span");
//         groupTitle.className = "tarea1-channel-group-title";
//         groupTitle.textContent = group.name;

//         groupWrapper.appendChild(groupTitle);

//         group.channels.forEach((channel) => {
//             const label = document.createElement("label");
//             label.className = "tarea1-channel-checkbox-item";

//             const checkbox = document.createElement("input");
//             checkbox.type = "checkbox";
//             checkbox.checked = activeTarea1Channels.includes(channel);

//             checkbox.addEventListener("change", async () => {
//                 if (checkbox.checked) {
//                     if (!activeTarea1Channels.includes(channel)) {
//                         activeTarea1Channels.push(channel);
//                     }
//                 } else {
//                     activeTarea1Channels = activeTarea1Channels.filter(
//                         (activeChannel) => activeChannel !== channel
//                     );
//                 }

//                 if (selectedPoint) {
//                     await loadAndRenderTarea1Signals(selectedPoint);
//                 }

//                 renderTarea1ChannelSelector();
//             });

//             const text = document.createElement("span");
//             text.textContent = channel;
//             text.style.color = CHANNEL_COLORS[channel] ?? "#111827";
//             text.style.fontWeight = "700";

//             label.appendChild(checkbox);
//             label.appendChild(text);
//             groupWrapper.appendChild(label);
//         });

//         container.appendChild(groupWrapper);
//     });
// }

function getSelectedRadioValue(name) {
    const selectedInput = document.querySelector(
        `input[name="${name}"]:checked`
    );

    return selectedInput.value;
}


function getH2SelectedExperiment() {
    return Number(
        document.getElementById("h2-experiment-select").value
    );
}


function getH2RowGroup() {
    return getSelectedRadioValue("h2-row-group");
}


function getH2ReferenceGroup() {
    return getSelectedRadioValue("h2-reference-group");
}


function getH2ReferenceChannel() {
    return document.getElementById(
        "h2-reference-channel-select"
    ).value;
}


function updateReferenceChannelOptions() {
    const referenceGroup = getH2ReferenceGroup();
    const select = document.getElementById(
        "h2-reference-channel-select"
    );

    select.innerHTML = "";

    CHANNEL_GROUPS[referenceGroup].forEach((channel) => {
        const option = document.createElement("option");
        option.value = channel;
        option.textContent = channel;

        select.appendChild(option);
    });
}


async function renderH2ExperimentInfo(experiment) {
    const container = document.getElementById(
        "h2-experiment-info"
    );

    try {
        const data = await fetchEmotionSpace({
            xVariable: "Valence",
            yVariable: "Arousal",
            participant: "all",
            experiment,
        });

        const firstPoint = data.points?.[0];

        if (!firstPoint) {
            container.innerHTML = "No metadata available.";
            return;
        }

        container.innerHTML = `
            <strong>Experiment:</strong> ${experiment}<br>
            <strong>Tag:</strong> ${firstPoint.Lastfm_tag ?? "N/A"}<br>
            <strong>Artist:</strong> ${firstPoint.Artist ?? "N/A"}<br>
            <strong>Title:</strong> ${firstPoint.Title ?? "N/A"}
        `;
    } catch (error) {
        container.innerHTML = "Could not load experiment metadata.";
    }
}

async function updateParticipantProfiles() {
    if (selectedParticipants.length === 0) {
        document.getElementById("h2-participant-profiles").innerHTML = `
            Select one or more participants from the matrix.
        `;
        return;
    }

    const profileData = await fetchH2ParticipantProfiles(
        selectedParticipants
    );

    renderH2ParticipantProfiles({
        containerId: "h2-participant-profiles",
        profileData,
    });
}


async function handleParticipantToggle(participantLabel) {
    if (selectedParticipants.includes(participantLabel)) {
        selectedParticipants = selectedParticipants.filter(
            (participant) => participant !== participantLabel
        );
    } else {
        selectedParticipants.push(participantLabel);
    }

    if (currentMatrixData) {
        renderH2CorrelationMatrix({
            containerSelector: "#h2-correlation-matrix",
            data: currentMatrixData,
            selectedParticipants,
            onCellClick: handleH2CellClick,
            onParticipantToggle: handleParticipantToggle,
        });
    }

    await updateParticipantProfiles();
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
        <strong>Participant:</strong> ${cell.participant_label}<br>
        <strong>Group Y:</strong> ${cell.row_group}<br>
        <strong>Channel Y:</strong> ${cell.row_channel}<br>
        <strong>Reference Group X:</strong> ${cell.reference_group}<br>
        <strong>Reference Channel X:</strong> ${cell.reference_channel}<br>
        <strong>Pearson:</strong> ${correlationText}
    `;

    const experiment = getH2SelectedExperiment();

    const pairData = await fetchH2TimeseriesPair({
        participant: cell.participant_id,
        experiment,
        channelA: cell.row_channel,
        channelB: cell.reference_channel,
    });

    renderH2TimeseriesPairChart({
        containerId: "h2-timeseries-pair",
        pairData,
    });
    renderH2EEGSpatialChart({
        containerId: "h2-eeg-spatial-explorer",
        matrixData: currentMatrixData,
        selectedCell: cell,
    });
}


export async function updateH2Relationships() {
    const experiment = getH2SelectedExperiment();
    const rowGroup = getH2RowGroup();
    const referenceGroup = getH2ReferenceGroup();
    const referenceChannel = getH2ReferenceChannel();

    await renderH2ExperimentInfo(experiment);

    const data = await fetchH2Relationships({
        experiment,
        rowGroup,
        referenceGroup,
        referenceChannel,
    });
    currentMatrixData = data;
    selectedParticipants = [];

    renderH2CorrelationMatrix({
        containerSelector: "#h2-correlation-matrix",
        data,
        selectedParticipants,
        onCellClick: handleH2CellClick,
        onParticipantToggle: handleParticipantToggle,
    });

    document.getElementById("h2-selected-relation-text").innerHTML = `
        Select a cell from the matrix.
    `;

    document.getElementById("h2-timeseries-pair").innerHTML = `
        Select a relation to load the temporal explorer.
    `;

    document.getElementById("h2-participant-profiles").innerHTML = `
        Select one or more participants from the matrix.
    `;
    document.getElementById("h2-eeg-spatial-explorer").innerHTML = `
        Select a matrix cell to inspect its EEG spatial pattern.
    `;
}

// here
function initializeH2BottomTabs() {
    const profilesButton = document.getElementById(
        "h2-profiles-tab-button"
    );

    const spatialButton = document.getElementById(
        "h2-spatial-tab-button"
    );

    const profilesContent = document.getElementById(
        "h2-profiles-tab-content"
    );

    const spatialContent = document.getElementById(
        "h2-spatial-tab-content"
    );

    profilesButton.addEventListener("click", () => {
        profilesButton.classList.add("active");
        spatialButton.classList.remove("active");

        profilesContent.classList.add("active");
        profilesContent.classList.remove("hidden");

        spatialContent.classList.add("hidden");
        spatialContent.classList.remove("active");
    });

    spatialButton.addEventListener("click", () => {
        spatialButton.classList.add("active");
        profilesButton.classList.remove("active");

        spatialContent.classList.add("active");
        spatialContent.classList.remove("hidden");

        profilesContent.classList.add("hidden");
        profilesContent.classList.remove("active");
    });
}

export function initializeH2View() {
    const updateButton = document.getElementById(
        "h2-update-button"
    );

    const referenceGroupInputs = document.querySelectorAll(
        `input[name="h2-reference-group"]`
    );

    referenceGroupInputs.forEach((input) => {
        input.addEventListener("change", updateReferenceChannelOptions);
    });

    updateButton.addEventListener(
        "click",
        updateH2Relationships
    );
    initializeH2BottomTabs();
    updateReferenceChannelOptions();
    updateH2Relationships();
}