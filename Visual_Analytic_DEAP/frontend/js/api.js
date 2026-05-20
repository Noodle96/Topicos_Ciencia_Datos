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
export async function fetchH2Relationships(participant, trial) {
  const response = await fetch(
    `/api/h2/relationships?participant=${participant}&trial=${trial}`
  );

  if (!response.ok) {
    throw new Error("Error loading H2 relationships");
  }

  return await response.json();
}