(function () {
  "use strict";

  function getToken() {
    return localStorage.getItem("skillbridge-token") || "";
  }

  function authHeaders() {
    var token = getToken();
    return token ? { Authorization: "Bearer " + token } : {};
  }

  function updateThemeButton(theme) {
    var icon = document.getElementById("themeIcon");
    var button = document.getElementById("themeToggle");
    if (!icon || !button) {
      return;
    }
    icon.className = theme === "dark" ? "theme-icon icon-sun-fill" : "theme-icon icon-moon-stars-fill";
    button.setAttribute("aria-label", theme === "dark" ? "Switch to light theme" : "Switch to dark theme");
  }

  function initTheme() {
    var theme = localStorage.getItem("skillbridge-theme") || "light";
    document.documentElement.setAttribute("data-theme", theme);
    updateThemeButton(theme);
    var button = document.getElementById("themeToggle");
    if (!button) {
      return;
    }
    button.addEventListener("click", function () {
      var current = document.documentElement.getAttribute("data-theme") || "light";
      var next = current === "dark" ? "light" : "dark";
      document.documentElement.setAttribute("data-theme", next);
      localStorage.setItem("skillbridge-theme", next);
      updateThemeButton(next);
    });
  }

  async function logout() {
    try {
      await fetch("/api/logout", { method: "POST", headers: authHeaders() });
    } catch (error) {
      // Local logout should still complete if the old session already expired.
    }
    localStorage.removeItem("skillbridge-token");
    localStorage.removeItem("skillbridge-email");
    window.location.href = "index.html";
  }

  function initNav() {
    var loggedIn = Boolean(getToken());
    var savedLink = document.getElementById("savedJobsNav");
    var authButton = document.getElementById("authNavBtn");
    if (savedLink) {
      savedLink.hidden = !loggedIn;
    }
    if (authButton) {
      authButton.textContent = loggedIn ? "Logout" : "Login";
      authButton.addEventListener("click", function () {
        if (getToken()) {
          logout();
        } else {
          window.location.href = "login.html";
        }
      });
    }
  }

  window.SkillBridgeCommon = {
    authHeaders: authHeaders,
    getToken: getToken,
    initNav: initNav,
    initTheme: initTheme,
    logout: logout
  };

  document.addEventListener("DOMContentLoaded", function () {
    initTheme();
    initNav();
  });
}());
