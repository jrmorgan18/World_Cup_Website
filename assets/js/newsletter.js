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
  var FORM_ID = "REPLACE_WITH_FORM_ID";
  var EMAIL_ENTRY = "entry.REPLACE_WITH_ENTRY_ID";
  /* ===================================================================== */

  var form = document.getElementById("newsletter-form");
  if (!form) return;
  var input = document.getElementById("nl-email");
  var status = document.getElementById("newsletter-status");

  var configured =
    FORM_ID.indexOf("REPLACE") === -1 && EMAIL_ENTRY.indexOf("REPLACE") === -1;

  if (configured) {
    input.name = EMAIL_ENTRY;
    form.action =
      "https://docs.google.com/forms/d/e/" + FORM_ID + "/formResponse";
  }

  function setStatus(msg, ok) {
    status.textContent = msg;
    status.classList.toggle("is-error", ok === false);
    status.classList.toggle("is-ok", ok === true);
  }

  form.addEventListener("submit", function (e) {
    var email = (input.value || "").trim();
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
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
    setTimeout(function () {
      form.reset();
    }, 150);
  });
})();
