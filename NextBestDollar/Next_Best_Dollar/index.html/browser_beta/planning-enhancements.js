(function () {
  'use strict';

  const KEY = 'nextbestdollar-browser-beta-v3';
  const money = value => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value || 0));
  const n = value => { const x = Number(value || 0); return Number.isFinite(x) ? Math.max(0, x) : 0; };

  function state() {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (_) { return {}; }
  }

  function writeState(next) {
    try { localStorage.setItem(KEY, JSON.stringify(next)); } catch (_) {}
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

  function setTableRow(page, label, requested, funded) {
    const rows = [...page.querySelectorAll('.table tbody tr')];
    const row = rows.find(r => r.cells[0] && r.cells[0].textContent.trim() === label);
    if (!row || row.cells.length < 3) return;
    row.cells[1].textContent = money(requested);
    row.cells[2].textContent = money(funded);
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

    const allocationGrid = form.querySelector('.field-grid');
    const brokerageLabel = document.createElement('label');
    brokerageLabel.innerHTML = `Monthly brokerage contribution<input name="brokerage" type="number" min="0" max="1000000000000" step="any" value="${n(s.allocation && s.allocation.brokerage)}">`;
    allocationGrid.appendChild(brokerageLabel);
    const brokerageInput = form.elements.namedItem('brokerage');

    const wrap = document.createElement('section');
    wrap.id = 'nbd-live-allocation';
    wrap.className = 'card section';
    wrap.innerHTML = `
      <p class="eyebrow">Interactive plan</p>
      <h2>Drag your monthly allocation</h2>
      <p class="small">Move the four sliders to test how your monthly capacity could be split. The preview updates instantly. Nothing is saved until you press Save changes.</p>
      <div class="nbd-slider-grid">
        <label>Debt payment <strong id="nbd-debt-value"></strong><input id="nbd-debt-slider" type="range" min="0" step="10"></label>
        <label>Cash savings / goals <strong id="nbd-cash-value"></strong><input id="nbd-cash-slider" type="range" min="0" step="10"></label>
        <label>Roth IRA <strong id="nbd-roth-value"></strong><input id="nbd-roth-slider" type="range" min="0" step="10"></label>
        <label>Brokerage investing <strong id="nbd-brokerage-value"></strong><input id="nbd-brokerage-slider" type="range" min="0" step="10"></label>
      </div>
      <div id="nbd-allocation-status" class="callout"></div>
      <div id="nbd-allocation-preview" class="card-grid nbd-preview-grid"></div>
      <div class="nbd-market-note"><strong>Illustrative investment assumption:</strong> the live preview uses a 7% annual return for Roth IRA + brokerage contributions. Use Forecast to test other market assumptions.</div>`;

    form.after(wrap);

    const minimums = (s.financial?.debt || []).reduce((a,d) => a + n(d.minimum_payment), 0);
    const capacity = free + minimums;
    const max = Math.max(100, Math.ceil(capacity / 50) * 50);
    const sliders = {
      debt: document.getElementById('nbd-debt-slider'),
      cash: document.getElementById('nbd-cash-slider'),
      roth: document.getElementById('nbd-roth-slider'),
      brokerage: document.getElementById('nbd-brokerage-slider')
    };
    Object.values(sliders).forEach(x => x.max = max);
    sliders.debt.value = n(debtInput.value);
    sliders.cash.value = n(cashInput.value);
    sliders.roth.value = n(rothInput.value);
    sliders.brokerage.value = n(brokerageInput.value);

    function render() {
      const debt = n(sliders.debt.value), cash = n(sliders.cash.value), roth = n(sliders.roth.value), brokerage = n(sliders.brokerage.value);
      debtInput.value = debt; cashInput.value = cash; rothInput.value = roth; brokerageInput.value = brokerage;
      document.getElementById('nbd-debt-value').textContent = money(debt) + '/mo';
      document.getElementById('nbd-cash-value').textContent = money(cash) + '/mo';
      document.getElementById('nbd-roth-value').textContent = money(roth) + '/mo';
      document.getElementById('nbd-brokerage-value').textContent = money(brokerage) + '/mo';

      const requested = debt + cash + roth + brokerage;
      let available = capacity;
      const fundedDebt = Math.min(available, debt); available -= fundedDebt;
      const fundedCash = Math.min(available, cash); available -= fundedCash;
      const fundedRoth = Math.min(available, roth); available -= fundedRoth;
      const fundedBrokerage = Math.min(available, brokerage); available -= fundedBrokerage;
      const over = Math.max(0, requested - capacity);
      const unallocated = Math.max(0, capacity - requested);
      const status = document.getElementById('nbd-allocation-status');
      status.className = 'callout' + (over ? ' warning' : '');
      status.textContent = over
        ? `Your requested allocation is ${money(over)} above your available monthly capacity.`
        : `${money(unallocated)} of monthly capacity remains unallocated.`;

      const months = debtPayoffMonths(s.financial?.debt || [], debt);
      const startingInvestments = Object.values(s.financial?.investments || {}).reduce((a,b)=>a+n(b),0);
      const investMonthly = fundedRoth + fundedBrokerage;
      const tenYear = futureValue(startingInvestments, investMonthly, 10, 7);
      const twentyYear = futureValue(startingInvestments, investMonthly, 20, 7);
      document.getElementById('nbd-allocation-preview').innerHTML = `
        <article class="card"><p class="metric-label">Monthly capacity</p><strong class="metric-value">${money(capacity)}</strong></article>
        <article class="card"><p class="metric-label">Debt payoff</p><strong class="metric-value">${months === 0 ? 'No debt' : months ? Math.ceil(months/12) + ' yr' : 'Increase payment'}</strong><p class="small">${months ? months + ' months' : ''}</p></article>
        <article class="card"><p class="metric-label">10-year invested value</p><strong class="metric-value">${money(tenYear)}</strong><p class="small">Roth + brokerage at 7%</p></article>
        <article class="card"><p class="metric-label">20-year invested value</p><strong class="metric-value">${money(twentyYear)}</strong><p class="small">Roth + brokerage at 7%</p></article>`;

      setTableRow(page, 'Loans / debt', debt, fundedDebt);
      setTableRow(page, 'Savings', cash, fundedCash);
      setTableRow(page, 'Roth IRA', roth, fundedRoth);
      setTableRow(page, 'Brokerage investing', brokerage, fundedBrokerage);
    }

    Object.entries(sliders).forEach(([key, slider]) => slider.addEventListener('input', render));
    [[debtInput, sliders.debt], [cashInput, sliders.cash], [rothInput, sliders.roth], [brokerageInput, sliders.brokerage]].forEach(([input, slider]) => {
      input.addEventListener('input', () => { slider.value = n(input.value); render(); });
    });

    form.addEventListener('submit', () => {
      const brokerage = n(brokerageInput.value);
      setTimeout(() => {
        const saved = state();
        saved.allocation = { ...(saved.allocation || {}), brokerage };
        writeState(saved);
      }, 0);
    });

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
      <p>Use one of these illustrative annual return assumptions, or enter your own rate in the account model.</p>
      <div class="button-row nbd-preset-buttons">
        <button type="button" class="button secondary-button" data-rate="5">5% conservative</button>
        <button type="button" class="button secondary-button" data-rate="7">7% planning case</button>
        <button type="button" class="button secondary-button" data-rate="10">10% long-run reference</button>
        <button type="button" class="button secondary-button" data-rate="13.48">13.48% recent 10-year price return</button>
      </div>
      <p class="small">Historical returns vary substantially. These are reference scenarios, not predictions, and taxes, fees and inflation are not modeled here.</p>`;
    form.after(block);
    block.querySelectorAll('[data-rate]').forEach(button => button.addEventListener('click', () => {
      annual.value = button.dataset.rate;
      annual.dispatchEvent(new Event('change', { bubbles: true }));
      const submit = form.querySelector('button[type="submit"], .button:not([type="button"])');
      if (submit) submit.click();
    }));
  }

  function labelFor(form, name) {
    const field = form.elements.namedItem(name);
    return field ? field.closest('label') : null;
  }

  function setLabelText(label, text) {
    if (!label) return;
    const node = [...label.childNodes].find(x => x.nodeType === Node.TEXT_NODE);
    if (node) node.nodeValue = text;
  }

  function configureForecastFields() {
    const page = document.getElementById('page-forecast');
    const form = document.getElementById('forecast-form');
    if (!page || !page.classList.contains('active') || !form) return;
    const kind = form.elements.namedItem('kind');
    if (!kind) return;

    const all = ['account','goal','initial','monthly','years','annual','increase','employer','takehome','cost_change','gross'];
    const visible = {
      'Accounts': ['account','initial','monthly','years','annual','increase','employer'],
      'Debt payoff': ['monthly'],
      'Goal': ['goal','monthly'],
      'Job / income change': ['takehome','cost_change','gross']
    };

    function apply() {
      const model = kind.value || 'Accounts';
      const show = new Set(visible[model] || []);
      all.forEach(name => {
        const label = labelFor(form, name);
        if (label) label.classList.toggle('nbd-hidden-field', !show.has(name));
      });

      const monthlyLabel = labelFor(form, 'monthly');
      if (model === 'Debt payoff') setLabelText(monthlyLabel, 'Extra monthly debt payment');
      else if (model === 'Goal') setLabelText(monthlyLabel, 'Monthly contribution to this goal');
      else setLabelText(monthlyLabel, 'Monthly investment contribution');

      const account = form.elements.namedItem('account');
      const employerLabel = labelFor(form, 'employer');
      if (model === 'Accounts' && account && employerLabel) {
        const s = state();
        const idx = parseInt(account.value, 10);
        const chosen = Number.isInteger(idx) ? s.financial?.account_entries?.[idx] : null;
        employerLabel.classList.toggle('nbd-hidden-field', !chosen || chosen.type !== 'retirement_employer');
      }

      const presets = document.getElementById('nbd-market-presets');
      if (presets) presets.hidden = model !== 'Accounts';
    }

    if (!form.dataset.nbdDynamicForecast) {
      form.dataset.nbdDynamicForecast = '1';
      kind.addEventListener('change', apply);
      const account = form.elements.namedItem('account');
      if (account) account.addEventListener('change', apply);
    }
    apply();
  }

  function clarifyFeedbackStatus() {
    const page = document.getElementById('page-feedback');
    if (!page || !page.classList.contains('active') || document.getElementById('nbd-feedback-status')) return;
    const configured = Boolean(window.NBD_CONFIG && window.NBD_CONFIG.googleFormUrl);
    const status = document.createElement('div');
    status.id = 'nbd-feedback-status';
    status.className = configured ? 'callout' : 'callout warning';
    status.innerHTML = configured
      ? '<strong>Central feedback is connected.</strong> Use the Google Form button above to send feedback to the beta owner.'
      : '<strong>Central feedback is not connected yet.</strong> “Save changes” only stores this feedback in this browser. “Download feedback only” creates a file the tester can send manually. A published Google Form link still needs to be added before responses flow to one place automatically.';
    const form = document.getElementById('feedback-form');
    if (form) form.before(status); else page.prepend(status);
  }

  function inject() {
    addAllocationSliders();
    addMarketPresets();
    configureForecastFields();
    clarifyFeedbackStatus();
  }

  const observer = new MutationObserver(() => requestAnimationFrame(inject));
  observer.observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });
  window.addEventListener('load', inject);
  document.addEventListener('click', e => {
    if (e.target.closest('[data-page="allocation"], [data-page="forecast"], [data-page="feedback"]')) setTimeout(inject, 0);
  });
  setTimeout(inject, 300);
})();
