function addMenuButton() {
  const menuBtn = document.createElement("a");
  menuBtn.id = "menuBtn";
  menuBtn.textContent = "Go to menu";
  menuBtn.href = "#docNav";
  document.getElementById("content").appendChild(menuBtn);
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

function detailsBuilder({ element }) {
  const content = [...element.parentNode.children];
  const elements = [...element.parentNode.querySelectorAll(".details")];

  const nextElement = elements[elements.indexOf(element) + 1];
  const findEndElement = content.indexOf(nextElement);

  const sliceStart = content.indexOf(element) + 1;
  const sliceEnd = nextElement ? findEndElement : undefined;

  return content.slice(sliceStart, sliceEnd);
}

function doOnDocumentLoaded() {
  if (document.querySelector("#docNav")) {
    addMenuButton();
  }

  document.querySelectorAll(`.details`).forEach((element) => {
    element.previousElementSibling.after(
      detailsEl({
        summaryText: element.textContent,
        content: detailsBuilder({
          element,
        }),
      })
    );

    element.remove();
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", doOnDocumentLoaded);
} else {
  doOnDocumentLoaded();
}
