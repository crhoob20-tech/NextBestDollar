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
        canvas.create_text(152,80,text=f'${total:,.0f}/month',anchor='w',fill=TEXT,font=('Helvetica',12,'bold'))
        for i,(label,value) in enumerate(items):
            y=185+i*22
            canvas.create_rectangle(16,y-4,24,y+4,fill=COLORS[i],outline='')
            canvas.create_text(32,y,text=f'{label}: ${value:,.0f} ({value/total:.0%})',anchor='w',fill=TEXT,font=('Helvetica',9))
        canvas.config(height=200+len(items)*22)
    canvas.bind('<Configure>',draw)
def build_overview(parent,state):
    frame=tk.Frame(parent,bg=BG);frame.pack(fill='both',expand=True,padx=18,pady=16)
    cash,investments,debt,net=snapshot(state)
    tk.Label(frame,text=f'Tracked net worth: ${net:,.0f}',font=('Helvetica',20,'bold'),bg=BG,fg=TEXT).pack(anchor='w',pady=8)
    tk.Label(frame,text=f'Cash ${cash:,.0f}   Investments ${investments:,.0f}   Debt ${debt:,.0f}',bg=BG,fg=MUTED).pack(anchor='w')
    tk.Label(frame,text='Includes recorded accounts and debts; excludes unrecorded assets.',bg=BG,fg=MUTED).pack(anchor='w',pady=(3,12))
    if not state.get('financial_complete'):
        tk.Label(frame,text='Complete Financial facts to populate this overview.',bg=BG,fg=MUTED).pack(anchor='w');return
    f=normalize_financial(state.get('financial',{}))
    charts=tk.Frame(frame,bg=BG);charts.pack(fill='x')
    income=tk.Frame(charts,bg=BG);income.pack(side='left',fill='both',expand=True)
    expenses=tk.Frame(charts,bg=BG);expenses.pack(side='left',fill='both',expand=True)
    pie(income,'Income sources',f['income'])
    out=dict(f['spending']);out['debt payments']=sum(d.get('minimum_payment',0) for d in f['debt'])
    pie(expenses,'Where monthly money goes',out)
    tk.Label(frame,text='Weekly / monthly changes need dated transaction history. These charts show your saved typical-month budget, not actual spending trends.',bg=BG,fg=MUTED,wraplength=720,justify='left').pack(anchor='w',pady=14)
