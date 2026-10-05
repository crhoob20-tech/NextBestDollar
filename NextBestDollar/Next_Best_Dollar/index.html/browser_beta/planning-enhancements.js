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

  function debtMinimums(s) {
    return (s.financial?.debt || []).reduce((a, d) => a + n(d.minimum_payment), 0);
  }

  function debtPayoffMonths(debts, totalMonthlyPayment) {
    const ds = (debts || []).filter(d => n(d.balance) > 0).map(d => ({
      balance: n(d.balance), rate: n(d.apr) / 1200, minimum: n(d.minimum_payment)
    }));
    if (!ds.length) return 0;
    const totalMinimums = ds.reduce((a, d) => a + d.minimum, 0);
    const budget = Math.max(totalMonthlyPayment, totalMinimums);
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

  function monthsUntil(dateString) {
    if (!dateString) return 0;
    const target = new Date(dateString + 'T12:00:00');
    if (Number.isNaN(target.getTime())) return 0;
    const now = new Date();
    const months = (target.getFullYear() - now.getFullYear()) * 12 + target.getMonth() - now.getMonth();
    return Math.max(1, months);
  }

  function goalBucket(goal, rothConfirmed) {
    if (goal.type === 'Pay off debt') return 'debt';
    if (goal.type === 'Invest') return rothConfirmed ? 'roth' : 'brokerage';
    return 'cash';
  }

  function goalBasedPlan(s, capacity) {
    const goals = (s.goals || []).filter(g => n(g.target_amount) > n(g.progress_amount));
    const plan = { debt: 0, cash: 0, roth: 0, brokerage: 0, details: [] };
    if (!goals.length || capacity <= 0) return plan;

    const dated = [];
    const undated = [];
    const priorityWeight = { High: 3, Medium: 2, Low: 1 };

    goals.forEach(goal => {
      const remaining = Math.max(0, n(goal.target_amount) - n(goal.progress_amount));
      const months = monthsUntil(goal.target_date);
      const item = {
        goal,
        bucket: goalBucket(goal, Boolean(s.allocation?.roth_confirmed)),
        remaining,
        weight: priorityWeight[goal.priority] || 2,
        needed: months ? remaining / months : 0
      };
      (months ? dated : undated).push(item);
    });

    let available = capacity;
    dated.sort((a,b) => b.weight - a.weight).forEach(item => {
      const amount = Math.min(available, item.needed);
      plan[item.bucket] += amount;
      available -= amount;
      plan.details.push({ name: item.goal.name, bucket: item.bucket, amount, target: item.goal.target_date, remaining: item.remaining });
    });

    if (available > 0 && undated.length) {
      const totalWeight = undated.reduce((sum, item) => sum + item.weight, 0);
      undated.forEach((item, index) => {
        const amount = index === undated.length - 1 ? available : available * item.weight / totalWeight;
        plan[item.bucket] += amount;
        plan.details.push({ name: item.goal.name, bucket: item.bucket, amount, target: '', remaining: item.remaining });
      });
      available = 0;
    }

    for (const key of ['debt','cash','roth','brokerage']) plan[key] = Math.round(plan[key] * 100) / 100;
    return plan;
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
    const capacity = monthlyFreeCash(s);
    const minimums = debtMinimums(s);
    const debtInput = form.elements.namedItem('debt');
    const cashInput = form.elements.namedItem('cash');
    const rothInput = form.elements.namedItem('roth');
    if (!debtInput || !cashInput || !rothInput) return;

    const debtLabel = debtInput.closest('label');
    if (debtLabel) {
      const text = [...debtLabel.childNodes].find(x => x.nodeType === Node.TEXT_NODE);
      if (text) text.nodeValue = 'Extra debt payment above required minimums';
    }
    const savedTotalDebtPayment = n(debtInput.value);
    debtInput.value = Math.max(0, savedTotalDebtPayment - minimums);

    const allocationGrid = form.querySelector('.field-grid');
    const brokerageLabel = document.createElement('label');
    brokerageLabel.innerHTML = `Monthly brokerage contribution<input name="brokerage" type="number" min="0" max="1000000000000" step="any" value="${n(s.allocation && s.allocation.brokerage)}">`;
    allocationGrid.appendChild(brokerageLabel);
    const brokerageInput = form.elements.namedItem('brokerage');

    const goalPlan = goalBasedPlan(s, capacity);
    const wrap = document.createElement('section');
    wrap.id = 'nbd-live-allocation';
    wrap.className = 'card section';
    wrap.innerHTML = `
      <p class="eyebrow">Discretionary money only</p>
      <h2>Allocate the money left after bills and required debt minimums</h2>
      <p class="small">Your monthly allocation capacity is the money left after recorded living expenses and required debt minimums. Move the four sliders to decide what the remaining dollars should do.</p>
      <div class="nbd-capacity-banner"><span>Available to allocate</span><strong>${money(capacity)}/mo</strong></div>
      <div class="nbd-slider-grid">
        <label>Extra debt payoff <strong id="nbd-debt-value"></strong><input id="nbd-debt-slider" type="range" min="0" step="10"></label>
        <label>Cash savings / goals <strong id="nbd-cash-value"></strong><input id="nbd-cash-slider" type="range" min="0" step="10"></label>
        <label>Roth IRA <strong id="nbd-roth-value"></strong><input id="nbd-roth-slider" type="range" min="0" step="10"></label>
        <label>Brokerage investing <strong id="nbd-brokerage-value"></strong><input id="nbd-brokerage-slider" type="range" min="0" step="10"></label>
      </div>
      <div id="nbd-allocation-status" class="callout"></div>
      <div id="nbd-goal-plan" class="nbd-goal-plan"></div>
      <div id="nbd-allocation-preview" class="card-grid nbd-preview-grid"></div>
      <div class="nbd-market-note"><strong>Illustrative investment assumption:</strong> the live preview uses a 7% annual return for Roth IRA + brokerage contributions. Use Forecast to test other market assumptions.</div>`;

    form.after(wrap);

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

    const goalArea = document.getElementById('nbd-goal-plan');
    if ((s.goals || []).length) {
      const rows = goalPlan.details.map(item => `
        <div class="nbd-goal-row"><div><strong>${item.name}</strong><span>${item.target ? 'Target ' + item.target : 'No target date'} · ${money(item.remaining)} remaining</span></div><strong>${money(item.amount)}/mo</strong></div>`).join('');
      goalArea.innerHTML = `
        <div class="nbd-goal-head"><div><p class="eyebrow">Connected to your goals</p><h3>Goal-based starting plan</h3></div><button type="button" id="nbd-apply-goals" class="button secondary-button">Apply goal-based plan</button></div>
        <p class="small">Dated goals are funded toward their target date first. Undated goals share the remaining capacity by priority. Investment goals use Roth if you have acknowledged eligibility; otherwise they use brokerage.</p>
        ${rows || '<p class="small">Your current goals are already funded.</p>'}`;
    } else {
      goalArea.innerHTML = '<div class="callout warning"><strong>No goals are connected yet.</strong> Add goals first, then this page can turn them into a suggested monthly allocation.</div>';
    }

    function render() {
      const extraDebt = n(sliders.debt.value), cash = n(sliders.cash.value), roth = n(sliders.roth.value), brokerage = n(sliders.brokerage.value);
      debtInput.value = extraDebt; cashInput.value = cash; rothInput.value = roth; brokerageInput.value = brokerage;
      document.getElementById('nbd-debt-value').textContent = money(extraDebt) + '/mo';
      document.getElementById('nbd-cash-value').textContent = money(cash) + '/mo';
      document.getElementById('nbd-roth-value').textContent = money(roth) + '/mo';
      document.getElementById('nbd-brokerage-value').textContent = money(brokerage) + '/mo';

      const requested = extraDebt + cash + roth + brokerage;
      let available = capacity;
      const fundedDebt = Math.min(available, extraDebt); available -= fundedDebt;
      const fundedCash = Math.min(available, cash); available -= fundedCash;
      const fundedRoth = Math.min(available, roth); available -= fundedRoth;
      const fundedBrokerage = Math.min(available, brokerage); available -= fundedBrokerage;
      const over = Math.max(0, requested - capacity);
      const unallocated = Math.max(0, capacity - requested);
      const status = document.getElementById('nbd-allocation-status');
      status.className = 'callout' + (over ? ' warning' : '');
      status.textContent = over
        ? `Your discretionary choices are ${money(over)} above the ${money(capacity)} you actually have available.`
        : `${money(unallocated)} of discretionary money remains unallocated.`;

      const months = debtPayoffMonths(s.financial?.debt || [], minimums + fundedDebt);
      const startingInvestments = Object.values(s.financial?.investments || {}).reduce((a,b)=>a+n(b),0);
      const investMonthly = fundedRoth + fundedBrokerage;
      const tenYear = futureValue(startingInvestments, investMonthly, 10, 7);
      const twentyYear = futureValue(startingInvestments, investMonthly, 20, 7);
      document.getElementById('nbd-allocation-preview').innerHTML = `
        <article class="card"><p class="metric-label">Discretionary capacity</p><strong class="metric-value">${money(capacity)}</strong></article>
        <article class="card"><p class="metric-label">Debt payoff</p><strong class="metric-value">${months === 0 ? 'No debt' : months ? Math.ceil(months/12) + ' yr' : 'Increase payment'}</strong><p class="small">Includes ${money(minimums)}/mo required minimums</p></article>
        <article class="card"><p class="metric-label">10-year invested value</p><strong class="metric-value">${money(tenYear)}</strong><p class="small">Roth + brokerage at 7%</p></article>
        <article class="card"><p class="metric-label">20-year invested value</p><strong class="metric-value">${money(twentyYear)}</strong><p class="small">Roth + brokerage at 7%</p></article>`;

      setTableRow(page, 'Loans / debt', minimums + extraDebt, minimums + fundedDebt);
      setTableRow(page, 'Savings', cash, fundedCash);
      setTableRow(page, 'Roth IRA', roth, fundedRoth);
      setTableRow(page, 'Brokerage investing', brokerage, fundedBrokerage);
    }

    Object.values(sliders).forEach(slider => slider.addEventListener('input', render));
    [[debtInput, sliders.debt], [cashInput, sliders.cash], [rothInput, sliders.roth], [brokerageInput, sliders.brokerage]].forEach(([input, slider]) => {
      input.addEventListener('input', () => { slider.value = n(input.value); render(); });
    });

    const applyGoals = document.getElementById('nbd-apply-goals');
    if (applyGoals) applyGoals.addEventListener('click', () => {
      sliders.debt.value = goalPlan.debt;
      sliders.cash.value = goalPlan.cash;
      sliders.roth.value = goalPlan.roth;
      sliders.brokerage.value = goalPlan.brokerage;
      render();
    });

    form.addEventListener('submit', () => {
      const extraDebt = n(debtInput.value);
      const brokerage = n(brokerageInput.value);
      debtInput.value = minimums + extraDebt;
      setTimeout(() => {
        const saved = state();
        saved.allocation = { ...(saved.allocation || {}), brokerage };
        writeState(saved);
      }, 0);
    }, true);

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
      <p>Use one of these illustrative annual return assumptions for account forecasts, or enter your own rate.</p>
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

      const initialLabel = labelFor(form, 'initial');
      if (initialLabel) setLabelText(initialLabel, 'Starting balance override');

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

      const note = form.querySelector('.small');
      if (note) {
        const copy = {
          'Accounts': 'Account forecasts use the saved balance unless you enter a starting-balance override. Choose an annual return assumption below. Taxes, fees and inflation are not modeled.',
          'Debt payoff': 'Debt payoff uses your recorded balances, APRs and required minimums plus the extra monthly payment you enter here, paying highest APR first.',
          'Goal': 'Goal forecasts use the goal target and current progress plus the monthly contribution you enter. No investment growth is assumed for this goal timeline.',
          'Job / income change': 'Use this model only to compare a different job or income scenario. Enter the new monthly take-home pay and any expected change in monthly living costs.'
        };
        note.textContent = copy[model] || '';
      }
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
    const feedbackForm = document.getElementById('feedback-form');
    if (feedbackForm) feedbackForm.before(status); else page.prepend(status);
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
