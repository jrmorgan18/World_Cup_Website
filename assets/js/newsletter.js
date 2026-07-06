(function () {
  "use strict";

  /* =====================================================================
     MAILING LIST SETUP — replace the two values below, then commit.
     ---------------------------------------------------------------------
     1. In Gmail/Google Drive, create a Google Form with ONE question:
        a "Short answer" question titled "Email" (mark it Required).
     2. In the form's Responses tab, click the green Sheets icon to send
        every signup into a Google Sheet automatically.
     3. Click "Send" on the form, choose the link (<>) tab, and copy the
        live form URL. It looks like:
          https://docs.google.com/forms/d/e/1FAIpQLSxxxxxxxx/viewform
        The long part between /d/e/ and /viewform is your FORM_ID.
     4. Open that live form in your browser, right-click the email box and
        choose "Inspect". Find the input's name — it looks like
        "entry.1234567890". Paste that whole string into EMAIL_ENTRY.
     ===================================================================== */
  var FORM_ID = "1FAIpQLSeob9vw5hPZYI6ZqOmh2xRrY4l0kMudRy2nitv9nrZsN4-NHQ";
  var EMAIL_ENTRY = "entry.181187106";
  /* ===================================================================== */

  var configured =
    FORM_ID.indexOf("REPLACE") === -1 && EMAIL_ENTRY.indexOf("REPLACE") === -1;
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
    var scope = form.closest(".newsletter, .nl-modal-card") || form.parentNode;
    var status = scope ? scope.querySelector(".newsletter-status") : null;
    var inModal = !!form.closest("#nl-modal");

    function setStatus(msg, ok) {
      if (!status) return;
      status.textContent = msg;
      status.classList.toggle("is-error", ok === false);
      status.classList.toggle("is-ok", ok === true);
    }

    if (configured) {
      input.name = EMAIL_ENTRY;
      form.action =
        "https://docs.google.com/forms/d/e/" + FORM_ID + "/formResponse";
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
      setStatus("Thanks! You're on the list. ⚽", true);
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
