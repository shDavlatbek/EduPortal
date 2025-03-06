document.addEventListener('DOMContentLoaded', function() {
    const themeStorageKey = "twikerTheme";
    const defaultTheme = "light";
    let theme = null;

    function setTheme(theme, hideElements, showElements, hideElements2) {
        document.documentElement.setAttribute("data-bs-theme", theme);
        const themeLayoutElement = document.getElementById(`${theme}-layout`);
        if (themeLayoutElement) {
          themeLayoutElement.checked = true;
        }
  
        hideElements.forEach((el) =>
          document
            .querySelectorAll(`.${el}`)
            .forEach((e) => (e.style.display = "none"))
        );
        showElements.forEach((el) =>
          document
            .querySelectorAll(`.${el}`)
            .forEach((e) => (e.style.display = "flex"))
        );
        hideElements2.forEach((el) =>
          document
            .querySelectorAll(`.${el}`)
            .forEach((e) => (e.style.display = "none"))
        );
    };

    function initializeTheme() {
      const storedTheme = localStorage.getItem(themeStorageKey);
      theme = storedTheme ? storedTheme : defaultTheme;
      setTheme(theme, [], [], []);
    }

    function applyTheme() {
      if (theme === "dark") {
        setTheme("dark", ["dark-logo"], ["sun"], ["moon"]);
      } else {
        setTheme("light", ["light-logo"], ["moon"], ["sun"]);
      }
    }

    const toggleButton = document.querySelector('.theme-toggle');

    toggleButton.addEventListener('click', function() {
      theme = theme === "dark" ? "light" : "dark";
      localStorage.setItem(themeStorageKey, theme);
      applyTheme();
    });

    initializeTheme();

});
