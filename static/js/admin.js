/* Admin UI interactions: delete confirmations, image preview, status forms. */
(function () {
  "use strict";

  // Confirm before any destructive action
  document.querySelectorAll("[data-confirm]").forEach(function (el) {
    el.addEventListener("submit", function (e) {
      var message = el.getAttribute("data-confirm") || "Are you sure?";
      if (!window.confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // Auto-submit status change selects
  document.querySelectorAll("[data-auto-submit]").forEach(function (select) {
    select.addEventListener("change", function () {
      select.form.submit();
    });
  });

  // Live image preview for project image upload
  var imageInput = document.querySelector('input[name="image"]');
  var preview = document.querySelector("[data-image-preview]");
  if (imageInput && preview) {
    imageInput.addEventListener("change", function () {
      var file = imageInput.files[0];
      if (!file) return;
      var reader = new FileReader();
      reader.onload = function (e) {
        preview.src = e.target.result;
        preview.style.display = "block";
      };
      reader.readAsDataURL(file);
    });
  }
})();
