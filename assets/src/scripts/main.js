import Alpine from "alpinejs/packages/csp/dist/module.esm";
import Screen from "@alpine-collective/toolkit-screen/dist/module.esm";
import "./_ie11";
import "./_plausible";
import "../styles/main.scss";
import sidebar from "./alpine/sidebar";
import userMenu from "./alpine/user-menu";
import subnav from "./alpine/subnav";

Alpine.plugin(Screen);

Alpine.data("sidebar", sidebar);
Alpine.data("userMenu", userMenu);
Alpine.data("subnav", subnav);

window.Alpine = Alpine;
window.Alpine.start();
