$(document).ready(function () {
  "use strict";

  // =================================
  // Back to top button
  // =================================
  $(window).on("scroll", function () {
    if ($(this).scrollTop() > 200) {
      $("#back-to-top").fadeIn().css("bottom", "20px");
    } else {
      $("#back-to-top").fadeOut().css("bottom", "-200px");
    }
  });

  $("#back-to-top").on("click", function (e) {
    e.preventDefault();
    $("html, body").animate({ scrollTop: 0 }, 100);
  });

  // NOTE: Popover functionality has been moved to twiker-bs-popover.js
});
