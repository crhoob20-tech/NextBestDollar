import tkinter as tk
from ui import WHITE,TEXT,MUTED

def milestones(rows):return [row for row in rows if row[0]<=5 or row[0]%5==0 or row[0]==rows[-1][0]]

def projection_chart(parent,rows,initial):
    canvas=tk.Canvas(parent,height=230,bg=WHITE,highlightthickness=0);canvas.pack(fill='x',pady=10)
    def draw(event=None):
        canvas.delete('all');w=max(420,canvas.winfo_width());h=230;left=80;right=w-22;top=32;bottom=192
        maximum=max([r[3] for r in rows]+[r[1] for r in rows]+[initial,1])
        canvas.create_text(left,14,text='Projected balance (blue) and money added (green)',anchor='w',fill=TEXT)
        canvas.create_text(left-8,top,text=f'${maximum:,.0f}',anchor='e',fill=MUTED)
        canvas.create_text(left-8,bottom,text='$0',anchor='e',fill=MUTED)
        canvas.create_line(left,top,left,bottom,right,bottom,fill='#D4DCE7')
        for column,color in [(3,'#2F6BFF'),(1,'#0F9D6A')]:
            coords=[left,bottom-initial/maximum*(bottom-top)]
            for row in rows:coords.extend([left+(right-left)*row[0]/rows[-1][0],bottom-row[column]/maximum*(bottom-top)])
            canvas.create_line(*coords,fill=color,width=3)
        canvas.create_text(left,bottom+18,text='Today',anchor='w',fill=MUTED)
        canvas.create_text(right,bottom+18,text=f"Year {rows[-1][0]}",anchor='e',fill=MUTED)
    canvas.bind('<Configure>',draw)
    return canvas

def flow_chart(parent,state):
    from financial import normalize_financial
    f=normalize_financial(state.get('financial',{}));income=sum(f['income'].values());out=sum(f['spending'].values())+sum(d.get('minimum_payment',0) for d in f['debt'])
    canvas=tk.Canvas(parent,height=110,bg=WHITE,highlightthickness=0);canvas.pack(fill='x',padx=12,pady=8)
    def draw(event=None):
        canvas.delete('all');w=max(400,canvas.winfo_width());maximum=max(income,out,1)
        for i,(label,value,color) in enumerate([('Monthly inflows',income,'#2F6BFF'),('Monthly outflows',out,'#D64545')]):
            y=28+i*44
            canvas.create_text(5,y,text=label,anchor='w',fill=TEXT)
            canvas.create_rectangle(135,y-12,135+(w-265)*value/maximum,y+12,fill=color,outline='')
            canvas.create_text(w-8,y,text=f'${value:,.0f}',anchor='e',fill=TEXT)
    canvas.bind('<Configure>',draw)
