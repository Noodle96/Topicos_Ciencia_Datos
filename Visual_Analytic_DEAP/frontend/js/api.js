const API_BASE_URL = "http://127.0.0.1:5000/api";

/**
 * Consulta el estado del backend Flask.
 */
export async function fetchHealthStatus() {
    const response = await fetch(`${API_BASE_URL}/health`);

    if (!response.ok) {
        throw new Error("No se pudo conectar con el backend");
    }

    return await response.json();
}

/**
 * Obtiene los puntos del espacio emocional filtrados
 * por participante y experimento emocional.
 */
export async function fetchEmotionSpace({
    xVariable,
    yVariable,
    participant,
    experiment,
}) {
    const response = await fetch(
        `${API_BASE_URL}/emotion-space?x=${xVariable}&y=${yVariable}&participant=${participant}&experiment=${experiment}`
    );

    if (!response.ok) {
        throw new Error("No se pudo obtener emotion-space");
    }

    return await response.json();
}

/**
 * Obtiene señales reales del .bdf para un trial específico.
 */
export async function fetchTrialSignals({
    participant,
    trial,
    channels,
}) {
    const channelsQuery = channels.join(",");

    const response = await fetch(
        `http://127.0.0.1:5000/api/trial-signals?participant=${participant}&trial=${trial}&channels=${channelsQuery}`
    );

    if (!response.ok) {
        throw new Error("No se pudieron obtener las señales del trial");
    }

    return await response.json();
}




// TO H2
/**
 * Obtiene la matriz H2 por experimento.
 *
 * Filas:
 * - canales del grupo Y.
 *
 * Columnas:
 * - participantes S01...S32.
 *
 * Celda:
 * - correlación entre el canal de fila y el canal de referencia.
 */
export async function fetchH2Relationships({
    experiment,
    rowGroup,
    referenceGroup,
    referenceChannel,
}) {
    const response = await fetch(
        `${API_BASE_URL}/h2/relationships?experiment=${experiment}&row_group=${rowGroup}&reference_group=${referenceGroup}&reference_channel=${referenceChannel}`
    );

    if (!response.ok) {
        throw new Error("Error loading H2 relationships");
    }

    return await response.json();
}

/**
 * Obtiene un par temporal sincronizado canal A ↔ canal B
 * para un participante y experimento específico.
 */
export async function fetchH2TimeseriesPair({
    participant,
    experiment,
    channelA,
    channelB,
}) {
    const response = await fetch(
        `${API_BASE_URL}/h2/timeseries-pair?participant=${participant}&experiment=${experiment}&channel_a=${channelA}&channel_b=${channelB}`
    );

    if (!response.ok) {
        throw new Error("Error loading H2 timeseries pair");
    }

    return await response.json();
}

/**
 * Calcula la correlación local H2 dentro de una ventana temporal
 * seleccionada durante la fase During.
 */
export async function fetchH2LocalRelationship({
    participant,
    experiment,
    eeg,
    peripheral,
    startSec,
    endSec,
}) {
    const response = await fetch(
        `${API_BASE_URL}/h2/local-relationship?participant=${participant}&experiment=${experiment}&eeg=${eeg}&peripheral=${peripheral}&start_sec=${startSec}&end_sec=${endSec}`
    );

    if (!response.ok) {
        throw new Error("Error loading H2 local relationship");
    }

    return await response.json();
}


/**
 * Obtiene comparación de perfiles humanos para participantes seleccionados.
 */
export async function fetchH2ParticipantProfiles(participants) {
    const participantsQuery = participants.join(",");

    const response = await fetch(
        `${API_BASE_URL}/h2/participant-profiles?participants=${participantsQuery}`
    );

    if (!response.ok) {
        throw new Error("Error loading H2 participant profiles");
    }

    return await response.json();
}

export async function fetchTarea1Projection({ method }) {
    const response = await fetch(
        `${API_BASE_URL}/tarea1/projection?method=${method}`
    );

    if (!response.ok) {
        throw new Error("Error loading Tarea 1 projection");
    }

    return await response.json();
}

// TO HUSFORMER (Vista A/B/C)
/**
 * Obtiene los puntos 2D de la Vista A, sub-panel A1: last_hs de Husformer
 * agregado por trial (mean-pooling) y proyectado con pca/umap/tsne.
 */
export async function fetchHusformerTrialProjection({ method }) {
    const response = await fetch(
        `${API_BASE_URL}/husformer/trial-projection?method=${method}`
    );

    if (!response.ok) {
        throw new Error("Error loading Husformer trial projection");
    }

    return await response.json();
}

/**
 * Obtiene la etiqueta de cluster por trial (Vista A, sub-panel A2),
 * calculada al vuelo en el backend (KMeans o HDBSCAN) sobre el vector de
 * 40-dim estandarizado de last_hs -- NO sobre las coordenadas 2D.
 *
 * method: "kmeans" (paramValue = k, uno de 3/4/6/12) o
 * "hdbscan" (paramValue = min_cluster_size, uno de 5/10/20/50).
 */
export async function fetchHusformerTrialClusters({ method, paramValue }) {
    const response = await fetch(
        `${API_BASE_URL}/husformer/trial-clusters?method=${method}&param_value=${paramValue}`
    );

    if (!response.ok) {
        throw new Error("Error loading Husformer trial clusters");
    }

    return await response.json();
}

/**
 * Obtiene la serie temporal de dominancia de modalidad para un trial
 * (Vista B, B1/B2): un peso por modalidad (5) por cada ventana de 1s del
 * trial, calculado al vuelo en el backend a partir de attn_final_summary.
 */
export async function fetchHusformerTrialAttention({ participantId, trial }) {
    const response = await fetch(
        `${API_BASE_URL}/husformer/trial-attention?participant_id=${participantId}&trial=${trial}`
    );

    if (!response.ok) {
        throw new Error("Error loading Husformer trial attention");
    }

    return await response.json();
}

/**
 * Obtiene la matriz 5x5 cruda de atención cross-modal (attn_cross_summary)
 * de UNA ventana puntual (Vista C, C1) -- distinta de attn_final_summary
 * (B1/B2): ver husformer_attention_service.py.
 */
export async function fetchHusformerWindowCrossAttention({ participantId, trial, windowIndex }) {
    const response = await fetch(
        `${API_BASE_URL}/husformer/window-cross-attention`
        + `?participant_id=${participantId}&trial=${trial}&window_index=${windowIndex}`
    );

    if (!response.ok) {
        throw new Error("Error loading Husformer window cross-attention");
    }

    return await response.json();
}

export async function fetchTarea1TrialSignals({
    participant,
    trial,
    channels,
}) {
    const channelsQuery = channels.join(",");

    const response = await fetch(
        `${API_BASE_URL}/tarea1/trial-signals?participant=${participant}&trial=${trial}&channels=${channelsQuery}`
    );

    if (!response.ok) {
        throw new Error("Error loading Tarea 1 trial signals");
    }

    return await response.json();
}