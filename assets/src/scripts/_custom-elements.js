function addMenuButton() {
  const menuBtn = document.createElement("a");
  menuBtn.id = "menuBtn";
  menuBtn.textContent = "Go to menu";
  menuBtn.href = "#docNav";
  menuBtn.classList.add(
    "fixed",
    "bottom-0",
    "right-8",
    "px-4",
    "py-2",
    "border",
    "border-transparent",
    "text-base",
    "font-medium",
    "rounded-t-md",
    "text-white",
    "bg-oxford-700",
    "hover:bg-oxford-800",
    "focus:outline-none",
    "focus:ring-2",
    "focus:ring-offset-2",
    "focus:ring-oxford-500"
  );
  document.getElementById("content").appendChild(menuBtn);
}

function detailsEl({ summaryText = "", content = [] }) {
  const details = document.createElement("details");
  details.classList.add(
    "block",
    "my-2",
    "border",
    "border-oxford-400",
    "bg-oxford-50",
    "rounded-lg",
    "overflow-hidden",
    "open:[&>summary:hover]:bg-oxford-50",
    "open:[&>summary:hover]:text-oxford-600"
  );

  const summary = document.createElement("summary");
  summary.classList.add(
    "py-2",
    "px-4",
    "cursor-pointer",
    "text-lg",
    "font-semibold",
    "text-oxford-600",
    "hover:bg-oxford-100",
    "hover:text-oxford-900"
  );
  summary.textContent = summaryText;

  const wrapper = document.createElement("div");
  wrapper.classList = "m-0 px-8";

  details.appendChild(summary);
  details.appendChild(wrapper);

  content.map((item, i) => {
    if (i === 0) {
      item.classList.add("mt-0");
    }
    wrapper.appendChild(item);
  });

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

function docNavStyles(element) {
  element.classList.add(
    "m-0",
    "p-0",
    "list-none",
    "bg-oxford-50",
    "pt-14",
    "pb-4",
    "px-5",
    "rounded-lg",
    "relative",
    "overflow-hidden",
    "before:absolute",
    "before:top-0",
    "before:left-0",
    "before:z-10",
    "before:w-auto",
    "before:h-auto",
    "before:py-2",
    "before:px-4",
    "before:bg-oxford-900",
    "before:text-white",
    "before:rounded-br-md",
    "before:font-semibold",
    "before:text-lg",
    "before:content-['Menu']"
  );

  element.querySelectorAll("li").forEach((item) => {
    item.classList.add("!my-1");

    item.querySelectorAll("a").forEach((link) => {
      link.classList.add("text-lg");
    });
  });
}

function doOnDocumentLoaded() {
  const docNav = document.querySelector("#docNav");
  if (docNav) {
    addMenuButton();
    docNavStyles(docNav);
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
