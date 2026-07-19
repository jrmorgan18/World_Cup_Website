(function () {
  "use strict";

  document.addEventListener("click", function (event) {
    var link = event.target.closest("[data-donation-link]");
    if (!link || typeof window.gtag !== "function") return;

    window.gtag("event", "donation_click", {
      charity: "Soccer Without Borders Maryland",
      placement: link.getAttribute("data-donation-placement") || "unknown",
      outbound_url: link.href
    });
  });
})();
