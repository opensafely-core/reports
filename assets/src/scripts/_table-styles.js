// Table cells have `white-space: nowrap;` set
// This will find all cells with longer contents
// and unset that value
document
  .querySelectorAll("td")
  .forEach((item) =>
    item.textContent.length > 30
      ? (item.style.whiteSpace = "break-spaces")
      : null
  );

// Checks if an element has overflown it's boundary
const isOverflownX = ({ clientWidth, scrollWidth }) => {
  return scrollWidth > clientWidth;
};

// Adds the `.has-shadow` utility class if and overflow-wrapper
// element has overflown on the X axis
document
  .querySelectorAll(".overflow-wrapper")
  .forEach((wrapper) =>
    isOverflownX(wrapper) ? wrapper.classList.add("has-shadow") : null
  );
