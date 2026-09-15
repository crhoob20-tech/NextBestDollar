"""A single monthly budget, funded in the user's stated priority order."""
import tkinter as tk
from tkinter import ttk
from datetime import date
from copy import deepcopy
import math,sqlite3
from financial import normalize_financial
from storage import save_state
from ui import BG,WHITE,TEXT,MUTED,Button

def allocate(income,expenses,loans,savings,roth,minimums=0):
    values=(income,expenses,loans,savings,roth,minimums)
    if not all(math.isfinite(x) and x>=0 for x in values):raise ValueError('Enter nonnegative, finite monthly amounts.')
    if loans<minimums:raise ValueError(f'Total loan/debt allocation must cover recorded minimums of ${minimums:,.2f}.')
    available=max(0,income-expenses)
    rows=[]
    for name,requested in [('Loans / debt',loans),('Savings',savings),('Roth IRA',roth)]:
        funded=min(available,requested);available-=funded
        rows.append((name,requested,funded))
    rows.append(('Brokerage investing',available,available))
    shortfall=max(0,expenses+loans+savings+roth-income)
    return dict(rows=rows,shortfall=shortfall,available_before_allocations=income-expenses,
                living_expenses_funded=min(income,expenses),unfunded_minimums=max(0,minimums-rows[0][2]))

