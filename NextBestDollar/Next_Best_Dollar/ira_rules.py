"""2026 direct IRA contribution screen. IRS 590-A and 2026 cost-of-living notice.
Sources: https://www.irs.gov/publications/p590a
https://www.irs.gov/newsroom/401k-limit-increases-to-24500-for-2026-ira-limit-increases-to-7500
No rollovers, conversions, special compensation or spousal-IRA calculations.
"""
import math
STATUSES=['Single / head of household','Married filing jointly / surviving spouse','Married separately; lived apart all year','Married separately; lived together']
def remaining_ira(kind,age,compensation,magi,status,traditional,roth,year=2026):
    if year!=2026:raise ValueError('IRA rules are verified for 2026 only. Update the tax-year rules before checking another year.')
    if kind not in ('Roth IRA','Traditional IRA') or status not in STATUSES:raise ValueError('Choose IRA type and tax filing status.')
    if not all(math.isfinite(v) and v>=0 for v in (age,compensation,magi,traditional,roth)) or age>120 or age!=int(age):raise ValueError('Enter valid age and nonnegative dollar amounts.')
    base=min(8600 if age>=50 else 7500,compensation)
    combined=max(0,base-traditional-roth)
    if kind=='Traditional IRA':return combined
    low,high=(242000,252000) if status==STATUSES[1] else (0,10000) if status==STATUSES[3] else (153000,168000)
    if magi>=high:return 0
    reduced=base
    if magi>low:
        reduced=max(200,math.ceil((base*(1-(magi-low)/(high-low)))/10)*10)
    return max(0,min(reduced-roth,combined))

def open_check(parent,state,callback):
    import tkinter as tk
    from tkinter import ttk
    from datetime import date
    from ui import Button,BG,WHITE,TEXT
    import webbrowser
    window=tk.Toplevel(parent);window.title('IRA contribution check');window.geometry('630x740');window.configure(bg=BG);window.transient(parent);window.grab_set()
    saved=state.get('ira_check_inputs',{})
    tk.Label(window,text='2026 IRA contribution check',bg=BG,fg=TEXT,font=('Helvetica',16,'bold')).pack(pady=12)
    tk.Label(window,text='Use tax-year amounts. MAGI is modified adjusted gross income, not salary. This check covers ordinary direct contributions; spousal IRA and special compensation cases need separate review.',bg=BG,fg=TEXT,wraplength=570,justify='left').pack(padx=20)
    variables={}
    for key,label,options in [('kind','Account tax type',['Roth IRA','Traditional IRA']),('status','Filing status',STATUSES)]:
        tk.Label(window,text=label,bg=BG,fg=TEXT).pack(anchor='w',padx=20,pady=(8,2))
        var=tk.StringVar(value=saved.get(key,''));variables[key]=var
        ttk.Combobox(window,textvariable=var,values=options,state='readonly').pack(fill='x',padx=20)
    age=''
    try:age=2026-date.fromisoformat(state.get('personal',{})['date_of_birth']).year
    except (KeyError,ValueError):pass
    for key,label,default in [('age','Age at the end of 2026',age),('compensation','Your eligible taxable compensation in 2026 ($)',''),('magi','2026 MAGI for Roth purposes ($)',''),('traditional','Already contributed to all traditional IRAs for 2026 ($)',''),('roth','Already contributed to all Roth IRAs for 2026 ($)','')]:
        tk.Label(window,text=label,bg=BG,fg=TEXT).pack(anchor='w',padx=20,pady=(8,2))
        var=tk.StringVar(value=saved.get(key,default));variables[key]=var
        tk.Entry(window,textvariable=var,bg=WHITE,fg=TEXT,insertbackground=TEXT).pack(fill='x',padx=20,ipady=4)
    error=tk.Label(window,text='',bg=BG,fg='#D64545',wraplength=560);error.pack(pady=8)
    def accept():
        try:
            raw={k:v.get().strip() for k,v in variables.items()}
            if any(v=='' for v in raw.values()):raise ValueError('Fill each field; enter 0 where appropriate.')
            for k in ('age','compensation','magi','traditional','roth'):raw[k]=float(raw[k].replace(',','').replace('$',''))
            room=remaining_ira(**raw,year=date.today().year)
        except ValueError as exc:error.config(text=str(exc));return
        callback(raw,room);window.destroy()
    Button(window,text='Use this eligibility check',command=accept).pack(pady=8)
    Button(window,text='Open IRS rules',command=lambda:webbrowser.open('https://www.irs.gov/publications/p590a')).pack(pady=4)
