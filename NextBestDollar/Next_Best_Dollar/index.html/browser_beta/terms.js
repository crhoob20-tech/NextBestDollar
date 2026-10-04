/* Beta terms acknowledgment is stored on this browser only; no network requests. */
(() => {
  'use strict';
  const version = '2026-10-03-draft-1';
  const storageKey = 'nextbestdollar.betaTermsAcknowledgment';
  const dialog = document.createElement('dialog');
  dialog.setAttribute('aria-labelledby', 'nbd-terms-title');
  dialog.style.cssText = 'max-width:36rem;width:calc(100% - 2rem);max-height:85vh;overflow:auto;border:1px solid #64748b;border-radius:16px;padding:1.5rem;color:#182334;background:#fff;line-height:1.6;box-sizing:border-box';
  dialog.innerHTML = `<h2 id="nbd-terms-title">Before you use the beta</h2>
    <p>NextBestDollar provides financial education and illustrative calculations. It does not provide personalized investment, tax, or legal advice. Estimates can be wrong; investment losses are possible.</p>
    <p>Your entered data and saved sessions stay in this browser unless you choose to download, share, or send them. People using this browser profile may be able to access them. External feedback forms have their own privacy terms.</p>
    <p><a href="terms.html" target="_blank" rel="noopener">Read the full beta terms and privacy notice (opens a new tab)</a>. These are draft terms pending legal review.</p>
    <label style="display:flex;gap:.7rem;align-items:flex-start"><input id="nbd-terms-check" type="checkbox" style="margin-top:.45rem"><span>I have read and acknowledge the beta terms and privacy notice.</span></label>
    <p id="nbd-terms-error" role="status"></p>
    <div style="display:flex;gap:1rem;flex-wrap:wrap"><button type="button" id="nbd-terms-continue" disabled>Continue to the beta</button><button type="button" id="nbd-terms-close">Close notice</button></div>`;
  document.body.append(dialog);
  const checkbox = dialog.querySelector('#nbd-terms-check');
  const proceed = dialog.querySelector('#nbd-terms-continue');
  let returnFocus;
  const open = () => {
    returnFocus = document.activeElement;
    checkbox.checked = false;
    proceed.disabled = true;
    dialog.querySelector('#nbd-terms-error').textContent = '';
    if (!dialog.open) dialog.showModal();
    checkbox.focus();
  };
  checkbox.addEventListener('change', () => { proceed.disabled = !checkbox.checked; });
  proceed.addEventListener('click', () => {
    if (!checkbox.checked) return;
    try {
      localStorage.setItem(storageKey, JSON.stringify({version, acknowledgedAt: new Date().toISOString()}));
    } catch (_) {
      dialog.querySelector('#nbd-terms-error').textContent = 'Your browser could not save this acknowledgment. You can continue, but this notice may appear again next time.';
      proceed.textContent = 'Continue without saving';
      proceed.onclick = () => dialog.close();
      return;
    }
    dialog.close();
  });
  dialog.querySelector('#nbd-terms-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { if (returnFocus && returnFocus.isConnected) returnFocus.focus(); });
  document.addEventListener('click', event => {
    if (event.target.closest('[data-open-terms]')) { event.preventDefault(); open(); }
  });
  let acknowledged = false;
  try { acknowledged = JSON.parse(localStorage.getItem(storageKey) || 'null')?.version === version; } catch (_) { /* Show the notice when storage is unavailable or malformed. */ }
  if (!acknowledged) open();
})();
