function subnav() {
  return {
    isSubmenuVisible: !!this.$el.dataset.active,

    toggleSubnav() {
      this.isSubmenuVisible = !this.isSubmenuVisible;
    },

    subnavAriaExpanded: {
      [":aria-expanded"]() {
        return this.isSubmenuVisible.toString();
      }
    },
    subnavArrowStyles: {
      [":class"]() {
        return {
          "text-gray-400 rotate-90": this.isSubmenuVisible,
          "text-gray-300": !this.isSubmenuVisible,
        };
      },
    },
  };
}

export default subnav;
