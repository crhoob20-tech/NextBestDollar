(function () {
  'use strict';

  const KEY = 'nextbestdollar-browser-beta-v3';
  const money = value => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value || 0));
  const n = value => { const x = Number(value || 0); return Number.isFinite(x) ? Math.max(0, x) : 0; };

  function state() {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (_) { return {}; }
  }

  function monthlyFreeCash(s) {
    const f = s.financial || {};
    const income = Object.values(f.income || {}).reduce((a, b) => a + n(b), 0);
    const spending = Object.values(f.spending || {}).reduce((a, b) => a + n(b), 0);
    const minimums = (f.debt || []).reduce((a, d) => a + n(d.minimum_payment), 0);
    return Math.max(0, income - spending - minimums);
  }

  function debtPayoffMonths(debts, monthlyPayment) {
    const ds = (debts || []).filter(d => n(d.balance) > 0).map(d => ({
      balance: n(d.balance), rate: n(d.apr) / 1200, minimum: n(d.minimum_payment)
    }));
    if (!ds.length) return 0;
    const totalMinimums = ds.reduce((a, d) => a + d.minimum, 0);
    const budget = Math.max(monthlyPayment, totalMinimums);
    if (budget <= 0) return null;
    for (let month = 1; month <= 1200; month++) {
      ds.forEach(d => d.balance += d.balance * d.rate);
      let left = budget;
      ds.forEach(d => { const pay = Math.min(d.minimum, d.balance, left); d.balance -= pay; left -= pay; });
      [...ds].sort((a,b) => b.rate - a.rate || a.balance - b.balance).forEach(d => {
        const pay = Math.min(d.balance, left); d.balance -= pay; left -= pay;
      });
      if (ds.reduce((a,d) => a + Math.max(0,d.balance),0) < 0.01) return month;
    }
    return null;
  }

  function futureValue(initial, monthly, years, annualRate) {
    const months = years * 12;
    const r = Math.pow(1 + annualRate / 100, 1 / 12) - 1;
    let balance = n(initial);
    for (let i = 0; i < months; i++) balance = balance * (1 + r) + n(monthly);
    return balance;
  }

  function addAllocationSliders() {
    const page = document.getElementById('page-allocation');
    const form = document.getElementById('allocation-form');
    if (!page || !page.classList.contains('active') || !form || document.getElementById('nbd-live-allocation')) return;

    const s = state();
    const free = monthlyFreeCash(s);
    const debtInput = form.elements.namedItem('debt');
    const cashInput = form.elements.namedItem('cash');
    const rothInput = form.elements.namedItem('roth');
    if (!debtInput || !cashInput || !rothInput) return;

    const wrap = document.createElement('section');
    wrap.id = 'nbd-live-allocation';
    wrap.className = 'card section';
    wrap.innerHTML = `
      <p class="eyebrow">Interactive plan</p>
      <h2>Drag your monthly allocation</h2>
      <p class="small">Move the sliders to see how different choices affect debt payoff and long-term investing. Values update the editable fields above, but nothing is saved until you press Save changes.</p>
      <div class="nbd-slider-grid">
        <label>Debt payment <strong id="nbd-debt-value"></strong><input id="nbd-debt-slider" type="range" min="0" step="10"></label>
        <label>Cash savings / goals <strong id="nbd-cash-value"></strong><input id="nbd-cash-slider" type="range" min="0" step="10"></label>
        <label>Roth IRA <strong id="nbd-roth-value"></strong><input id="nbd-roth-slider" type="range" min="0" step="10"></label>
      </div>
      <div id="nbd-allocation-preview" class="card-grid nbd-preview-grid"></div>
      <div class="nbd-market-note"><strong>Illustrative investment assumption:</strong> 7% annual return for this live preview. Use the Forecast tab to test other S&amp;P 500-based scenarios.</div>`;

    form.after(wrap);

    const minimums = (s.financial?.debt || []).reduce((a,d) => a + n(d.minimum_payment), 0);
    const max = Math.max(100, Math.ceil((free + minimums) / 50) * 50);
    const sliders = {
      debt: document.getElementById('nbd-debt-slider'),
      cash: document.getElementById('nbd-cash-slider'),
      roth: document.getElementById('nbd-roth-slider')
    };
    Object.values(sliders).forEach(x => x.max = max);
    sliders.debt.value = n(debtInput.value);
    sliders.cash.value = n(cashInput.value);
    sliders.roth.value = n(rothInput.value);

    function render() {
      const debt = n(sliders.debt.value), cash = n(sliders.cash.value), roth = n(sliders.roth.value);
      debtInput.value = debt; cashInput.value = cash; rothInput.value = roth;
      document.getElementById('nbd-debt-value').textContent = money(debt) + '/mo';
      document.getElementById('nbd-cash-value').textContent = money(cash) + '/mo';
      document.getElementById('nbd-roth-value').textContent = money(roth) + '/mo';
      const requested = debt + cash + roth;
      const capacity = free + minimums;
      const months = debtPayoffMonths(s.financial?.debt || [], debt);
      const startingInvestments = Object.values(s.financial?.investments || {}).reduce((a,b)=>a+n(b),0);
      const investMonthly = roth + Math.max(0, capacity - requested);
      const tenYear = futureValue(startingInvestments, investMonthly, 10, 7);
      const twentyYear = futureValue(startingInvestments, investMonthly, 20, 7);
      document.getElementById('nbd-allocation-preview').innerHTML = `
        <article class="card"><p class="metric-label">Monthly capacity</p><strong class="metric-value">${money(capacity)}</strong></article>
        <article class="card"><p class="metric-label">Debt payoff</p><strong class="metric-value">${months === 0 ? 'No debt' : months ? Math.ceil(months/12) + ' yr' : 'Increase payment'}</strong><p class="small">${months ? months + ' months' : ''}</p></article>
        <article class="card"><p class="metric-label">10-year invested value</p><strong class="metric-value">${money(tenYear)}</strong><p class="small">At 7% illustrative annual return</p></article>
        <article class="card"><p class="metric-label">20-year invested value</p><strong class="metric-value">${money(twentyYear)}</strong><p class="small">At 7% illustrative annual return</p></article>`;
    }
    Object.values(sliders).forEach(slider => slider.addEventListener('input', render));
    render();
  }

  function addMarketPresets() {
    const page = document.getElementById('page-forecast');
    const form = document.getElementById('forecast-form');
    if (!page || !page.classList.contains('active') || !form || document.getElementById('nbd-market-presets')) return;
    const annual = form.elements.namedItem('annual');
    if (!annual) return;
    const block = document.createElement('section');
    block.id = 'nbd-market-presets';
    block.className = 'card section';
    block.innerHTML = `
      <p class="eyebrow">Market reference</p>
      <h2>S&amp;P 500 return assumptions</h2>
      <p>Use one of these illustrative annual return assumptions, or enter your own rate above.</p>
      <div class="button-row nbd-preset-buttons">
        <button type="button" class="button secondary-button" data-rate="5">5% conservative</button>
        <button type="button" class="button secondary-button" data-rate="7">7% planning case</button>
        <button type="button" class="button secondary-button" data-rate="10">10% long-run reference</button>
        <button type="button" class="button secondary-button" data-rate="13.48">13.48% recent 10-year price return</button>
      </div>
      <p class="small"><strong>Context:</strong> S&amp;P Dow Jones Indices reported the S&amp;P 500 price return at 13.48% annualized over the 10 years ended Aug. 31, 2026. A separate S&amp;P historical study cited roughly 10.21% annual return for the S&amp;P 500 over its study period. Past performance is not a forecast. The 5% and 7% buttons are planning scenarios, not historical averages.</p>`;
    form.after(block);
    block.querySelectorAll('[data-rate]').forEach(button => button.addEventListener('click', () => {
      annual.value = button.dataset.rate;
      annual.dispatchEvent(new Event('change', { bubbles: true }));
      const submit = form.querySelector('button[type="submit"], .button:not([type="button"])');
      if (submit) submit.click();
    }));
  }

  function inject() {
    addAllocationSliders();
    addMarketPresets();
  }

  const observer = new MutationObserver(() => requestAnimationFrame(inject));
  observer.observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });
  window.addEventListener('load', inject);
  document.addEventListener('click', e => {
    if (e.target.closest('[data-page="allocation"], [data-page="forecast"]')) setTimeout(inject, 0);
  });
  setTimeout(inject, 300);
})();
