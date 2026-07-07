export function initializeViewNavigation() {
    const h1Button = document.getElementById("h1-tab-button");
    const h2Button = document.getElementById("h2-tab-button");
    const tarea1Button = document.getElementById("tarea1-tab-button");
    const systemButton = document.getElementById("system-tab-button");

    const h1View = document.getElementById("h1-view");
    const h2View = document.getElementById("h2-view");
    const tarea1View = document.getElementById("tarea1-view");
    const systemView = document.getElementById("system-view");

    const topNavigation = document.querySelector(".top-navigation");

    const views = [h1View, h2View, tarea1View, systemView];
    const buttons = [h1Button, h2Button, tarea1Button, systemButton];

    function activateView(activeView, activeButton) {
        views.forEach((view) => {
            view.classList.add("hidden-view");
            view.classList.remove("active-view");
        });

        buttons.forEach((button) => {
            button.classList.remove("active");
        });

        activeView.classList.add("active-view");
        activeView.classList.remove("hidden-view");

        activeButton.classList.add("active");

        // System Overview es una vista inmersiva: oculta la barra de
        // navegación superior y deja solo el botón de retorno (visible
        // al hacer hover en la esquina superior izquierda) para volver
        // a H1.
        topNavigation.classList.toggle(
            "nav-hidden",
            activeView === systemView
        );
    }

    h1Button.addEventListener("click", () => {
        activateView(h1View, h1Button);
    });

    h2Button.addEventListener("click", () => {
        activateView(h2View, h2Button);
    });

    tarea1Button.addEventListener("click", () => {
        activateView(tarea1View, tarea1Button);
    });

    systemButton.addEventListener("click", () => {
        activateView(systemView, systemButton);
    });

    const systemBackButton = document.getElementById("system-back-button");

    systemBackButton.addEventListener("click", () => {
        activateView(h1View, h1Button);
    });

    // NOTA (2026-07-07): las cards de acceso a H1/H2/Tarea1 dentro de
    // System Overview se eliminaron -- System Overview ahora ES el CMV de
    // Husformer (Vistas A/B/C), no un menú de acceso a las otras vistas.
    // Si en el futuro se necesita volver a navegar desde aquí a H1/H2/Tarea1
    // sin pasar por systemBackButton, agregar los listeners aquí.
}