export function initializeViewNavigation() {
    const h1Button = document.getElementById("h1-tab-button");
    const h2Button = document.getElementById("h2-tab-button");

    const h1View = document.getElementById("h1-view");
    const h2View = document.getElementById("h2-view");

    h1Button.addEventListener("click", () => {
        h1View.classList.add("active-view");
        h1View.classList.remove("hidden-view");

        h2View.classList.add("hidden-view");
        h2View.classList.remove("active-view");

        h1Button.classList.add("active");
        h2Button.classList.remove("active");
    });

    h2Button.addEventListener("click", () => {
        h2View.classList.add("active-view");
        h2View.classList.remove("hidden-view");

        h1View.classList.add("hidden-view");
        h1View.classList.remove("active-view");

        h2Button.classList.add("active");
        h1Button.classList.remove("active");
    });
}