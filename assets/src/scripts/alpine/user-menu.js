export default () => ({
  isUserNavOpen: false,

  showUserNav() {
    this.isUserNavOpen = true;
  },
  hideUserNav() {
    this.isUserNavOpen = false;
  },

  userNavAriaExpanded: {
    [":aria-expanded"]() {
      return this.isUserNavOpen.toString();
    }
  },
});
