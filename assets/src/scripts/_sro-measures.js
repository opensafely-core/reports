function addDocNav() {
  const docNav = document.querySelector("h1 ~ ul:last-of-type");
  docNav.id = "docNav";

  const menuBtn = document.createElement("a");
  menuBtn.id = "menuBtn";
  menuBtn.textContent = "Go to menu";
  menuBtn.href = "#docNav";
  document.querySelector(".ie-block").parentElement.append(menuBtn);
}

function detailsEl({ summaryText = "", content = [] }) {
  const details = document.createElement("details");
  const summary = document.createElement("summary");
  const wrapper = document.createElement("div");

  wrapper.classList = "details__wrapper";
  summary.textContent = summaryText;

  details.appendChild(summary);
  details.appendChild(wrapper);

  content.map((item) => wrapper.appendChild(item));

  return details;
}

function detailsBuilder({ element, end = undefined }) {
  const content = element.parentNode.children;

  const startContent = Array.from(content).indexOf(element);
  const endContent = end
    ? Array.from(content).indexOf(element.parentNode.querySelector(end))
    : undefined;

  return [...content].slice(startContent + 1, endContent);
}

if (document.location.pathname.includes("sro-measures")) {
  document.addEventListener("DOMContentLoaded", () => {
    addDocNav();

    document.querySelectorAll(`#What-it-is`).forEach((element) => {
      element.previousElementSibling.after(
        detailsEl({
          summaryText: "What it is",
          content: detailsBuilder({
            element,
            end: "#Why-it-matters",
          }),
        })
      );

      element.remove();
    });

    document.querySelectorAll(`#Why-it-matters`).forEach((element) => {
      element.previousElementSibling.after(
        detailsEl({
          summaryText: "Why it matters",
          content: detailsBuilder({ element }),
        })
      );

      element.remove();
    });
  });
}
