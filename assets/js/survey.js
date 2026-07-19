(function () {
  "use strict";

  var form = document.getElementById("reader-survey");
  if (!form) return;

  var steps = Array.prototype.slice.call(form.querySelectorAll("[data-survey-step]"));
  var stepNumber = document.getElementById("survey-step-number");
  var progressBar = document.getElementById("survey-progress-bar");
  var status = document.getElementById("survey-status");
  var currentStep = 0;

  document.documentElement.classList.add("survey-js");
  form.classList.add("is-enhanced");

  function showStep(index, moveFocus) {
    currentStep = Math.max(0, Math.min(index, steps.length - 1));

    steps.forEach(function (step, i) {
      var active = i === currentStep;
      step.hidden = !active;
      step.classList.toggle("is-active", active);
    });

    if (stepNumber) stepNumber.textContent = String(currentStep + 1);
    if (progressBar) progressBar.style.width = ((currentStep + 1) / steps.length * 100) + "%";

    if (moveFocus) {
      var heading = steps[currentStep].querySelector("h2");
      if (heading) {
        heading.setAttribute("tabindex", "-1");
        heading.focus();
      }
      window.scrollTo({ top: Math.max(0, form.offsetTop - 110), behavior: "smooth" });
    }
  }

  function validateCurrentStep() {
    var fields = Array.prototype.slice.call(
      steps[currentStep].querySelectorAll("input, select, textarea")
    );

    for (var i = 0; i < fields.length; i += 1) {
      if (!fields[i].checkValidity()) {
        fields[i].reportValidity();
        return false;
      }
    }
    return true;
  }

  form.addEventListener("click", function (event) {
    var next = event.target.closest("[data-survey-next]");
    var back = event.target.closest("[data-survey-back]");

    if (next) {
      if (validateCurrentStep()) showStep(currentStep + 1, true);
    } else if (back) {
      showStep(currentStep - 1, true);
    }
  });

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    if (!validateCurrentStep()) return;

    var submit = form.querySelector('button[type="submit"]');
    var originalLabel = submit.textContent;
    submit.disabled = true;
    submit.textContent = "Sending…";
    if (status) {
      status.textContent = "";
      status.className = "survey-status";
    }

    fetch(form.action, {
      method: "POST",
      body: new FormData(form),
      headers: { Accept: "application/json" }
    })
      .then(function (response) {
        if (!response.ok) throw new Error("Submission failed");

        if (typeof window.gtag === "function") {
          window.gtag("event", "survey_complete", { survey_name: "post_world_cup_2026" });
        }

        form.innerHTML =
          '<div class="survey-thanks" tabindex="-1">' +
            '<span class="survey-thanks-mark" aria-hidden="true">✓</span>' +
            '<span class="survey-step-kicker">Response received</span>' +
            '<h2>Thank you for helping shape what comes next.</h2>' +
            '<p>Your answers will guide whether the site continues and which stories get the most attention.</p>' +
            '<a class="survey-button survey-button--primary" href="' + window.WC_SURVEY_HOME + '">Back to the latest coverage</a>' +
          '</div>';

        var thanks = form.querySelector(".survey-thanks");
        if (thanks) thanks.focus();
      })
      .catch(function () {
        submit.disabled = false;
        submit.textContent = originalLabel;
        if (status) {
          status.textContent = "Your response could not be sent. Please check your connection and try again.";
          status.className = "survey-status is-error";
        }
      });
  });

  showStep(0, false);
})();
