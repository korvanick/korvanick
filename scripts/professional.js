/* ============================================================================
   /professional — copy the work-history brief to the clipboard.

   The text lives in the page, in #brief-text, inside a <details>. This file
   reads it from the DOM rather than carrying its own copy, so there is
   exactly one version of that document and editing the HTML is enough.

   No inline handlers, so the page stays clean for the Content-Security-Policy
   that is still to be added to korvanick.conf.
   ============================================================================ */
(function () {
  const btn    = document.getElementById('copy-brief');
  const source = document.getElementById('brief-text');
  const status = document.getElementById('copy-status');
  if (!btn || !source) return;

  const IDLE = btn.dataset.label || btn.textContent.trim();
  let resetTimer = null;

  /* navigator.clipboard needs a secure context. The site is HTTPS, but a
     local http:// preview is not, so fall back to the old textarea trick
     rather than failing silently in exactly the place edits get tested. */
  function copy(text) {
    if (navigator.clipboard && window.isSecureContext) {
      return navigator.clipboard.writeText(text);
    }
    return new Promise(function (resolve, reject) {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.setAttribute('readonly', '');
      ta.style.position = 'fixed';   /* fixed, so focusing it cannot scroll the page */
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      let ok = false;
      try { ok = document.execCommand('copy'); } catch (e) { ok = false; }
      document.body.removeChild(ta);
      ok ? resolve() : reject(new Error('copy command rejected'));
    });
  }

  function report(label, message) {
    btn.textContent = label;
    if (status) status.textContent = message;
    clearTimeout(resetTimer);
    resetTimer = setTimeout(function () {
      btn.textContent = IDLE;
      if (status) status.textContent = '';
    }, 6000);
  }

  btn.addEventListener('click', function () {
    const text = source.textContent;
    copy(text).then(function () {
      const words = text.trim().split(/\s+/).length;
      report('Copied',
             'Copied about ' + words.toLocaleString() + ' words. Paste it into an ' +
             'LLM along with the job description you are hiring for.');
    }).catch(function () {
      /* Open the <details> so the text is on screen and can be selected by
         hand. A failed copy should still leave the visitor somewhere useful. */
      const details = source.closest('details');
      if (details) details.open = true;
      report('Copy failed',
             'The clipboard was not available. The full text is now open below ' +
             'and can be selected and copied by hand.');
    });
  });
})();
