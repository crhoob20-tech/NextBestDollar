(function () {
  'use strict';

  const KEY = 'nextbestdollar-browser-beta-v3';
  const OLD = 'nextbestdollar-browser-beta-v2';

  const n = value => {
    const x = Number(value || 0);
    return Number.isFinite(x) && x >= 0 ? x : 0;
  };

  const money = value => new Intl.NumberFormat('en-US', {
    style: 'currency', currency: 'USD'
  }).format(n(value));

  function readState() {
    try {
      const raw = localStorage.getItem(KEY) || localStorage.getItem(OLD);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      return parsed && parsed.format === 'nextbestdollar-web' && parsed.profile ? parsed.profile : parsed;
    } catch (_) {
      return null;
    }
  }

  function suggestionsFor(state) {
    if (!state) return [{
      type: 'Other milestone', name: 'Choose your next milestone',
      reason: 'Start with one thing you want your money to make possible.',
      target_amount: '', progress_amount: 0, priority: 'Medium', notes: ''
    }];

    const f = state.financial || {};
    const debts = Array.isArray(f.debt) ? f.debt : Object.values(f.debt || {});
    const spending = Object.values(f.spending || {}).reduce((s, v) => s + n(v), 0);
    const debtMinimums = debts.reduce((s, d) => s + n(d && d.minimum_payment), 0);
    const monthlyOutflow = spending + debtMinimums;
    const reserve = n(f.accounts && f.accounts.emergency_fund);
    const debt = debts.reduce((s, d) => s + n(d && d.balance), 0);
    const income = Object.values(f.income || {}).reduce((s, v) => s + n(v), 0);
    const freeCash = income - monthlyOutflow;
    const dependents = parseInt(state.personal && state.personal.dependents, 10) || 0;
    const match = n(f.benefits && f.benefits.employer_match);
    const contribution = n(f.benefits && f.benefits.current_retirement_contribution);
    const existing = new Set((state.goals || []).map(g => g && g.type));
    const out = [];

    function add(type, name, reason, targetAmount, progressAmount, priority) {
      if (existing.has(type)) return;
      out.push({
        type, name, reason,
        target_amount: targetAmount == null ? '' : targetAmount,
        progress_amount: progressAmount == null ? 0 : progressAmount,
        priority: priority || 'Medium', notes: ''
      });
    }

    if (debt > 0) {
      add('Pay off debt', 'Build a debt payoff goal',
        `You reported ${money(debt)} in debt. Turn that balance into a payoff target and timeline.`,
        debt, 0, 'High');
    }

    if (monthlyOutflow > 0 && reserve < monthlyOutflow * 3) {
      add('Emergency fund', 'Build a stronger cash buffer',
        `Your designated emergency savings are ${money(reserve)}. Three months of your recorded outflows is about ${money(monthlyOutflow * 3)}. Review the target and choose what fits your situation.`,
        monthlyOutflow * 3, reserve, debt > 0 ? 'Medium' : 'High');
    }

    if (dependents > 0) {
      add('Children / family', 'Plan for family costs',
        'You listed dependents. Consider a goal for care, education, or another recurring family priority.',
        '', 0, 'Medium');
    }

    if (match > contribution) {
      add('Invest', 'Review your employer retirement match',
        `You entered an employer match of ${match}% and a current retirement contribution of ${contribution}%. Review your plan rules and consider whether increasing contributions fits your budget.`,
        '', 0, 'Medium');
    } else if (freeCash > 0 && debt <= 0) {
      add('Invest', 'Build a consistent investing goal',
        `You have about ${money(freeCash)} of monthly breathing room after recorded living costs and debt minimums. Consider a long-term investing target after maintaining the cash reserve you need.`,
        '', 0, 'Medium');
    }

    if (!out.length) {
      add('Other milestone', 'Choose your next milestone',
        'Your core profile does not point to one obvious priority. Choose the next milestone that matters most to you.',
        '', 0, 'Medium');
    }

    return out.slice(0, 4);
  }

  function fillGoalForm(goal) {
    const form = document.getElementById('goal-form');
    if (!form) return;
    const set = (name, value) => {
      const field = form.elements.namedItem(name);
      if (field) field.value = value == null ? '' : String(value);
    };
    set('name', goal.name);
    set('type', goal.type);
    set('target_amount', goal.target_amount);
    set('progress_amount', goal.progress_amount);
    set('priority', goal.priority);
    set('notes', goal.notes || '');
    const notice = document.getElementById('app-notice');
    if (notice) notice.textContent = 'Suggestion loaded. Review the target and date, then save it as your goal.';
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  function cardFor(goal) {
    const card = document.createElement('article');
    card.className = 'card nbd-suggestion-card';
    const h = document.createElement('h3');
    h.textContent = goal.name;
    const meta = document.createElement('p');
    meta.className = 'small';
    meta.textContent = `${goal.type} · ${goal.priority} priority`;
    const reason = document.createElement('p');
    reason.className = 'nbd-suggestion-reason';
    reason.textContent = goal.reason;
    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'button secondary-button';
    button.textContent = 'Use this suggestion';
    button.addEventListener('click', () => fillGoalForm(goal));
    card.append(h, meta, reason, button);
    return card;
  }

  function inject() {
    const page = document.getElementById('page-goals');
    const form = document.getElementById('goal-form');
    if (!page || !page.classList.contains('active') || !form) return;

    const old = document.getElementById('nbd-suggested-goals');
    if (old) return;

    const section = document.createElement('section');
    section.id = 'nbd-suggested-goals';
    section.className = 'section nbd-suggestions';
    section.innerHTML = '<div class="nbd-section-heading"><div><p class="eyebrow">Based on your profile</p><h2>Suggested next goals</h2><p class="small">These are starting points generated from the financial facts you entered. Review every suggestion before saving it.</p></div></div>';

    const grid = document.createElement('div');
    grid.className = 'card-grid nbd-suggestion-grid';
    suggestionsFor(readState()).forEach(goal => grid.appendChild(cardFor(goal)));
    section.appendChild(grid);
    form.parentNode.insertBefore(section, form);
  }

  const observer = new MutationObserver(() => requestAnimationFrame(inject));
  observer.observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });
  window.addEventListener('load', inject);
  document.addEventListener('click', event => {
    if (event.target.closest('[data-page="goals"], [data-page-link="goals"]')) setTimeout(inject, 0);
  });
  setTimeout(inject, 250);
})();
