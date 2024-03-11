import Alpine from "alpinejs/packages/csp/dist/module.esm";
import Screen from "@alpine-collective/toolkit-screen/dist/module.esm";
import "./_ie11";
import "./_plausible";
import "../styles/main.scss";
import userMenu from "./alpine/user-menu";

Alpine.plugin(Screen);

Alpine.data("userMenu", userMenu);

window.Alpine = Alpine;
window.Alpine.start();