def build_allocation(parent,state,open_plan):
    f=normalize_financial(state.get('financial',{}));minimums=sum(d.get('minimum_payment',0) for d in f['debt'])
    saved=state.get('allocation_plan',{});prior=saved.get('inputs',{})
    frame=tk.Frame(parent,bg=BG);frame.pack(fill='both',expand=True,padx=20,pady=12)
    canvas=tk.Canvas(frame,bg=BG,highlightthickness=0);scroll=ttk.Scrollbar(frame,command=canvas.yview)
    body=tk.Frame(canvas,bg=BG);win=canvas.create_window((0,0),window=body,anchor='nw')
    body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>',lambda e:canvas.itemconfigure(win,width=e.width))
    canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
    def label(text):tk.Label(body,text=text,bg=BG,fg=TEXT,wraplength=710,justify='left').pack(anchor='w',pady=6)
    label('Give every available dollar one job')
    label('After living expenses: loans → savings → Roth IRA → remaining money to brokerage. These are your editable priorities, not a universal recommendation.')
    mode=tk.StringVar(value=prior.get('mode','Current budget'))
    ttk.Combobox(body,textvariable=mode,values=['Current budget','Future full-time scenario'],state='readonly').pack(fill='x')
    fields={}
    specs=[('gross','Annual gross salary ($; optional context only)',prior.get('gross','')),('income','Monthly take-home pay after payroll deductions ($)',prior.get('income',sum(f['income'].values()))),('expenses','Monthly living expenses, excluding debt payments ($)',prior.get('expenses',sum(f['spending'].values()))),('loans','Total monthly loans / debt, INCLUDING minimums ($)',prior.get('loans',minimums)),('savings','Monthly savings target ($)',prior.get('savings',round(max(0,sum(f['income'].values())-sum(f['spending'].values())-minimums)*.1,2)))]
    for key,text,value in specs:
        label(text);var=tk.StringVar(value=str(value));fields[key]=var
        tk.Entry(body,textvariable=var,bg=WHITE,fg=TEXT,insertbackground=TEXT).pack(fill='x',ipady=5)
    label(f'Recorded debt minimums: ${minimums:,.2f}/month. Gross salary is recorded for context; taxes are not inferred. Use expected take-home pay for a future job. Payroll retirement deductions already excluded from take-home are not subtracted again.')
    def use_current():
        fields['income'].set(str(sum(f['income'].values())));fields['expenses'].set(str(sum(f['spending'].values())));mode.set('Current budget')
    Button(body,text='Load my current budget',command=use_current).pack(anchor='w',pady=8)
    label('Roth IRA: check eligibility, then spread remaining annual room over the months you choose.')
    months=tk.StringVar(value='12');label('Months over which to fund this tax-year contribution (1–12)')
    ttk.Combobox(body,textvariable=months,values=list(range(1,13)),state='readonly').pack(fill='x')
    roth_mode=tk.StringVar(value='Pending check')
    ttk.Combobox(body,textvariable=roth_mode,values=['Pending check','Fund remaining Roth room','Skip Roth for this scenario'],state='readonly').pack(fill='x',pady=8)
    tax={}
    taxlabel=tk.Label(body,text='Roth allocation is $0 until eligibility is checked or you choose to skip it.',bg=BG,fg=MUTED,wraplength=710,justify='left');taxlabel.pack(anchor='w')
    def checked(raw,room):
        if raw['kind']!='Roth IRA':
            taxlabel.config(text='Choose Roth IRA for this allocation check.');tax.clear();roth_mode.set('Pending check');return
        tax.update(raw=raw,room=room);roth_mode.set('Fund remaining Roth room')
        taxlabel.config(text=f'2026 remaining Roth room: ${room:,.2f}. Future tax years require updated rules and income checks. This is not an approval for a future-year contribution.')
    from ira_rules import open_check
    Button(body,text='Check Roth eligibility / remaining room',command=lambda:open_check(body.winfo_toplevel(),state,checked)).pack(anchor='w',pady=8)
    output=tk.Label(body,text='',bg=BG,fg=TEXT,wraplength=710,justify='left');output.pack(anchor='w',pady=8)
    result_frame=tk.Frame(body,bg=BG);result_frame.pack(fill='x')
    latest={}
    def calculate():
        for w in result_frame.winfo_children():w.destroy()
        latest.clear()
        try:
            inputs={k:float(fields[k].get().replace(',','').replace('$','')) for k in ('income','expenses','loans','savings')}
            gross=fields['gross'].get().strip()
            if gross and (not math.isfinite(float(gross.replace(',',''))) or float(gross.replace(',',''))<0):raise ValueError('Enter a valid gross salary.')
            if roth_mode.get()=='Pending check':raise ValueError('Check Roth eligibility or explicitly choose Skip Roth before allocating the remainder.')
            if roth_mode.get()=='Fund remaining Roth room' and not tax:raise ValueError('Complete the Roth check first.')
            n=int(months.get())
            # Round down so a monthly contribution does not exceed remaining annual room.
            roth=math.floor(tax['room']/n*100)/100 if roth_mode.get()=='Fund remaining Roth room' else 0
            result=allocate(**inputs,roth=roth,minimums=minimums)
        except ValueError as exc:output.config(text=str(exc));return
        label_text=f"Available after living expenses: ${result['available_before_allocations']:,.2f}/month. "
        label_text+=f"Requested plan is short ${result['shortfall']:,.2f}/month." if result['shortfall'] else 'Your monthly plan balances.'
        if result['unfunded_minimums']:label_text+=f" Debt minimums remain underfunded by ${result['unfunded_minimums']:,.2f}."
        output.config(text=label_text)
        for name,requested,funded in result['rows']:
            tk.Label(result_frame,text=f'{name}: ${funded:,.2f}/month'+(f' (requested ${requested:,.2f})' if funded<requested else ''),bg=BG,fg=TEXT,font=('Helvetica',12,'bold')).pack(anchor='w',pady=6)
            kind={'Savings':'hysa','Roth IRA':'ira','Brokerage investing':'brokerage'}.get(name)
            if kind and funded:
                Button(result_frame,text='Explore this contribution',command=lambda k=kind,v=funded:open_plan({'account_type':k,'allocation_monthly':v})).pack(anchor='w',pady=3)
        tk.Label(result_frame,text='One shared monthly budget. Loan totals include minimum payments. Shortfalls reduce later allocations; they are never treated as investable money. Saved allocations are targets, not transfers or standing bank instructions.',bg=BG,fg=MUTED,wraplength=710,justify='left').pack(anchor='w',pady=10)
        latest.update(inputs=dict(inputs,gross=gross,mode=mode.get()),result=result,roth_months=n,roth_mode=roth_mode.get(),tax_year=2026)
    def save():
        calculate()
        if not latest:return
        draft=deepcopy(state);draft['allocation_plan']=dict(latest,saved_on=date.today().isoformat())
        if tax:draft['ira_check_inputs']=tax['raw']
        try:save_state(draft)
        except sqlite3.Error as exc:output.config(text=f'Unable to save: {exc}');return
        state.update(draft);output.config(text=output.cget('text')+' Saved as a scenario.')
    actions=tk.Frame(body,bg=BG);actions.pack(fill='x',pady=12)
    Button(actions,text='Build my allocation',command=calculate).pack(side='left')
    Button(actions,text='Save allocation scenario',command=save).pack(side='right')
