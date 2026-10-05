(function () {
  'use strict';

  const KEY = 'nextbestdollar-browser-beta-v3';
  const OLD = 'nextbestdollar-browser-beta-v2';

  function number(value) {
    const n = Number(value || 0);
    return Number.isFinite(n) && n >= 0 ? n : 0;
  }

  function money(value) {
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(number(value));
  }

  function readState() {
    try {
      const raw = localStorage.getItem(KEY) || localStorage.getItem(OLD);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      if (parsed && parsed.format === 'nextbestdollar-web' && parsed.profile) return parsed.profile;
      return parsed;
    } catch (_) {
      return null;
    }
  }

  function suggestedGoals(state) {
    if (!state || !state.financial_complete) return [];

    const f = state.financial || {};
    const debtList = Array.isArray(f.debt) ? f.debt : Object.values(f.debt || {});
    const existing = new Set((state.goals || []).map(goal => goal && goal.type));
    const results = [];

    function add(type, name, reason, targetAmount, progressAmount, priority) {
      if (existing.has(type)) return;
      results.push({
        type,
        name,
        reason,
        target_amount: targetAmount == null ? '' : targetAmount,
        progress_amount: progressAmount == null ? 0 : progressAmount,
        priority: priority || 'Medium',
        notes: ''
      });
    }

    const totalDebt = debtList.reduce((sum, debt) => sum + number(debt && debt.balance), 0);
    if (totalDebt > 0) {
      add(
        'Pay off debt',
        'Build a debt payoff goal',
        `You reported ${money(totalDebt)} in debt. Review a payoff target and timeline alongside your required payments.`,
        totalDebt,
        0,
        'High'
      );
    }

    const livingSpending = Object.values(f.spending || {}).reduce((sum, value) => sum + number(value), 0);
    const debtMinimums = debtList.reduce((sum, debt) => sum + number(debt && debt.minimum_payment), 0);
    const monthlyOutflows = livingSpending + debtMinimums;
    const reserve = number(f.accounts && f.accounts.emergency_fund);

    if (monthlyOutflows > 0 && reserve < monthlyOutflows) {
      add(
        'Emergency fund',
        'Build a cash buffer',
        `Your designated emergency savings (${money(reserve)}) is below one month of recorded outflows (${money(monthlyOutflows)}). Choose a reserve target that fits you.`,
        '',
        reserve,
        'Medium'
      );
    }

    const dependents = Number.parseInt(state.personal && state.personal.dependents, 10) || 0;
    if (dependents > 0) {
      add(
        'Children / family',
        'Plan for family costs',
        'You listed dependents. Consider a goal for care, education, or another family expense.',
        '',
        0,
        'Medium'
      );
    }

    if (!results.length) {
      add(
        'Other milestone',
        'Choose your next milestone',
        'What would you like your money to make possible? Choose your own target and timeline.',
        '',
        0,
        'Medium'
      );
    }

    return results;
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
    if (notice) notice.textContent = 'Suggested goal loaded below. Review it, choose any missing target amount or date, then press Save changes.';

    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
    const first = form.elements.namedItem('name');
    if (first) first.focus({ preventScroll: true });
  }

  function makeSuggestionCard(goal) {
    const card = document.createElement('article');
    card.className = 'card';

    const title = document.createElement('h3');
    title.textContent = goal.name;
    card.appendChild(title);

    const type = document.createElement('p');
    type.className = 'small';
    type.textContent = `${goal.type} · ${goal.priority} priority`;
    card.appendChild(type);

    const reason = document.createElement('p');
    reason.style.marginTop = '.75rem';
    reason.textContent = goal.reason;
    card.appendChild(reason);

    const button = document.createElement('button');
    button.type = 'button';
    button.className = 'button secondary-button';
    button.style.marginTop = '1rem';
    button.textContent = 'Use this suggestion';
    button.addEventListener('click', function () { fillGoalForm(goal); });
    card.appendChild(button);

    return card;
  }

  function injectSuggestions() {
    const page = document.getElementById('page-goals');
    if (!page || !page.classList.contains('active')) return;
    if (document.getElementById('nbd-suggested-goals')) return;

    const form = document.getElementById('goal-form');
    if (!form) return;

    const state = readState();
    const section = document.createElement('section');
    section.id = 'nbd-suggested-goals';
    section.className = 'card section';

    const heading = document.createElement('h2');
    heading.textContent = 'Suggested goals from your profile';
    section.appendChild(heading);

    const intro = document.createElement('p');
    intro.className = 'small';
    intro.style.marginTop = '.5rem';
    intro.textContent = 'These are explainable starting points based on the facts you entered. Nothing is added until you review and save it.';
    section.appendChild(intro);

    if (!state || !state.financial_complete) {
      const message = document.createElement('div');
      message.className = 'callout warning';
      message.textContent = 'Complete Financial facts first so NextBestDollar can suggest goals from your actual situation.';
      section.appendChild(message);
    } else {
      const suggestions = suggestedGoals(state);
      const grid = document.createElement('div');
      grid.className = 'card-grid';
      grid.style.marginTop = '1rem';
      suggestions.forEach(goal => grid.appendChild(makeSuggestionCard(goal)));
      section.appendChild(grid);
    }

    form.parentNode.insertBefore(section, form);
  }

  const observer = new MutationObserver(function () {
    window.requestAnimationFrame(injectSuggestions);
  });

  observer.observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });
  window.addEventListener('load', injectSuggestions);
  document.addEventListener('click', function (event) {
    if (event.target.closest('[data-page="goals"], [data-page-link="goals"]')) {
      window.setTimeout(injectSuggestions, 0);
    }
  });
})();
