(function () {
  'use strict';
  const KEY = 'nextbestdollar-browser-beta-v3';
  const n = v => { const x = Number(v || 0); return Number.isFinite(x) ? Math.max(0, x) : 0; };
  const money = v => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(n(v));

  function read() {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (_) { return {}; }
  }

  function scoreState(s) {
    const f = s.financial || {};
    const income = Object.values(f.income || {}).reduce((a,b)=>a+n(b),0);
    const living = Object.values(f.spending || {}).reduce((a,b)=>a+n(b),0);
    const minimums = (f.debt || []).reduce((a,d)=>a+n(d.minimum_payment),0);
    const outflow = living + minimums;
    const free = income - outflow;
    const reserve = n(f.accounts && f.accounts.emergency_fund);
    const reserveMonths = outflow > 0 ? reserve / outflow : 0;
    const debt = (f.debt || []).reduce((a,d)=>a+n(d.balance),0);
    const highAprDebt = (f.debt || []).reduce((a,d)=>a + (n(d.apr) >= 8 ? n(d.balance) : 0), 0);
    const actual = Object.values(s.checkin || {}).reduce((a,b)=>a+n(b),0);
    const goalCount = (s.goals || []).length;

    const cashFlow = income <= 0 ? 0 : Math.max(0, Math.min(100, 50 + (free / income) * 250));
    const reserveScore = Math.max(0, Math.min(100, reserveMonths / 3 * 100));
    const debtScore = debt <= 0 ? 100 : highAprDebt > 0 ? Math.max(10, 70 - Math.min(60, highAprDebt / Math.max(income * 12,1) * 100)) : 75;
    const budgetScore = living <= 0 ? 50 : actual <= 0 ? 60 : Math.max(0, Math.min(100, 100 - Math.max(0, actual - living) / living * 200));
    const goalScore = goalCount >= 2 ? 100 : goalCount === 1 ? 75 : 40;

    const components = [
      ['Cash flow', cashFlow],
      ['Emergency reserve', reserveScore],
      ['Debt position', debtScore],
      ['Budget tracking', budgetScore],
      ['Goals', goalScore]
    ];
    const total = Math.round(components.reduce((a,[,v])=>a+v,0) / components.length);

    const suggestions = [];
    if (free < 0) suggestions.push(`Your recorded monthly outflows exceed income by ${money(Math.abs(free))}. Start by reducing or reclassifying recurring spending before allocating money to new goals.`);
    else if (income > 0 && free / income < 0.1) suggestions.push(`Only about ${Math.max(0, Math.round(free / income * 100))}% of take-home income is left after recorded outflows. Look for one or two recurring categories to trim before increasing investing.`);
    if (outflow > 0 && reserveMonths < 1) suggestions.push(`Your emergency reserve is under one month of recorded outflows. Consider prioritizing cash savings before taking more investment risk.`);
    else if (outflow > 0 && reserveMonths < 3) suggestions.push(`Your emergency reserve covers about ${reserveMonths.toFixed(1)} months. Building toward a larger buffer may improve flexibility.`);
    if (highAprDebt > 0) suggestions.push(`You have ${money(highAprDebt)} of debt at 8% APR or higher. Extra payoff dollars may deserve priority before taxable brokerage investing.`);
    if (goalCount === 0) suggestions.push('Add at least one concrete goal with a target amount. The allocation page can then suggest how to divide your discretionary cash around that goal.');
    if (actual > living && living > 0) suggestions.push(`Your actual tracked spending is ${money(actual - living)} above your planned living expenses. Review the categories with the biggest gap before changing your long-term plan.`);
    if (!suggestions.length) suggestions.push('Your recorded budget is relatively balanced. Use the allocation page to direct discretionary cash toward your highest-priority goals and test the trade-offs in Forecast.');

    return { total, components, suggestions, free, reserveMonths };
  }

  function inject() {
    const page = document.getElementById('page-overview');
    if (!page || !page.classList.contains('active') || document.getElementById('nbd-budget-coach')) return;
    const s = read();
    if (!s.financial_complete) return;
    const result = scoreState(s);
    const section = document.createElement('section');
    section.id = 'nbd-budget-coach';
    section.className = 'card section';
    section.innerHTML = `
      <p class="eyebrow">Budget coach</p>
      <h2>Your budgeting score and next moves</h2>
      <p class="small">This is an educational planning score based on the information you entered. It is not a credit score or financial advice.</p>
      <div class="nbd-budget-score">
        <div class="nbd-score-ring" style="--score:${result.total}"><strong>${result.total}</strong><span>out of 100</span></div>
        <div>
          <h3>${result.total >= 80 ? 'Strong foundation' : result.total >= 65 ? 'Solid, with room to improve' : result.total >= 50 ? 'Needs attention' : 'Rebuild the basics first'}</h3>
          <div class="nbd-score-breakdown">${result.components.map(([name,value])=>`<div class="nbd-score-row"><span>${name}</span><div class="nbd-score-track"><span style="width:${Math.round(value)}%"></span></div><strong>${Math.round(value)}</strong></div>`).join('')}</div>
        </div>
      </div>
      <div class="nbd-advice-list">${result.suggestions.slice(0,4).map(text=>`<div class="nbd-advice">${text}</div>`).join('')}</div>`;
    const firstSection = page.querySelector('.section');
    if (firstSection) firstSection.before(section); else page.appendChild(section);
  }

  const observer = new MutationObserver(() => requestAnimationFrame(inject));
  observer.observe(document.documentElement, { subtree: true, childList: true, attributes: true, attributeFilter: ['class'] });
  window.addEventListener('load', inject);
  document.addEventListener('click', e => { if (e.target.closest('[data-page="overview"]')) setTimeout(inject, 0); });
  setTimeout(inject, 350);
})();
