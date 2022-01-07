/**
 * Check for IE11 and add a class to the body for styling
 */
 const isIE11 = !!window.MSInputMethodContext && !!document.documentMode;

 if (isIE11) {
   document.documentElement.classList.add("ie11");
 }
