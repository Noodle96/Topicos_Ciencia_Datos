// export function initializeViewNavigation() {
//     const h1Button = document.getElementById("h1-tab-button");
//     const h2Button = document.getElementById("h2-tab-button");

//     const h1View = document.getElementById("h1-view");
//     const h2View = document.getElementById("h2-view");

//     h1Button.addEventListener("click", () => {
//         h1View.classList.add("active-view");
//         h1View.classList.remove("hidden-view");

//         h2View.classList.add("hidden-view");
//         h2View.classList.remove("active-view");

//         h1Button.classList.add("active");
//         h2Button.classList.remove("active");
//     });

//     h2Button.addEventListener("click", () => {
//         h2View.classList.add("active-view");
//         h2View.classList.remove("hidden-view");

//         h1View.classList.add("hidden-view");
//         h1View.classList.remove("active-view");

//         h2Button.classList.add("active");
//         h1Button.classList.remove("active");
//     });
// }

export function initializeViewNavigation() {
    const h1Button = document.getElementById("h1-tab-button");
    const h2Button = document.getElementById("h2-tab-button");
    const tarea1Button = document.getElementById("tarea1-tab-button");

    const h1View = document.getElementById("h1-view");
    const h2View = document.getElementById("h2-view");
    const tarea1View = document.getElementById("tarea1-view");

    const views = [h1View, h2View, tarea1View];
    const buttons = [h1Button, h2Button, tarea1Button];

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
}