export default () => ({
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
});
