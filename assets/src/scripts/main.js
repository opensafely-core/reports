import Alpine from "alpinejs/packages/csp/dist/module.esm";
import Screen from "@alpine-collective/toolkit-screen/dist/module.esm";
import "./_ie11";
import "./_plausible";
import "../styles/main.scss";

Alpine.plugin(Screen);

Alpine.data("sidebar", () => ({
  canShowSidebar: false,

  showSidebar() {
    this.canShowSidebar = true;
  },
  hideSidebar() {
    this.canShowSidebar = false;
  },

  get isLargeScreenSize() {
    return this.$screen("lg");
  },
  get isSidebarVisible() {
    if (this.canShowSidebar && !this.isLargeScreenSize) {
      return true;
    }
    return false;
  },

  sidebarBodyClass: {
    [":class"]() {
      return this.isSidebarVisible ? "overflow-y-hidden" : "overflow-y-scroll";
    },
  },

  sidebarOpenOrLargeScreen: {
    ["x-show"]() {
      return this.isSidebarVisible || this.isLargeScreenSize;
    },
  },
  sidebarOpenAndSmallScreen: {
    ["x-show"]() {
      return !this.isLargeScreenSize && this.isSidebarVisible;
    },
  },
}));

Alpine.data("userMenu", () => ({
  isUserNavOpen: false,
  showUserNav() {
    this.isUserNavOpen = true;
  },
  hideUserNav() {
    this.isUserNavOpen = false;
  },
}));

window.Alpine = Alpine;
window.Alpine.start();
