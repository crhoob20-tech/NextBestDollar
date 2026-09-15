"""Illustrative monthly compound-growth scenarios, not predicted returns."""
import tkinter as tk
from tkinter import ttk
import math
from ui import Button, BG, WHITE, TEXT, MUTED

def project(initial,monthly,years,annual,increase=0,employer=0):
    if not all(math.isfinite(x) for x in (initial,monthly,years,annual,increase,employer)):
        raise ValueError('Enter finite numbers.')
    if increase < -100 or increase > 100 or employer < 0 or initial<0 or monthly<0 or years<1 or years>60 or years!=int(years) or annual<=-100 or annual>100:
        raise ValueError('Use nonnegative balances, whole years from 1–60, and an annual return above -100% and at most 100%.')
    # Annual effective rate converted to its equivalent monthly rate.
    rate=(1+annual/100)**(1/12)-1
    balance=initial;rows=[];paid=initial
    for month in range(1,int(years)*12+1):
        contribution=(monthly+employer)*(1+increase/100)**((month-1)//12)
        balance=balance*(1+rate)+contribution
        paid+=contribution
        if month%12==0:
            rows.append((month//12,paid,balance-paid,balance))
    return rows

GROUPS = {
    'Savings & investing': [('hysa','High-yield savings (cash)'),('savings','Savings (cash)'),('brokerage','Brokerage (investments)')],
    'Retirement': [('retirement_employer','Workplace retirement'),('ira','Roth / traditional IRA')],
    'Children & education': [('savings','Savings for a child'),('529','529 education account')],
    'Health': [('hsa','Health Savings Account (HSA)')],
}
EXPLAIN = {
    'hysa':'Cash savings that earns interest. Enter your account’s rate in More options.',
    'savings':'Money set aside for a goal. Enter your savings rate in More options.',
    'brokerage':'An account for investments such as funds, stocks and bonds. Value can rise or fall.',
    'retirement_employer':'A retirement account through work. Use your payroll contribution; employer dollars are optional.',
    'ira':'Retirement on your terms. A Roth IRA uses after-tax contributions; qualified withdrawals can be tax-free. A traditional IRA has different tax treatment. Eligibility and annual limits apply. The investments inside the account determine growth.',
    '529':'Saving for a child’s education? Explore a 529. Investment choices often include age-based portfolios. Qualified education withdrawals can receive tax benefits; fees, state benefits and eligible expenses vary by plan.',
    'hsa':'An account for eligible health expenses. Eligibility matters; money may be held in cash or invested.',
}

def account_choices(state, group):
    from financial import normalize_financial
    entries=normalize_financial(state.get('financial',{}))['account_entries']
    kinds=dict(GROUPS[group]);choices=[]
    for i,a in enumerate(entries):
        if a['type'] in kinds:
            choices.append(dict(a,key=f"saved:{a['type']}:{a['name']}:{a.get('provider','')}:{i}",label=f"{a['name']} — {kinds[a['type']]}"))
    for kind,label in GROUPS[group]:
        if any(a['type']==kind for a in choices):continue
        if kind=='retirement_employer' and state.get('personal',{}).get('retirement_access')!='Yes':continue
        choices.append(dict(type=kind,name=label,label='Explore: '+label,balance=0,key='explore:'+kind))
    return choices

def suggested_monthly(state,goal=None,years=10):
    available=state.get('financial_metrics',{}).get('monthly_free_cash_flow')
    if available is None:return None,'Complete your budget to see a suggested amount.'
    if available<=0:return 0,'Your recorded expenses meet or exceed income. Suggested additional saving: $0 until the budget changes.'
    if goal:
        gap=max(0,goal['target_amount']-goal.get('progress_amount',0))
        amount=min(available,gap/(years*12))
        return round(amount,2),'Starting estimate: remaining goal amount divided over this horizon, capped at your monthly surplus. No growth assumed.'
    return round(available*.1,2),'Example starting amount: 10% of your recorded monthly surplus. Adjust it alongside your other goals.'

def build_forecast(parent,state,context=None):
    PlanView(parent,state,context or {})

class PlanView:
    def __init__(self,parent,state,context):
        from ui import style_widgets
        style_widgets(parent)
        self.state=state;self.context=context;self.drafts={};self.goal=None;self.ira_check=None;self.return_notes={}
        outer=tk.Frame(parent,bg=BG);outer.pack(fill='both',expand=True,padx=26,pady=10)
        self.canvas=tk.Canvas(outer,bg=BG,highlightthickness=0)
        scroll=ttk.Scrollbar(outer,orient='vertical',command=self.canvas.yview)
        self.body=tk.Frame(self.canvas,bg=BG);win=self.canvas.create_window((0,0),window=self.body,anchor='nw')
        self.body.bind('<Configure>',lambda e:self.canvas.configure(scrollregion=self.canvas.bbox('all')))
        self.canvas.bind('<Configure>',lambda e:self.canvas.itemconfigure(win,width=e.width))
        self.canvas.configure(yscrollcommand=scroll.set);scroll.pack(side='right',fill='y');self.canvas.pack(side='left',fill='both',expand=True)
        target=context.get('account_type')
        group=next((g for g,items in GROUPS.items() if target in dict(items)),next(iter(GROUPS)))
        self.group=tk.StringVar(value=group);self.selected_key=None
        self.choose()
    def clear(self,title):
        for child in self.body.winfo_children():child.destroy()
        self.canvas.yview_moveto(0)
        self.label(title,True)
    def label(self,text,bold=False,parent=None):
        widget=tk.Label(parent or self.body,text=text,bg=BG,fg=TEXT if bold else MUTED,wraplength=710,justify='left',font=('Helvetica',15,'bold') if bold else ('Helvetica',10))
        widget.pack(anchor='w',pady=(8,8));return widget
    def choose(self):
        self.clear('What do you want your money to do?')
        self.label('1  Choose your purpose     →     2  Build a scenario     →     3  Explore the future')
        purposes=tk.Frame(self.body,bg=BG);purposes.pack(fill='x',pady=10)
        descriptions={
            'Savings & investing':('Build wealth or save soon','Cash savings for near-term needs; brokerage for investing.'),
            'Retirement':('Prepare for retirement','Explore workplace plans and Roth / traditional IRAs.'),
            'Children & education':('Give a child a head start','Compare a 529 education plan with cash savings.'),
            'Health':('Plan for health costs','Explore an HSA if you meet eligibility requirements.'),
        }
        purpose_buttons=[]
        for index,(group,(title,description)) in enumerate(descriptions.items()):
            tile=tk.Frame(purposes,bg=WHITE,highlightbackground='#DEE5EF',highlightthickness=1)
            tile.grid(row=index//2,column=index%2,sticky='nsew',padx=(0,8) if index%2==0 else (8,0),pady=8)
            radio=tk.Radiobutton(tile,text=title,variable=self.group,value=group,bg=WHITE,fg=TEXT,
                selectcolor='#E7EFFF',activebackground=WHITE,font=('Helvetica',12,'bold'),anchor='w',
                command=lambda:populate())
            radio.pack(fill='x',padx=12,pady=(12,4));purpose_buttons.append(radio)
            from ui import copy_label
            description_label=copy_label(tile,description,color=MUTED)
            description_label.pack_configure(padx=16,pady=(0,16))
            purposes.columnconfigure(index%2,weight=1,uniform='purpose')
        if self.group.get()=='Retirement':
            from occupation import prompt
            self.label(prompt(self.state.get('personal',{}).get('work_sector','')))
        self.label('Choose an account')
        account=ttk.Combobox(self.body,state='readonly');account.pack(fill='x',pady=6)
        explanation=self.label('')
        def populate(event=None):
            self.choices=account_choices(self.state,self.group.get())
            account.config(values=[a['label'] for a in self.choices])
            index=next((i for i,a in enumerate(self.choices) if a['key']==self.selected_key),None)
            if index is None:index=next((i for i,a in enumerate(self.choices) if a['type']==self.context.get('account_type')),0)
            account.current(index);changed()
        def changed(event=None):
            self.chosen=self.choices[account.current()];self.selected_key=self.chosen['key']
            explanation.config(text=EXPLAIN[self.chosen['type']])
        account.bind('<<ComboboxSelected>>',changed);populate()
        self.label('Connect a savings goal (optional)')
        self.goals=[g for g in self.state.get('goals',[]) if g.get('type')!='Pay off debt']
        goals=ttk.Combobox(self.body,values=['No goal selected']+[g['name'] for g in self.goals],state='readonly');goals.pack(fill='x',pady=6)
        selected=next((i+1 for i,g in enumerate(self.goals) if (self.goal and g.get('id')==self.goal.get('id')) or g.get('id')==self.context.get('goal_id') and g.get('id')),0);goals.current(selected)
        def proceed():
            self.goal=self.goals[goals.current()-1] if goals.current()>0 else None
            self.numbers()
        self.label('An account is the container. Cash, funds, stocks or bonds inside it determine the return—not the account name. No account is opened here.')
        Button(self.body,text='Continue to my numbers',command=proceed).pack(anchor='w',pady=12)
    def numbers(self):
        from datetime import date
        self.clear('2. Review your starting plan')
        self.label(self.chosen['name'],True)
        key=self.chosen['key'];kind=self.chosen['type']
        if key not in self.drafts:
            saved=self.state.get('forecast_plans',{}).get(key,{})
            years=10
            if self.goal and self.goal.get('target_date'):
                years=max(1,min(60,math.ceil((date.fromisoformat(self.goal['target_date'])-date.today()).days/365.25)))
            suggestion,reason=suggested_monthly(self.state,self.goal,years)
            monthly=self.chosen.get('monthly_contribution',suggestion)
            if kind=='retirement_employer' and 'monthly_contribution' not in self.chosen:monthly=''
            defaults=dict(initial=self.chosen['balance'],monthly='' if monthly is None else monthly,years=years,annual=0,increase=0,employer=0)
            defaults.update(saved);defaults['initial']=self.chosen['balance']
            if self.context.get('account_type')==kind and 'allocation_monthly' in self.context:
                defaults['monthly']=self.context['allocation_monthly']
            self.drafts[key]={k:tk.StringVar(value=str(v)) for k,v in defaults.items()}
        self.fields=self.drafts[key]
        def entry(parent,key,title):
            self.label(title,parent=parent)
            tk.Entry(parent,textvariable=self.fields[key],bg=WHITE,fg=TEXT,insertbackground=TEXT,font=('Helvetica',12)).pack(fill='x',ipady=6)
        entry(self.body,'initial','Balance today ($) — loaded from your saved account')
        entry(self.body,'monthly','Monthly contribution ($)')
        suggestion,reason=suggested_monthly(self.state,self.goal,10)
        if kind=='retirement_employer':reason='Enter your actual payroll contribution, or use the salary helper below. We do not infer gross salary from take-home pay.'
        elif self.goal and suggestion is not None and suggestion>0:reason='Suggested starting amount uses your remaining goal and selected horizon, capped at your recorded surplus. Review the amount if you change the horizon.'
        self.label(reason)
        entry(self.body,'years','Years from now')
        entry(self.body,'annual','Annual return assumption (%)')
        if key not in self.return_notes:
            self.return_notes[key]=tk.StringVar(value=self.state.get('forecast_return_notes',{}).get(key,''))
        from return_guidance import build_return_guidance
        build_return_guidance(self.body,kind,self.fields['annual'],self.return_notes[key])
        advanced=tk.Frame(self.body,bg=BG)
        toggle=Button(self.body,text='Optional: contribution increases & employer',command=lambda:None)
        toggle.pack(anchor='w',pady=12)
        def expand():
            if advanced.winfo_manager():advanced.pack_forget();toggle.config(text='Optional: contribution increases & employer')
            else:advanced.pack(fill='x',after=toggle);toggle.config(text='Hide more options')
        toggle.command=expand
        # Button bindings use the callable passed at creation.
        toggle.bind('<Button-1>',lambda e:expand());toggle.bind('<Return>',lambda e:expand());toggle.bind('<space>',lambda e:expand())
        entry(advanced,'increase','Increase monthly contributions each year (%)')
        if kind=='retirement_employer':
            entry(advanced,'employer','Employer contribution per month ($)')
            salary=tk.StringVar();pct=tk.StringVar(value=self.state.get('financial',{}).get('benefits',{}).get('current_retirement_contribution',0))
            self.label('Payroll helper: gross annual salary ($), then your contribution (%)',parent=advanced)
            for var in (salary,pct):tk.Entry(advanced,textvariable=var,bg=WHITE,fg=TEXT,insertbackground=TEXT).pack(fill='x',ipady=5,pady=4)
            def derive():
                try:
                    gross=float(salary.get().replace(',',''));percent=float(pct.get())
                    if not math.isfinite(gross) or gross<0 or not math.isfinite(percent) or not 0<=percent<=100:raise ValueError()
                    self.fields['monthly'].set(str(round(gross*percent/1200,2)));self.error.config(text='Payroll contribution filled in.')
                except ValueError:self.error.config(text='Enter a valid salary and a percentage from 0 to 100.')
            Button(advanced,text='Use payroll amount',command=derive).pack(anchor='w',pady=6)
        else:self.fields['employer'].set('0')
        if kind=='ira':
            self.label('IRA contributions require an income and annual-limit check. Your account label alone does not tell us whether it is Roth or traditional.')
            def checked(raw,room):
                self.ira_check=(raw,room)
                self.error.config(text=f'2026 additional direct contribution room: ${room:,.2f}. Annualized monthly plan must fit this amount.')
            from ira_rules import open_check
            Button(self.body,text='Check IRA eligibility & limit',command=lambda:open_check(self.body.winfo_toplevel(),self.state,checked)).pack(anchor='w',pady=8)
        self.error=self.label('')
        actions=tk.Frame(self.body,bg=BG);actions.pack(fill='x',pady=12)
        Button(actions,text='Back',command=self.choose).pack(side='left')
        Button(actions,text='See my projection',command=self.results).pack(side='right')
    def results(self):
        try:
            if not self.fields['monthly'].get().strip():raise ValueError('Enter a monthly contribution; 0 is allowed.')
            values={k:float(v.get().replace(',','').replace('$','').replace('%','')) for k,v in self.fields.items()}
            if self.chosen['type']=='ira':
                if self.ira_check is None:raise ValueError('Complete the IRA eligibility check before projecting contributions.')
                raw,room=self.ira_check
                if values['monthly']*12>room+0.001:raise ValueError(f'Annualized contributions exceed your 2026 remaining room (${room:,.2f}). Reduce the monthly amount.')
                from ira_rules import remaining_ira
                full=remaining_ira(**dict(raw,traditional=0,roth=0))
                if values['monthly']*12*max(1,(1+values['increase']/100)**max(0,int(values['years'])-1))>full+0.001:
                    raise ValueError('Later annual contributions exceed the current-rule limit. Reduce the annual increase or monthly amount. Future rules and income must be checked again.')
            rows=project(**values)
        except (ValueError,OverflowError) as exc:self.error.config(text=str(exc));return
        self.clear('3. Where this plan could take you')
        if self.chosen['type']=='ira':self.label('IRA eligibility checked against your supplied 2026 facts. Future-year income and limits are unknown; this is a constant-current-rules illustration, not future eligibility approval.')
        self.label(f"${rows[-1][3]:,.0f} in {int(values['years'])} years",True)
        self.label(f"Starting money + additions: ${rows[-1][1]:,.0f}    Modeled growth/loss: ${rows[-1][2]:,.0f}")
        self.label(f"${values['monthly']:,.2f}/month • {values['annual']:g}% annual return assumption")
        self.label('Illustration in future dollars. Taxes, fees, inflation and withdrawals are excluded. Market losses and changing returns are possible.')
        note=self.return_notes[self.chosen['key']].get().strip()
        if note:self.label('Your investment / history note (not verified): '+note)
        if self.chosen['type'] in ('brokerage','ira','retirement_employer','529','hsa'):
            self.label('How sensitive is the outcome to returns?',True)
            comparison=tk.Frame(self.body,bg=BG);comparison.pack(fill='x',pady=8)
            for index,(title,rate) in enumerate([('Lower return',max(-99,values['annual']-2)),('Your assumption',values['annual']),('Higher return',min(100,values['annual']+2))]):
                end=project(**dict(values,annual=rate))[-1][3]
                card=tk.Frame(comparison,bg=WHITE);card.grid(row=0,column=index,sticky='nsew',padx=4)
                from ui import copy_label
                copy_label(card,f'{title} · {rate:g}%',color=MUTED).pack_configure(padx=12)
                copy_label(card,f'${end:,.0f}',18,True).pack_configure(padx=12,pady=12)
                comparison.columnconfigure(index,weight=1,uniform='outcome')
            self.label('These are fixed-rate examples, not a probability range or a worst-case estimate. Actual results can fall outside all three.')
        free=self.state.get('financial_metrics',{}).get('monthly_free_cash_flow')
        if free is not None and self.chosen['type']!='retirement_employer' and values['monthly']>max(0,free):
            self.label('This hypothetical contribution exceeds your current recorded monthly surplus. Update your budget before adopting it.')
        if self.goal:
            gap=max(0,self.goal['target_amount']-rows[-1][3])
            self.label(f"{self.goal['name']}: ${self.goal['target_amount']:,.0f} target; ${gap:,.0f} gap at this horizon. Assumes the whole account is dedicated to this goal.")
            if self.goal.get('target_date'):self.label('Goal date: '+self.goal['target_date']+'. The table uses whole years from today.')
        from visual_charts import projection_chart
        projection_chart(self.body,rows,values['initial'])
        if values['annual']==0:self.label('0% growth selected: this view shows your starting balance and contributions only. Adjust your annual return to test investment growth.')
        details=tk.Frame(self.body,bg=BG)
        toggle=Button(self.body,text='View year-by-year numbers & assumptions',command=lambda:None)
        toggle.pack(anchor='w',pady=6)
        def expand():
            if details.winfo_manager():details.pack_forget();toggle.config(text='View year-by-year numbers & assumptions')
            else:details.pack(fill='x',after=toggle);toggle.config(text='Hide details')
        for event in ('<Button-1>','<Return>','<space>'):toggle.bind(event,lambda e:expand())
        holder=tk.Frame(details,bg=BG);holder.pack(fill='x',pady=8)
        table=ttk.Treeview(holder,columns=('year','add','balance'),show='headings',height=6)
        for k,t in [('year','Year'),('add','Added that year'),('balance','Balance')]:table.heading(k,text=t);table.column(k,width=180,anchor='e')
        previous=values['initial']
        for year,paid,gain,end in rows:
            addition=paid-previous;previous=paid
            if year<=5 or year%5==0 or year==int(values['years']):table.insert('', 'end',values=(year,f'${addition:,.0f}',f'${end:,.0f}'))
        table.pack(side='left',fill='x',expand=True)
        sb=ttk.Scrollbar(holder,command=table.yview);sb.pack(side='right',fill='y');table.configure(yscrollcommand=sb.set)
        self.label('Fixed annual return, monthly compounding, month-end additions. Contribution increases happen each year. Taxes, fees, inflation and withdrawals are excluded. Future eligibility and contribution limits need rechecking.',parent=details)
        status=self.label('')
        def save():
            from copy import deepcopy
            from storage import save_state
            import sqlite3
            draft=deepcopy(self.state);draft.setdefault('forecast_plans',{})[self.chosen['key']]=values
            draft.setdefault('forecast_return_notes',{})[self.chosen['key']]=self.return_notes[self.chosen['key']].get().strip()
            if self.chosen['type']=='ira':draft['ira_check_inputs']=self.ira_check[0]
            try:save_state(draft)
            except sqlite3.Error as exc:status.config(text=f'Could not save: {exc}');return
            self.state.update(draft);status.config(text='Scenario saved. Your actual balances are unchanged.')
        buttons=tk.Frame(self.body,bg=BG);buttons.pack(fill='x',pady=12)
        Button(buttons,text='Adjust my numbers',command=self.numbers).pack(side='left')
        Button(buttons,text='Save scenario',command=save).pack(side='right')
