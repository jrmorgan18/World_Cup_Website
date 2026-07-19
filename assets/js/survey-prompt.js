(function () {
  "use strict";

  var root = document.getElementById("survey-prompt");
  if (!root) return;

  var launcher = root.querySelector(".survey-prompt-launcher");
  var modal = root.querySelector(".survey-prompt-modal");
  var closeButtons = root.querySelectorAll("[data-survey-prompt-close]");
  var surveyLink = root.querySelector('a[href*="/survey/"]');
  var lastFocus = null;
  var seenKey = "wcg-survey-prompt-seen-v1";
  var completedKey = "wcg-survey-completed-v1";

  try {
    if (localStorage.getItem(completedKey) === "1") {
      root.hidden = true;
      return;
    }
  } catch (error) {}

  function openPrompt(automatic) {
    if (!modal || !modal.hidden) return;
    lastFocus = automatic ? null : document.activeElement;
    modal.hidden = false;
    document.body.classList.add("survey-prompt-open");
    try {
      sessionStorage.setItem(seenKey, "1");
    } catch (error) {}
    window.setTimeout(function () {
      if (surveyLink) surveyLink.focus();
    }, 30);
  }

  function closePrompt() {
    if (!modal) return;
    modal.hidden = true;
    document.body.classList.remove("survey-prompt-open");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }

  launcher.addEventListener("click", function () {
    openPrompt(false);
  });

  for (var i = 0; i < closeButtons.length; i += 1) {
    closeButtons[i].addEventListener("click", closePrompt);
  }

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape" && !modal.hidden) closePrompt();
  });

  if (root.dataset.autoOpen !== "true") return;

  var alreadySeen = false;
  try {
    alreadySeen = sessionStorage.getItem(seenKey) === "1";
  } catch (error) {}
  if (alreadySeen) return;

  var articleEnd = document.querySelector(".article-footer");
  if (!articleEnd || !("IntersectionObserver" in window)) return;

  var observer = new IntersectionObserver(
    function (entries) {
      if (!entries[0].isIntersecting) return;
      observer.disconnect();
      window.setTimeout(function () {
        openPrompt(true);
      }, 700);
    },
    { threshold: 0.08 }
  );

  observer.observe(articleEnd);
})();
