"""Educational next steps from current facts. No transfers or tax eligibility claims."""
import math
from financial import normalize_financial


def next_action(state):
    def result(kind, title, why, action, section='income', amount=0):
        return dict(kind=kind, title=title, why=why, action=action,
                    section=section, amount=round(amount, 2))

    if not state.get('financial_complete'):
        return result('setup', 'Start with your monthly money picture',
                      'Add take-home income, everyday spending, cash savings and debts. Estimates are OK; include annual bills divided by 12. You can update everything later.',
                      'Add my finances')
    try:
        f = normalize_financial(state.get('financial', {}))
        def money(value):
            if isinstance(value, bool):
                raise ValueError('Invalid amount')
            value = float(value)
            if not math.isfinite(value) or value < 0:
                raise ValueError('Invalid amount')
            return value
        income = sum(money(v) for v in f['income'].values())
        spending = sum(money(v) for v in f['spending'].values())
        minimums = sum(money(d['minimum_payment']) for d in f['debt'])
        debts = [(d, money(d['balance']), money(d['apr'])) for d in f['debt']]
        reserve = money(f['accounts'].get('emergency_fund', 0))
        cash = sum(money(f['accounts'].get(k, 0)) for k in ('checking', 'savings', 'hysa', 'other_cash'))
        if reserve > cash:
            raise ValueError('Emergency reserve exceeds cash')
    except (ValueError, TypeError, KeyError, AttributeError):
        return result('review', 'Review your financial inputs',
                      'Some saved amounts are missing or invalid. Review income, spending, accounts and debt rates before relying on a recommendation.', 'Review finances')
    outflow = spending + minimums
    surplus = round(income - outflow, 2)
    if outflow == 0:
        return result('review', 'Check your monthly costs',
                      'No living costs or debt payments are recorded. Include the bills you pay, including irregular expenses, before assigning leftover money.', 'Review my budget')
    if surplus <= 0:
        why = (f'Your recorded costs and minimum payments exceed take-home income by ${-surplus:,.2f}/month.'
               if surplus < 0 else 'Your recorded income exactly covers your costs and debt minimums.')
        return result('shortfall', 'Make room before assigning extra dollars',
                      why + ' Review flexible spending and income first. If a required payment is at risk, contact the provider about options.', 'Review income & spending')
    if reserve < outflow:
        amount = min(surplus, outflow - reserve)
        return result('buffer', f'Consider ${amount:,.2f} toward emergency savings this month',
                      f'You have ${reserve:,.2f} set aside for emergencies against ${outflow:,.2f} in monthly costs and minimums. This starter target uses one month of recorded outflows; choose a target that fits your household. Checking money is not assumed to be emergency savings.',
                      'Review emergency savings', 'accounts', amount)
    costly = sorted((item for item in debts if item[1] > 0 and item[2] >= 8), key=lambda item: item[2], reverse=True)
    if costly:
        debt, balance, apr = costly[0]
        amount = min(surplus, max(0, balance - money(debt['minimum_payment'])))
        if amount > 0:
            return result('debt', f'Consider up to ${amount:,.2f} extra toward {debt.get("name", "your highest-rate debt")}',
                          f'Its recorded annual interest rate (APR) is {apr:g}%, the highest among your debts. Paying higher-rate debt first can reduce interest costs. This is extra to minimums already counted; confirm the current payoff quote, fees and any special loan benefits. The 8% cutoff is an app planning assumption.',
                          'Review debt details', 'debt', amount)
    if reserve < 3 * outflow:
        amount = min(surplus, 3 * outflow - reserve)
        return result('reserve', f'Consider ${amount:,.2f} toward a larger cash cushion',
                      f'Your designated reserve covers {reserve / outflow:.1f} months of recorded costs. This illustration targets three months (${3 * outflow:,.2f}); income stability and dependents may call for a different target.',
                      'Review savings & target', 'accounts', amount)
    return result('plan', 'Choose the goal your next dollar should support',
                  f'Your recorded budget leaves ${surplus:,.2f}/month after spending and minimums, with a cash cushion in place. Review upcoming goals, remaining debt and employer retirement benefits before considering investing. Confirm match rules and tax eligibility separately; investment returns are uncertain.',
                  'Review my goals', 'goals')


def build_next_step(parent, state, navigate):
    import tkinter as tk
    from ui import Button, WHITE, TEXT, MUTED
    recommendation = next_action(state)
    card = tk.Frame(parent, bg=WHITE, highlightbackground='#D4DCE7', highlightthickness=1)
    card.pack(fill='x', pady=(12, 4))
    for text, font, color in [
        ('YOUR NEXT BEST DOLLAR', ('Helvetica', 10, 'bold'), '#2F6BFF'),
        (recommendation['title'], ('Helvetica', 16, 'bold'), TEXT),
        (recommendation['why'], ('Helvetica', 11), TEXT),
    ]:
        label = tk.Label(card, text=text, font=font, fg=color, bg=WHITE, justify='left', anchor='w')
        label.pack(fill='x', padx=18, pady=(10, 0))
        label.bind('<Configure>', lambda event, widget=label: widget.config(wraplength=max(200, event.width)))
    Button(card, text=recommendation['action'], command=lambda: navigate(recommendation['section'])).pack(anchor='w', padx=18, pady=12)
    note = tk.Label(card, text='Based on saved estimates • Review upcoming bills first • Educational guidance, not a transfer or a complete financial plan', bg=WHITE, fg=MUTED, justify='left')
    note.pack(fill='x', padx=18, pady=(0, 12))
    note.bind('<Configure>', lambda event: note.config(wraplength=max(200, event.width)))
