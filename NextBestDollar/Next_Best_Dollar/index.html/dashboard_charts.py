"""Current snapshot charts; no invented historical data."""
import tkinter as tk
from tkinter import ttk
from financial import normalize_financial, CASH_TYPES
from ui import BG,WHITE,TEXT,MUTED,style_widgets

def snapshot(state):
    f=normalize_financial(state.get('financial',{}))
    cash=sum(a['balance'] for a in f['account_entries'] if a['type'] in CASH_TYPES)
    investments=sum(a['balance'] for a in f['account_entries'] if a['type'] not in CASH_TYPES)
    debt=sum(d.get('balance',0) for d in f['debt'])
    return cash,investments,debt,cash+investments-debt

def show_charts(parent,state):
    popup=tk.Toplevel(parent);popup.title('Your financial snapshot');popup.geometry('800x610');popup.minsize(620,520);popup.configure(bg=BG)
    style_widgets(popup)
    cash,investments,debt,net=snapshot(state)
    tk.Label(popup,text=f'Tracked net worth: ${net:,.2f}',font=('Helvetica',22,'bold'),bg=BG,fg=TEXT).pack(anchor='w',padx=26,pady=(22,8))
    tk.Label(popup,text='Recorded cash + investments − debts. Property and other unrecorded assets are excluded.',bg=BG,fg=MUTED,wraplength=710,justify='left').pack(anchor='w',padx=26)
    mode=tk.StringVar(value='Balances')
    choose=ttk.Combobox(popup,textvariable=mode,values=['Balances','Monthly cash flow','Saved projection'],state='readonly');choose.pack(fill='x',padx=26,pady=16)
    plans=list(state.get('forecast_plans',{}).items())
    plan_choice=ttk.Combobox(popup,values=[f"Scenario {i+1}: "+(k.split(':')[2] if k.startswith('saved:') and len(k.split(':'))>2 else k.replace('explore:','').replace('_',' ').title()) for i,(k,v) in enumerate(plans)],state='readonly')
    if plans:plan_choice.current(0)
    plan_choice.pack(fill='x',padx=26,pady=(0,8))
    canvas=tk.Canvas(popup,bg=WHITE,highlightthickness=0);canvas.pack(fill='both',expand=True,padx=26,pady=(0,20))
    def draw(event=None):
        canvas.delete('all');width=max(canvas.winfo_width(),500)
        if not state.get('financial_complete'):
            canvas.create_text(25,40,text='Complete Financial facts to see your snapshot.',anchor='w',fill=TEXT);return
        if mode.get()=='Saved projection':
            if not plans:
                canvas.create_text(25,40,text='Save a scenario in Plan to view it here.',anchor='w',fill=TEXT);return
            from forecasting import project
            try:
                rows=project(**plans[plan_choice.current()][1])
            except (ValueError,TypeError):
                canvas.create_text(25,40,text='Open and resave this scenario in Plan.',anchor='w',fill=TEXT);return
            max_value=max([r[3] for r in rows]+[1]);points=[]
            for row in rows:points.extend([60+(width-100)*row[0]/rows[-1][0],260-200*row[3]/max_value])
            if len(points)>=4:canvas.create_line(*points,fill='#2F6BFF',width=3)
            else:canvas.create_oval(points[0]-4,points[1]-4,points[0]+4,points[1]+4,fill='#2F6BFF')
            canvas.create_text(25,25,text=f'Saved illustration: ${rows[-1][3]:,.0f} at year {rows[-1][0]}',anchor='w',fill=TEXT)
            canvas.create_text(25,300,text='Uses saved assumptions, not live account values.',anchor='w',fill=MUTED)
            return
        if mode.get()=='Balances':
            data=[('Cash',cash,'#2F6BFF'),('Investments',investments,'#0F9D6A'),('Debt',debt,'#D64545')]
        else:
            f=normalize_financial(state.get('financial',{}));income=sum(f['income'].values());spend=sum(f['spending'].values());minimums=sum(d.get('minimum_payment',0) for d in f['debt'])
            data=[('Income',income,'#2F6BFF'),('Living expenses',spend,'#E8A13D'),('Debt payments',minimums,'#D64545')]
            canvas.create_text(24,280,text=f'Monthly surplus / deficit: ${income-spend-minimums:,.2f}',anchor='w',fill=TEXT,font=('Helvetica',12,'bold'))
        maximum=max([v for _,v,_ in data]+[1])
        for i,(label,value,color) in enumerate(data):
            y=36+i*74
            canvas.create_text(24,y,text=label,anchor='w',fill=TEXT,font=('Helvetica',11,'bold'))
            canvas.create_rectangle(160,y-12,160+(width-290)*value/maximum,y+16,fill=color,outline='')
            canvas.create_text(width-18,y,text=f'${value:,.2f}',anchor='e',fill=TEXT,font=('Helvetica',11))
        canvas.create_text(24,320,text='Current saved snapshot',anchor='w',fill=MUTED)
    plan_choice.bind('<<ComboboxSelected>>',draw)
    choose.bind('<<ComboboxSelected>>',draw);canvas.bind('<Configure>',draw)
