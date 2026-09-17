"""Editable milestone goals. Targets are user estimates, not recommendations."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from uuid import uuid4
from copy import deepcopy
import math
from storage import save_state
from ui import Button, style_widgets
import sqlite3

TYPES = ['Pay off debt', 'Buy a home', 'Buy a car', 'Invest', 'Vacation', 'Children / family', 'Emergency fund', 'Other milestone']
HELP = {
    'Emergency fund': 'Choose a cash reserve for unexpected expenses. Set a target that suits your circumstances.',
    'Pay off debt': 'Set the debt amount you want to pay off and how much you have paid toward this goal. Debt records are managed separately.',
    'Buy a home': 'Use your cash target for a down payment, closing costs and moving expenses.',
    'Buy a car': 'Use your cash purchase or down-payment target, including estimated taxes and fees.',
    'Invest': 'Set an investment contribution milestone. Progress is the amount you have contributed toward it.',
    'Vacation': 'Estimate the trip budget, including transport, lodging, food and activities.',
    'Children / family': 'Set a reserve for planned family costs, such as parental leave, childcare or education.',
    'Other milestone': 'Choose a specific financial milestone and the amount you want to set aside.'
}
BG='#F2F5F9'; WHITE='#FFFFFF'; TEXT='#1A2233'; BLUE='#2F6BFF'; MUTED='#596579'


def validate_goal(values):
    title = str(values.get('name', '')).strip()
    kind = values.get('type')
    if not title:
        raise ValueError('Give your goal a name.')
    if kind not in TYPES:
        raise ValueError('Select a goal type.')
    amounts = {}
    for key in ('target_amount', 'progress_amount'):
        raw = str(values.get(key, '')).strip().replace('$', '').replace(',', '')
        try:
            amount = float(raw or ('0' if key == 'progress_amount' else 'nan'))
        except ValueError:
            raise ValueError('Enter valid dollar amounts.')
        if not math.isfinite(amount) or amount < 0:
            raise ValueError('Amounts must be finite, nonnegative numbers.')
        amounts[key] = round(amount, 2)
    if amounts['target_amount'] <= 0:
        raise ValueError('The target amount must be greater than zero.')
    due = str(values.get('target_date', '')).strip()
    if due:
        try:
            date.fromisoformat(due)
        except ValueError:
            raise ValueError('Enter the date as YYYY-MM-DD, or leave it blank.')
    priority = values.get('priority', 'Medium')
    if priority not in ('High', 'Medium', 'Low'):
        raise ValueError('Choose High, Medium or Low priority.')
    return dict(name=title, type=kind, **amounts, target_date=due, priority=priority,
                notes=str(values.get('notes', '')).strip())


def goal_status(goal):
    target = goal.get('target_amount', 0)
    progress = goal.get('progress_amount', 0)
    remaining = max(0, target-progress)
    due = goal.get('target_date', '')
    if remaining == 0:
        return 'Complete'
    if due and date.fromisoformat(due) < date.today():
        return 'Target date passed'
    return 'In progress'


def build_goals(parent, state, refresh):
    top = tk.Frame(parent, bg=BG)
    top.pack(fill='x', padx=26, pady=14)
    tk.Label(top, text='Your big milestones', font=('Helvetica', 18, 'bold'), bg=BG, fg=TEXT).pack(side='left')
    Button(top, text='+ Add goal', command=lambda: GoalEditor(parent.winfo_toplevel(), state, refresh), bg=BLUE, fg=WHITE).pack(side='right')
    tk.Label(parent, text='Choose your own targets. Progress is entered manually; count money toward only one goal at a time.',
             bg=BG, fg=MUTED, wraplength=760, justify='left').pack(anchor='w', padx=26)
    container=tk.Frame(parent, bg=BG);container.pack(fill='both', expand=True, padx=26, pady=14)
    canvas=tk.Canvas(container,bg=BG,highlightthickness=0)
    bar=ttk.Scrollbar(container,orient='vertical',command=canvas.yview)
    body=tk.Frame(canvas,bg=BG)
    win=canvas.create_window((0,0),window=body,anchor='nw')
    body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>',lambda e:canvas.itemconfigure(win,width=e.width))
    canvas.configure(yscrollcommand=bar.set)
    bar.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
    from suggestions import suggested_goals
    suggestions = suggested_goals(state)
    if suggestions:
        tk.Label(body,text='Suggested for you',font=('Helvetica',14,'bold'),bg=BG,fg=TEXT).pack(anchor='w',pady=(8,6))
        for suggestion in suggestions:
            card=tk.Frame(body,bg=WHITE,highlightbackground='#D4DCE7',highlightthickness=1)
            card.pack(fill='x',pady=5)
            tk.Label(card,text=suggestion['name'],font=('Helvetica',12,'bold'),bg=WHITE,fg=TEXT).pack(anchor='w',padx=16,pady=(12,4))
            tk.Label(card,text=suggestion['reason'],bg=WHITE,fg=MUTED,wraplength=680,justify='left').pack(anchor='w',padx=16,pady=4)
            Button(card,text='Review goal',command=lambda p=suggestion: GoalEditor(parent.winfo_toplevel(),state,refresh,preset=p)).pack(anchor='w',padx=16,pady=(4,12))
    tk.Label(body,text='Your saved goals',font=('Helvetica',14,'bold'),bg=BG,fg=TEXT).pack(anchor='w',pady=(16,6))
    goals=state.get('goals',[])
    if not goals:
        tk.Label(body,text='No goals yet. Add a milestone to get started.',bg=BG,fg=MUTED).pack(anchor='w',pady=20)
    def remove(index):
        if messagebox.askyesno('Remove goal?', 'Remove this goal and its saved progress?', parent=parent.winfo_toplevel()):
            draft=deepcopy(state)
            draft['goals'].pop(index)
            save_state(draft)
            state.update(draft)
            refresh()
    for index, goal in enumerate(goals):
        card=tk.Frame(body,bg=WHITE,highlightbackground='#D4DCE7',highlightthickness=1)
        card.pack(fill='x',pady=6)
        tk.Label(card,text=goal['name'],font=('Helvetica',14,'bold'),bg=WHITE,fg=TEXT).pack(anchor='w',padx=16,pady=(14,4))
        tk.Label(card,text=f"{goal['type']}  •  {goal['priority']} priority  •  {goal_status(goal)}",bg=WHITE,fg=MUTED).pack(anchor='w',padx=16)
        remaining=max(0,goal['target_amount']-goal['progress_amount'])
        summary=f"${goal['progress_amount']:,.2f} of ${goal['target_amount']:,.2f}  •  ${remaining:,.2f} remaining"
        if goal.get('target_date'):
            summary+=f"  •  Target: {goal['target_date']}"
        tk.Label(card,text=summary,bg=WHITE,fg=TEXT,wraplength=680,justify='left').pack(anchor='w',padx=16,pady=8)
        ttk.Progressbar(card,maximum=max(goal['target_amount'],1),value=min(goal['progress_amount'],goal['target_amount'])).pack(fill='x',padx=16,pady=5)
        if goal.get('notes'):
            tk.Label(card,text=goal['notes'],bg=WHITE,fg=MUTED,wraplength=680,justify='left').pack(anchor='w',padx=16,pady=5)
        actions=tk.Frame(card,bg=WHITE);actions.pack(fill='x',padx=16,pady=(5,12))
        Button(actions,text='Edit goal / progress',command=lambda i=index:GoalEditor(parent.winfo_toplevel(),state,refresh,i)).pack(side='left')
        Button(actions,text='Remove',command=lambda i=index:remove(i)).pack(side='left',padx=8)


class GoalEditor(tk.Toplevel):
    def __init__(self,parent,state,refresh,index=None,preset=None):
        super().__init__(parent)
        style_widgets(self)
        self.title('Edit goal' if index is not None else 'Add a milestone')
        self.geometry('650x740');self.configure(bg=BG);self.transient(parent);self.grab_set()
        existing=deepcopy(state.get('goals',[])[index]) if index is not None else deepcopy(preset or {})
        shell=tk.Frame(self,bg=BG);shell.pack(fill='both',expand=True,padx=26,pady=18)
        canvas=tk.Canvas(shell,bg=BG,highlightthickness=0)
        bar=ttk.Scrollbar(shell,orient='vertical',command=canvas.yview)
        body=tk.Frame(canvas,bg=BG)
        win=canvas.create_window((0,0),window=body,anchor='nw')
        body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<Configure>',lambda e:canvas.itemconfigure(win,width=e.width))
        canvas.configure(yscrollcommand=bar.set)
        bar.pack(side='right',fill='y');canvas.pack(side='left',fill='both',expand=True)
        values={}
        tk.Label(body,text='Goal type',bg=BG,fg=TEXT).pack(anchor='w')
        kind=tk.StringVar(value=existing.get('type',TYPES[0]));values['type']=kind
        combo=ttk.Combobox(body,textvariable=kind,values=TYPES,state='readonly');combo.pack(fill='x',pady=(4,8))
        helper=tk.Label(body,bg=BG,fg=MUTED,wraplength=580,justify='left');helper.pack(anchor='w',pady=(0,8))
        progress_label=None
        for key,label in [('name','Goal name'),('target_amount','Target amount ($)'),('progress_amount','Progress so far ($)'),('target_date','Target date (optional)')]:
            lbl=tk.Label(body,text=label,bg=BG,fg=TEXT);lbl.pack(anchor='w',pady=(8,3))
            if key=='progress_amount':progress_label=lbl
            var=tk.StringVar(value=existing.get(key,''));values[key]=var
            if key=='target_date':
                from calendar_picker import DatePicker
                DatePicker(body,var).pack(fill='x')
            else:
                tk.Entry(body,textvariable=var,bg=WHITE,fg=TEXT,insertbackground=TEXT).pack(fill='x',ipady=5)
        if index is None and not values['name'].get():
            values['name'].set(kind.get())
        def update_type(event=None):
            helper.config(text=HELP[kind.get()])
            progress_label.config(text='Amount already paid toward this goal ($)' if kind.get()=='Pay off debt' else 'Amount contributed toward this goal ($)' if kind.get()=='Invest' else 'Amount already saved for this goal ($)')
            if index is None and values['name'].get() in TYPES:
                values['name'].set(kind.get())
        combo.bind('<<ComboboxSelected>>',update_type);update_type()
        tk.Label(body,text='Priority',bg=BG,fg=TEXT).pack(anchor='w',pady=(8,3))
        priority=tk.StringVar(value=existing.get('priority','Medium'));values['priority']=priority
        ttk.Combobox(body,textvariable=priority,values=['High','Medium','Low'],state='readonly').pack(fill='x')
        tk.Label(body,text='Notes (optional)',bg=BG,fg=TEXT).pack(anchor='w',pady=(8,3))
        notes=tk.Text(body,height=3,bg=WHITE,fg=TEXT,insertbackground=TEXT);notes.pack(fill='x');notes.insert('1.0',existing.get('notes',''))
        error=tk.Label(body,text='',bg=BG,fg='#D64545',wraplength=580);error.pack(anchor='w',pady=8)
        def save():
            try:
                raw={key:var.get() for key,var in values.items()};raw['notes']=notes.get('1.0','end').strip()
                goal=validate_goal(raw);goal['id']=existing.get('id',str(uuid4()))
                draft=deepcopy(state);draft.setdefault('goals',[])
                if index is None:draft['goals'].append(goal)
                else:draft['goals'][index]=goal
                save_state(draft)
            except (ValueError,OSError,sqlite3.Error) as exc:
                error.config(text=str(exc));return
            state.update(draft);self.destroy();refresh()
        actions=tk.Frame(body,bg=BG);actions.pack(fill='x',pady=5)
        Button(actions,text='Cancel',command=self.destroy).pack(side='left')
        Button(actions,text='Save goal',command=save,bg=BLUE,fg=WHITE).pack(side='right')
