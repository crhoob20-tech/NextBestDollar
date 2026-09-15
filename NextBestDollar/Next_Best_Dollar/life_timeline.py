"""Monthly illustrative cash flow and avalanche debt amortization; no bank access."""
from datetime import date
from copy import deepcopy
import math
import sqlite3
import tkinter as tk
from tkinter import ttk
from financial import normalize_financial
from storage import save_state
from ui import BG, TEXT, WHITE, MUTED, Button
from calendar_picker import DatePicker
from visual_charts import projection_chart, milestones


def month_date(start, offset):
    index = start.year * 12 + start.month - 1 + offset
    return date(index // 12, index % 12 + 1, 1)


def simulate(debts, inputs, start=None):
    start = start or date.today()
    p = dict(inputs)
    numeric = ('income', 'expenses', 'future_income', 'future_expenses', 'debt_budget',
               'savings_target', 'initial_savings', 'initial_investments', 'cash_rate', 'return_rate', 'years')
    for key in numeric:
        p[key] = float(p[key])
        if not math.isfinite(p[key]):
            raise ValueError('Enter finite numbers for every amount and rate.')
        if key not in ('return_rate',) and p[key] < 0:
            raise ValueError('Amounts and savings rates cannot be negative.')
    if not p['years'].is_integer() or not 1 <= p['years'] <= 60:
        raise ValueError('Choose a whole number of years from 1 to 60.')
    if not -100 < p['return_rate'] <= 100 or p['cash_rate'] > 100:
        raise ValueError('Investment return must be above −100% and at most 100%; cash rate at most 100%.')
    event = date.fromisoformat(p['event_date']) if p.get('event_date') else None
    if event and (event.year, event.month) < (start.year, start.month):
        raise ValueError('Choose this month or a future month for the life event.')
    loans = []
    for d in debts:
        balance, apr, minimum = (float(d.get(k, 0)) for k in ('balance', 'apr', 'minimum_payment'))
        if not all(math.isfinite(v) and v >= 0 for v in (balance, apr, minimum)):
            raise ValueError('Review your saved debt balances, rates and minimums.')
        loans.append(dict(name=d.get('name') or d.get('provider') or 'Debt', balance=balance,
                          apr=apr, minimum=minimum, interest=0., paid_off=0 if balance == 0 else None))
    savings, investments = p['initial_savings'], p['initial_investments']
    contributed = savings + investments
    cash_r = (1 + p['cash_rate']/100)**(1/12)-1
    inv_r = (1 + p['return_rate']/100)**(1/12)-1
    records, annual = [], []
    for m in range(int(p['years'])*12):
        current = month_date(start, m)
        future = event is not None and (current.year, current.month) >= (event.year, event.month)
        income = p['future_income'] if future else p['income']
        expenses = p['future_expenses'] if future else p['expenses']
        available = max(0., income-expenses)
        for d in loans:
            interest = d['balance'] * d['apr']/1200
            d['interest'] += interest
            d['balance'] += interest
        minimums = sum(min(d['balance'], d['minimum']) for d in loans)
        budget = min(available, max(p['debt_budget'], minimums))
        remaining = budget
        # Minimums first. Proportionate funding explicitly exposes any shortfall.
        ratio = min(1., budget/minimums) if minimums else 1.
        for d in loans:
            payment = min(d['balance'], d['minimum']) * ratio
            d['balance'] -= payment
            remaining -= payment
        for d in sorted(loans, key=lambda x: -x['apr']):
            payment = min(d['balance'], max(0., remaining))
            d['balance'] -= payment
            remaining -= payment
        debt_paid = budget - max(0., remaining)
        available -= debt_paid
        for d in loans:
            if d['balance'] < 1e-8:
                d['balance'] = 0.
                if d['paid_off'] is None: d['paid_off'] = m+1
        save_add = min(available, p['savings_target'])
        available -= save_add
        # Once debt is gone, optionally redirect its former budget to cash savings.
        if p.get('redirect') == 'Savings' and not any(d['balance'] for d in loans):
            extra = min(available, max(0., p['debt_budget']-debt_paid))
            save_add += extra
            available -= extra
        invest_add = max(0., available)
        savings = savings*(1+cash_r)+save_add
        investments = investments*(1+inv_r)+invest_add
        contributed += save_add+invest_add
        record = dict(month=m+1, income=income, expenses=expenses, debt_payment=debt_paid,
                      savings_added=save_add, invested=invest_add, savings=savings, investments=investments,
                      debt=sum(d['balance'] for d in loans), shortfall=max(0., expenses+minimums-income))
        records.append(record)
        if (m+1) % 12 == 0:
            annual.append(((m+1)//12, contributed, savings+investments-contributed, savings+investments))
    return dict(months=records, annual=annual, debts=loans,
                interest=sum(d['interest'] for d in loans), start=start.isoformat())


def build_timeline(parent, state):
    f = normalize_financial(state.get('financial', {}))
    old = state.get('life_timeline', {}).get('inputs', {})
    allocation = state.get('allocation_plan', {}).get('inputs', {})
    shell = tk.Frame(parent, bg=BG); shell.pack(fill='both', expand=True)
    canvas = tk.Canvas(shell, bg=BG, highlightthickness=0)
    scroll = ttk.Scrollbar(shell, command=canvas.yview); scroll.pack(side='right', fill='y')
    canvas.pack(side='left', fill='both', expand=True); canvas.configure(yscrollcommand=scroll.set)
    body = tk.Frame(canvas, bg=BG); win = canvas.create_window((0,0), window=body, anchor='nw')
    body.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>', lambda e: canvas.itemconfigure(win, width=e.width))
    def label(parent, text):
        tk.Label(parent, text=text, bg=BG, fg=TEXT, wraplength=780, justify='left').pack(anchor='w', padx=14, pady=6)
    label(body, 'Your debt-free date and the money you could build')
    label(body, 'Use your current budget, then explore graduation or a new job. All amounts stay editable.')
    form = tk.Frame(body, bg=BG); form.pack(fill='x', padx=14)
    values = {}
    def field(key, title, default):
        row = tk.Frame(form, bg=BG); row.pack(fill='x', pady=3)
        tk.Label(row, text=title, bg=BG, fg=TEXT, anchor='w', width=43).pack(side='left')
        values[key] = tk.StringVar(value=str(old.get(key, default)))
        tk.Entry(row, textvariable=values[key], bg=WHITE, fg=TEXT, insertbackground=TEXT).pack(side='right', fill='x', expand=True)
    field('income', 'Current monthly take-home pay ($)', sum(f['income'].values()))
    field('expenses', 'Current living expenses, excluding debt ($)', sum(f['spending'].values()))
    field('event_name', 'Life event (optional)', 'Graduation / full-time work')
    values['event_date'] = tk.StringVar(value=old.get('event_date',''))
    label(form, 'When does your new budget begin? Optional; starts in the selected month.')
    DatePicker(form, values['event_date']).pack(fill='x')
    field('gross', 'Future annual salary ($; context only)', allocation.get('gross',''))
    field('future_income', 'Future monthly take-home pay ($)', allocation.get('income', sum(f['income'].values())))
    field('future_expenses', 'Future monthly living expenses ($)', allocation.get('expenses', sum(f['spending'].values())))
    field('debt_budget', 'Monthly debt payment, including minimums ($)', allocation.get('loans', sum(d.get('minimum_payment',0) for d in f['debt'])))
    field('savings_target', 'Monthly savings target ($)', allocation.get('savings',0))
    field('initial_savings', 'Starting savings ($; excludes checking)', sum(a['balance'] for a in f['account_entries'] if a['type'] in ('savings','hysa')))
    field('initial_investments', 'Starting taxable brokerage balance ($)', sum(a['balance'] for a in f['account_entries'] if a['type']=='brokerage'))
    field('cash_rate', 'Estimated annual savings yield (%)', 0)
    field('return_rate', 'Estimated annual investment return (%)', 0)
    field('years', 'Years to explore', 10)
    values['redirect'] = tk.StringVar(value=old.get('redirect','Investing'))
    label(form, 'After debt payoff, redirect the former debt budget to:')
    ttk.Combobox(form,textvariable=values['redirect'],values=['Investing','Savings'],state='readonly').pack(fill='x')
    label(body, 'Living expenses → debt minimums and extra payments → savings target → remaining money to taxable investing. Existing payroll retirement contributions are already excluded from take-home pay. Roth contributions are handled separately in Account projection.')
    status = tk.Label(body,text='',bg=BG,fg=TEXT,wraplength=780,justify='left');status.pack(anchor='w',padx=14,pady=8)
    def edit_inputs():
        if form.winfo_manager(): form.pack_forget()
        else: form.pack(fill='x',padx=14,before=status)
    Button(body,text='Show / hide my inputs',command=edit_inputs).pack(anchor='w',padx=14,pady=8)
    result = tk.Frame(body,bg=BG);result.pack(fill='x',padx=14)
    def run(save=False):
        try:
            raw = {k:v.get().strip().replace(',','') for k,v in values.items()}
            if raw['gross'] and (not math.isfinite(float(raw['gross'])) or float(raw['gross'])<0):
                raise ValueError('Enter a valid future gross salary or leave it blank.')
            data = simulate(f['debt'],raw)
        except (ValueError,OverflowError) as exc:
            status.config(text=str(exc));return
        for child in result.winfo_children():child.destroy()
        last = data['months'][-1]
        short = sum(r['shortfall']>0.005 for r in data['months'])
        status.config(text=f"Focus first: cover living costs and debt minimums ({short} modeled months have a shortfall)." if short else 'Your essential costs and debt minimums fit this scenario.')
        label(result,f"Savings + taxable investments: ${last['savings']+last['investments']:,.0f} • Debt remaining: ${last['debt']:,.0f}")
        projection_chart(result,data['annual'],float(raw['initial_savings'])+float(raw['initial_investments']))
        label(result,f"Estimated debt interest paid/accrued: ${data['interest']:,.0f}. Green line shows starting money + additions, the 0% comparison.")
        for d in data['debts']:
            when = ('Already paid off' if d['paid_off']==0 else month_date(date.today(),d['paid_off']-1).strftime('%b %Y')) if d['paid_off'] is not None else 'Not paid off within this timeline'
            label(result,f"{d['name']}: {when} • Remaining ${d['balance']:,.0f}")
        detail = tk.Frame(result,bg=BG)
        def toggle():
            if detail.winfo_manager():detail.pack_forget()
            else:detail.pack(fill='x')
        Button(result,text='Show / hide yearly milestones',command=toggle).pack(anchor='w',pady=8)
        for row in milestones(data['annual']):
            r=data['months'][row[0]*12-1]
            label(detail,f"Year {row[0]}: savings ${r['savings']:,.0f} • investments ${r['investments']:,.0f} • debt ${r['debt']:,.0f}")
        for caption, index in [('First month',0),('Final month',len(data['months'])-1)]:
            r=data['months'][index]
            label(detail,f"{caption}: take-home ${r['income']:,.0f}; living ${r['expenses']:,.0f}; debt paid ${r['debt_payment']:,.0f}; saved ${r['savings_added']:,.0f}; invested ${r['invested']:,.0f}.")
        label(result,'Estimate: fixed APR, monthly debt interest, month-end payments and contributions; extra payments go to the highest APR. No new borrowing, fees, changing minimums, deferment, forgiveness, taxes or inflation modeled. Shortfalls are flagged, not financed; an underfunded scenario is incomplete. Investment returns can be negative. Salary is context only; enter take-home pay yourself. This is not a total-net-worth forecast or an IRA eligibility check.')
        if save:
            draft=deepcopy(state);draft['life_timeline']={'inputs':raw,'saved_on':date.today().isoformat()}
            try:save_state(draft)
            except sqlite3.Error as exc:status.config(text=f'Could not save: {exc}');return
            state.update(draft);status.config(text=status.cget('text')+' Scenario saved.')
        form.pack_forget()
        body.update_idletasks()
        canvas.yview_moveto(0)
    actions=tk.Frame(body,bg=BG);actions.pack(fill='x',padx=14,pady=12)
    Button(actions,text='Show my timeline',command=run).pack(side='left')
    Button(actions,text='Save timeline',command=lambda:run(True)).pack(side='right')
