(function () {
  "use strict";

  /* =====================================================================
     MAILING LIST — Kit (kit.com), "The Dual Eights Dispatch"
     ---------------------------------------------------------------------
     Signups POST straight to the Kit form endpoint below. The response is
     swallowed by the hidden "nl-sink" iframe so the reader never leaves
     the page; the status message under the form is our own.

     To repoint at a different Kit form: publish the form in Kit, open its
     HTML embed (not the JavaScript one), and copy the numeric id out of
     the action URL — https://app.kit.com/forms/<FORM_ID>/subscriptions
     Current form uid: 916b45cbd0
     ===================================================================== */
  var FORM_ID = "9740849";
  var EMAIL_FIELD = "email_address";
  /* ===================================================================== */

  var configured = /^\d+$/.test(FORM_ID);
  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  /* ---- Floating "Subscribe" button + popup ---- */
  var fab = document.getElementById("nl-fab");
  var modal = document.getElementById("nl-modal");
  var lastFocus = null;

  function openModal() {
    if (!modal) return;
    lastFocus = document.activeElement;
    modal.hidden = false;
    document.body.classList.add("nl-open");
    var field = modal.querySelector('input[type="email"]');
    if (field) setTimeout(function () { field.focus(); }, 30);
  }
  function closeModal() {
    if (!modal) return;
    modal.hidden = true;
    document.body.classList.remove("nl-open");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  if (fab && modal) {
    fab.addEventListener("click", openModal);
    modal.addEventListener("click", function (e) {
      if (e.target.closest("[data-nl-close]")) closeModal();
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !modal.hidden) closeModal();
    });
  }

  /* ---- Wire up every signup form (footer + popup) ---- */
  function wireForm(form) {
    var input = form.querySelector('input[type="email"]');
    if (!input) return;
    var scope = form.closest(".newsletter, .nl-modal-card, .post-cta") || form.parentNode;
    var status = scope ? scope.querySelector(".newsletter-status") : null;
    var inModal = !!form.closest("#nl-modal");

    function setStatus(msg, ok) {
      if (!status) return;
      status.textContent = msg;
      status.classList.toggle("is-error", ok === false);
      status.classList.toggle("is-ok", ok === true);
    }

    if (configured) {
      input.name = EMAIL_FIELD;
      form.action = "https://app.kit.com/forms/" + FORM_ID + "/subscriptions";
    }

    form.addEventListener("submit", function (e) {
      var email = (input.value || "").trim();
      if (!email || !EMAIL_RE.test(email)) {
        e.preventDefault();
        setStatus("Please enter a valid email address.", false);
        return;
      }
      if (!configured) {
        e.preventDefault();
        setStatus("Signup isn't connected yet — check back soon!", false);
        return;
      }
      // The POST goes to the hidden iframe so the visitor stays on the page.
      setStatus("Thanks! Check your inbox to confirm.", true);
      setTimeout(function () { form.reset(); }, 150);
      if (inModal) {
        setTimeout(function () {
          closeModal();
          setStatus("", null);
        }, 1900);
      }
    });
  }

  var forms = document.querySelectorAll(".newsletter-form");
  for (var i = 0; i < forms.length; i++) wireForm(forms[i]);
})();
