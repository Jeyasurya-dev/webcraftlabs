/* Mobile nav, scroll-reveal, toast auto-dismiss — vanilla JS only. */
(function () {
  "use strict";

  // Mobile navigation toggle
  var toggle = document.querySelector(".nav-toggle");
  var navLinks = document.querySelector(".nav-links");
  if (toggle && navLinks) {
    toggle.addEventListener("click", function () {
      var open = navLinks.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    navLinks.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        navLinks.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      });
    });
  }

  // Scroll reveal
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    var observer = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("in");
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12 }
    );
    revealEls.forEach(function (el) { observer.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("in"); });
  }

  // Toast auto-dismiss
  document.querySelectorAll(".toast").forEach(function (toast) {
    setTimeout(function () {
      toast.style.transition = "opacity 0.4s ease";
      toast.style.opacity = "0";
      setTimeout(function () { toast.remove(); }, 400);
    }, 5000);
  });

  // Portfolio filter (no page reload needed when data is already rendered client-side is
  // out of scope; filtering here is via query param links, so nothing further needed).
})();
