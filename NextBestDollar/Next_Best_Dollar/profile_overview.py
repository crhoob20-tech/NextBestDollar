import tkinter as tk
from financial import normalize_financial
from dashboard_charts import snapshot
from ui import BG,WHITE,TEXT,MUTED
COLORS=['#2F6BFF','#0F9D6A','#E8A13D','#875CD1','#E46F79','#51A6B9','#8795AA']
def composition(values):
    items=sorted(((k.replace('_',' ').title(),v) for k,v in values.items() if isinstance(v,(int,float)) and v>0),key=lambda x:x[1],reverse=True)
    return items if len(items)<=7 else items[:6]+[('Other categories',sum(v for _,v in items[6:]))]
def pie(parent,title,values):
    canvas=tk.Canvas(parent,bg=WHITE,height=290,highlightthickness=0)
    canvas.pack(fill='both',expand=True,padx=6,pady=6)
    items=composition(values);total=sum(v for _,v in items)
    def draw(event=None):
        canvas.delete('all');width=max(canvas.winfo_width(),260)
        canvas.create_text(15,20,text=title,anchor='w',fill=TEXT,font=('Helvetica',12,'bold'))
        if total==0:canvas.create_text(15,65,text='No positive amounts recorded.',anchor='w',fill=MUTED);return
        start=90
        for i,(label,value) in enumerate(items):
            angle=value/total*360
            if len(items)==1:canvas.create_oval(16,45,136,165,fill=COLORS[i],outline=WHITE)
            else:canvas.create_arc(16,45,136,165,start=start,extent=-angle,fill=COLORS[i],outline=WHITE)
            start-=angle
        canvas.create_oval(40,69,112,141,fill=WHITE,outline=WHITE)
        canvas.create_text(152,80,text=f'${total:,.0f}/month',anchor='w',fill=TEXT,font=('Helvetica',12,'bold'))
        for i,(label,value) in enumerate(items):
            y=185+i*22
            canvas.create_rectangle(16,y-4,24,y+4,fill=COLORS[i],outline='')
            canvas.create_text(32,y,text=f'{label}: ${value:,.0f} ({value/total:.0%})',anchor='w',fill=TEXT,font=('Helvetica',9))
        canvas.config(height=200+len(items)*22)
    canvas.bind('<Configure>',draw)
def build_overview(parent,state):
    from tkinter import ttk
    from ui import scroll_page, panel, copy_label
    frame=scroll_page(parent)
    cash,investments,debt,net=snapshot(state)
    hero=panel(frame)
    copy_label(hero,'YOUR MONEY AT A GLANCE',10,True,color='#2F6BFF')
    copy_label(hero,f'${net:,.0f}',30,True)
    copy_label(hero,'Tracked net worth · what you own minus what you owe',color=MUTED)
    copy_label(hero,'Recorded cash and investments, less debt. Property and unrecorded assets are not included.',color=MUTED)
    personal=state.get('personal',{})
    if personal:
        context=panel(frame)
        copy_label(context,'Built around your life',15,True)
        facts=[]
        for key,label in [('employment_status','Work'),('dependents','Dependents'),('financial_experience','Money experience')]:
            if str(personal.get(key,'')):facts.append(f"{label}: {personal[key]}")
        copy_label(context,'  ·  '.join(facts) or 'Your personal details are saved in your profile.',color=MUTED)
        copy_label(context,'Money habits questionnaire: '+('complete' if state.get('behavioral_complete') else 'ready to complete in Edit your information'),color=MUTED)
    if not state.get('financial_complete'):
        copy_label(frame,'Add your financial facts to fill in your cash flow, cash cushion and balance breakdown.',color=MUTED)
        return
    f=normalize_financial(state.get('financial',{}))
    income=sum(f['income'].values());spend=sum(f['spending'].values())
    minimums=sum(d.get('minimum_payment',0) for d in f['debt'])
    outflow=spend+minimums;left=income-outflow
    card=panel(frame)
    copy_label(card,'A typical month',16,True)
    copy_label(card,f'${left:,.0f} '+('left to assign' if left>=0 else 'cash-flow shortfall'),22,True,color='#0F9D6A' if left>=0 else '#D64545')
    copy_label(card,f'${income:,.0f} take-home income − ${spend:,.0f} living costs − ${minimums:,.0f} debt minimums',color=MUTED)
    bars=tk.Canvas(card,bg=WHITE,height=145,highlightthickness=0);bars.pack(fill='x',pady=8)
    def draw(event=None):
        bars.delete('all');width=max(320,bars.winfo_width());maximum=max(income,outflow,1)
        for i,(name,value,color) in enumerate([('Income',income,'#2F6BFF'),('Living costs',spend,'#8795AA'),('Debt minimums',minimums,'#E8A13D')]):
            y=24+i*44
            bars.create_text(0,y,text=name,anchor='w',fill=TEXT)
            bars.create_rectangle(115,y-9,115+max(0,width-225)*value/maximum,y+9,fill=color,outline='')
            bars.create_text(width-4,y,text=f'${value:,.0f}',anchor='e',fill=TEXT)
    bars.bind('<Configure>',draw)
    cushion=panel(frame)
    reserve=f['accounts'].get('emergency_fund',0)
    copy_label(cushion,'Your emergency cushion',16,True)
    copy_label(cushion,f'{reserve/outflow:.1f} months of recorded costs' if outflow>0 else 'Add monthly costs to measure coverage',22,True)
    copy_label(cushion,f'${reserve:,.0f} designated for emergencies. This is part of your cash, not an additional account.',color=MUTED)
    if outflow>0:
        ttk.Progressbar(cushion,maximum=3*outflow,value=min(reserve,3*outflow)).pack(fill='x',pady=12)
        copy_label(cushion,f'Illustrative 3-month target: ${3*outflow:,.0f} · ${max(0,3*outflow-reserve):,.0f} remaining. Your needs may differ.',color=MUTED)
    holdings=panel(frame)
    copy_label(holdings,'What you own and owe',16,True)
    for label,amount in [('Cash',cash),('Investments',investments),('Debt',debt)]:
        copy_label(holdings,f'{label}   ${amount:,.0f}',14,True)
    charts=tk.Frame(frame,bg=BG);charts.pack(fill='x',pady=8)
    for index,(title,values) in enumerate([('Income sources',f['income']),('Living spending',f['spending'])]):
        box=tk.Frame(charts,bg=WHITE);box.grid(row=0,column=index,sticky='nsew',padx=(0,8) if index==0 else (8,0))
        charts.columnconfigure(index,weight=1,uniform='profile')
        pie(box,title,values)
    copy_label(frame,'These are your saved estimates, not transaction history. Update your finances when income, bills or balances change.',color=MUTED)
