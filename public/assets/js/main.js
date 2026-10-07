(function () {
  "use strict";

  // Remember the chosen language; the root page uses it to redirect.
  function rememberLanguage(lang) {
    try {
      localStorage.setItem("vx-lang", lang);
    } catch (e) {
      /* storage unavailable */
    }
  }

  rememberLanguage(document.documentElement.lang.indexOf("pt") === 0 ? "pt" : "en");
  document.querySelectorAll("[data-lang]").forEach(function (link) {
    link.addEventListener("click", function () {
      rememberLanguage(link.getAttribute("data-lang"));
    });
  });

  // Mobile navigation
  var burger = document.getElementById("burger");
  var nav = document.getElementById("nav");

  function setMenu(open) {
    nav.classList.toggle("is-open", open);
    burger.setAttribute("aria-expanded", open ? "true" : "false");
  }

  if (burger && nav) {
    burger.addEventListener("click", function () {
      setMenu(!nav.classList.contains("is-open"));
    });
    nav.addEventListener("click", function (event) {
      if (event.target.tagName === "A") setMenu(false);
    });
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        setMenu(false);
        burger.focus();
      }
    });
  }

  // Header border once the page scrolls
  var header = document.querySelector(".site-header");
  function onScroll() {
    header.classList.toggle("is-scrolled", window.scrollY > 8);
  }
  if (header) {
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }
})();
