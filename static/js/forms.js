/* Client-side form validation & UX affordances.
   Server-side validation is authoritative — this only improves UX. */
(function () {
  "use strict";

  function showError(field, message) {
    clearError(field);
    var wrap = field.closest(".field");
    if (!wrap) return;
    var err = document.createElement("div");
    err.className = "error";
    err.textContent = message;
    wrap.appendChild(err);
    field.setAttribute("aria-invalid", "true");
  }

  function clearError(field) {
    var wrap = field.closest(".field");
    if (!wrap) return;
    var existing = wrap.querySelector(".error");
    if (existing) existing.remove();
    field.removeAttribute("aria-invalid");
  }

  function isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
  }

  function attachValidation(form) {
    form.addEventListener("submit", function (e) {
      var valid = true;
      form.querySelectorAll("[required]").forEach(function (field) {
        var value = (field.value || "").trim();
        if (!value) {
          showError(field, "This field is required.");
          valid = false;
        } else if (field.type === "email" && !isValidEmail(value)) {
          showError(field, "Please enter a valid email address.");
          valid = false;
        } else {
          clearError(field);
        }
      });

      if (!valid) {
        e.preventDefault();
        var firstError = form.querySelector('[aria-invalid="true"]');
        if (firstError) firstError.focus();
        return;
      }

      var submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn && !submitBtn.disabled) {
        submitBtn.dataset.originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = "Sending...";
      }
    });

    form.querySelectorAll("input, textarea, select").forEach(function (field) {
      field.addEventListener("input", function () { clearError(field); });
      field.addEventListener("change", function () { clearError(field); });
    });
  }

  document.querySelectorAll("form[data-validate]").forEach(attachValidation);

  // Resume file input: show selected filename
  document.querySelectorAll('input[type="file"]').forEach(function (input) {
    input.addEventListener("change", function () {
      var label = document.querySelector('[data-file-label-for="' + input.id + '"]');
      if (label) {
        label.textContent = input.files.length ? input.files[0].name : "No file chosen";
      }
    });
  });
})();
