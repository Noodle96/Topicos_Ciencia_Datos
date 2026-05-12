import { fetchHealthStatus } from "./api.js";

/**
 * Inicializa la aplicación frontend.
 */
async function initApp() {
    const statusElement = document.getElementById("connection-status");

    try {
        const data = await fetchHealthStatus();

        statusElement.textContent = `✅ ${data.message}`;
        statusElement.style.color = "green";
    } catch (error) {
        statusElement.textContent = "❌ No se pudo conectar con el backend Flask";
        statusElement.style.color = "red";

        console.error(error);
    }
}

initApp();