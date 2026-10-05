(function () {
  'use strict';

  const money = value => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(Number(value || 0));
  const round2 = value => Math.round((Number(value || 0) + Number.EPSILON) * 100) / 100;
  const clamp = (value, min, max) => Math.min(max, Math.max(min, Number(value || 0)));

  function fixAllocation() {
    const page = document.getElementById('page-allocation');
    const form = document.getElementById('allocation-form');
    const live = document.getElementById('nbd-live-allocation');
    if (!page || !page.classList.contains('active') || !form || !live || live.dataset.lockedAllocation === '1') return;
    live.dataset.lockedAllocation = '1';

    // Remove the visible IRA checkbox while keeping the existing validation path satisfied.
    const rothCheckbox = form.elements.namedItem('roth_confirmed');
    if (rothCheckbox) {
      const label = rothCheckbox.closest('label');
      if (label) label.remove();
      const hidden = document.createElement('input');
      hidden.type = 'hidden';
      hidden.name = 'roth_confirmed';
      hidden.value = 'true';
      form.appendChild(hidden);
    }

    const capacityText = live.querySelector('.nbd-capacity-banner strong')?.textContent || '';
    const capacityMatch = capacityText.replace(/[$,/a-zA-Z]/g, ' ').match(/-?\d+(?:\.\d+)?/);
    const capacity = round2(capacityMatch ? Number(capacityMatch[0]) : 0);

    const sliders = {
      debt: document.getElementById('nbd-debt-slider'),
      cash: document.getElementById('nbd-cash-slider'),
      roth: document.getElementById('nbd-roth-slider'),
      brokerage: document.getElementById('nbd-brokerage-slider')
    };
    const inputs = {
      debt: form.elements.namedItem('debt'),
      cash: form.elements.namedItem('cash'),
      roth: form.elements.namedItem('roth'),
      brokerage: form.elements.namedItem('brokerage')
    };
    if (Object.values(sliders).some(x => !x) || Object.values(inputs).some(x => !x)) return;

    Object.values(sliders).forEach(slider => {
      slider.max = String(capacity);
      slider.step = '0.01';
    });

    let updating = false;
    const keys = ['debt', 'cash', 'roth', 'brokerage'];

    function currentValues() {
      return Object.fromEntries(keys.map(key => [key, round2(clamp(sliders[key].value, 0, capacity))]));
    }

    function writeValues(values, triggerKey) {
      keys.forEach(key => {
        const value = round2(clamp(values[key], 0, capacity));
        sliders[key].value = String(value);
        inputs[key].value = String(value);
      });
      updating = true;
      sliders[triggerKey || 'debt'].dispatchEvent(new Event('input', { bubbles: true }));
      updating = false;
      const status = document.getElementById('nbd-allocation-status');
      if (status) {
        status.className = 'callout';
        status.textContent = `All ${money(capacity)} of your discretionary monthly income is allocated.`;
      }
    }

    function rebalance(changedKey) {
      if (updating || capacity <= 0) return;
      const values = currentValues();
      values[changedKey] = round2(clamp(values[changedKey], 0, capacity));
      const remaining = round2(capacity - values[changedKey]);
      const others = keys.filter(key => key !== changedKey);
      const otherTotal = others.reduce((sum, key) => sum + values[key], 0);

      if (otherTotal > 0) {
        let assigned = 0;
        others.forEach((key, index) => {
          if (index === others.length - 1) {
            values[key] = round2(remaining - assigned);
          } else {
            values[key] = round2(remaining * values[key] / otherTotal);
            assigned = round2(assigned + values[key]);
          }
        });
      } else {
        others.forEach(key => { values[key] = 0; });
        const fallback = changedKey === 'cash' ? 'brokerage' : 'cash';
        values[fallback] = remaining;
      }
      writeValues(values, changedKey);
    }

    function normalizeInitial() {
      if (capacity <= 0) return;
      const values = currentValues();
      const total = round2(keys.reduce((sum, key) => sum + values[key], 0));
      if (total <= 0) {
        values.cash = capacity;
      } else if (Math.abs(total - capacity) > 0.005) {
        let assigned = 0;
        keys.forEach((key, index) => {
          if (index === keys.length - 1) {
            values[key] = round2(capacity - assigned);
          } else {
            values[key] = round2(capacity * values[key] / total);
            assigned = round2(assigned + values[key]);
          }
        });
      }
      writeValues(values, 'debt');
    }

    keys.forEach(key => {
      sliders[key].addEventListener('input', () => rebalance(key));
      inputs[key].addEventListener('input', () => {
        if (updating) return;
        sliders[key].value = String(round2(clamp(inputs[key].value, 0, capacity)));
        rebalance(key);
      });
    });

    const goalButton = document.getElementById('nbd-apply-goals');
    if (goalButton) goalButton.addEventListener('click', () => setTimeout(normalizeInitial, 0));

    normalizeInitial();
  }

  function enhanceAbout() {
    const page = document.getElementById('page-guide');
    if (!page || !page.classList.contains('active') || page.dataset.enhancedAbout === '1') return;
    page.dataset.enhancedAbout = '1';
    page.innerHTML = `
      <p class="eyebrow">About NextBestDollar</p>
      <h1>Your financial plan, connected from start to finish.</h1>
      <p class="lead">NextBestDollar is an educational planning beta that turns the information you enter into a clearer view of your budget, goals, monthly allocation, and future scenarios.</p>

      <section class="section">
        <h2>How the app works</h2>
        <div class="card-grid">
          <article class="card"><p class="eyebrow">01</p><h3>Build your profile</h3><p>Enter personal facts, money habits, income, spending, accounts, debts, and benefits so the rest of the app has context.</p></article>
          <article class="card"><p class="eyebrow">02</p><h3>Understand your budget</h3><p>Overview summarizes cash flow and the Budget Coach highlights strengths, gaps, and practical areas to review.</p></article>
          <article class="card"><p class="eyebrow">03</p><h3>Set goals</h3><p>Create goals or use profile-based suggestions, including target amounts, dates, progress, and priority.</p></article>
          <article class="card"><p class="eyebrow">04</p><h3>Allocate what is left</h3><p>After living expenses and required debt minimums, divide your discretionary monthly income across extra debt payoff, cash goals, Roth IRA, and brokerage investing.</p></article>
          <article class="card"><p class="eyebrow">05</p><h3>Explore the future</h3><p>Forecast accounts, debt payoff, goal timelines, or a possible job change with visible assumptions and editable scenarios.</p></article>
          <article class="card"><p class="eyebrow">06</p><h3>Keep control of your data</h3><p>Your plan stays in this browser unless you download or share it. Use backup and import to move your saved plan between devices or browsers.</p></article>
        </div>
      </section>

      <section class="card section">
        <h2>What NextBestDollar is designed to help with</h2>
        <p>It connects budgeting, goal setting, debt decisions, savings, investing, and forecasting into one planning flow so the user can see how one decision changes the rest of the plan.</p>
        <div class="callout" style="margin-top:1rem"><strong>Planning flow:</strong> Profile → Budget → Goals → Allocation → Forecast → Review and adjust.</div>
      </section>

      <section class="card section">
        <h2>Beta limitations</h2>
        <p>Balances are manually entered. The app does not connect to banks, move money, check tax eligibility, or provide personalized investment, tax, or legal advice. Forecasts are educational illustrations and depend on the assumptions you choose.</p>
        <p style="margin-top:1rem"><a href="terms.html">Beta terms and privacy notice</a> · <button class="icon-button" data-open-terms>Review acknowledgment</button></p>
      </section>`;
  }

  function inject() {
    fixAllocation();
    enhanceAbout();
  }

  const observer = new MutationObserver(() => requestAnimationFrame(inject));
  observer.observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });
  window.addEventListener('load', inject);
  document.addEventListener('click', event => {
    if (event.target.closest('[data-page="allocation"], [data-page="guide"]')) setTimeout(inject, 0);
  });
  setTimeout(inject, 350);
})();
