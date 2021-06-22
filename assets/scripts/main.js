import "../styles/main.scss";

/**
 * Check for IE11 and add a class to the body for styling
 */
const isIE11 = !!window.MSInputMethodContext && !!document.documentMode;

if (isIE11) {
  document.documentElement.classList.add("ie11");
}

/**
 * Plausible Analytics only on production
 * Compat mode for IE11
 */
// if (document.location.hostname === "reports.opensafely.org") {
  const ua = window.navigator.userAgent;
  const trident = ua.indexOf("Trident/");
  const msie = ua.indexOf("MSIE ");

  const script = document.createElement("script");
  script.defer = true;
  script.setAttribute("data-domain", "reports.opensafely.org");

  // Serve legacy compat script to IE users
  if (trident > 0 || msie > 0) {
    script.id = "plausible";
    script.src = "https://plausible.io/js/plausible.compat.js";
  } else {
    script.setAttribute("data-api", "/pa/api/event");
    script.src = "/pa/js/script.js";
  }

  document.head.appendChild(script);
// }
