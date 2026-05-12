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