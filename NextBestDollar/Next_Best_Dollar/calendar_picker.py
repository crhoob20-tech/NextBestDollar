"""Compact date chip with a month calendar; the entire chip opens the picker."""
import tkinter as tk
from tkinter import ttk
from datetime import date,datetime
import calendar
from ui import Button,BG,WHITE,TEXT,BLUE,MUTED
class DatePicker(tk.Frame):
    def __init__(self,parent,variable,fmt='%Y-%m-%d',birth=False):
        super().__init__(parent,bg=BG)
        self.variable=variable;self.fmt=fmt;self.birth=birth;self.popup=None
        self.chip=Button(self,text='',command=self.open,bg='#E7EFFF',fg=BLUE)
        self.chip.pack(anchor='w',pady=4)
        self.trace=variable.trace_add('write',self.refresh)
        self.bind('<Destroy>',self.cleanup)
        self.refresh()
    def cleanup(self,event):
        if event.widget is self:self.variable.trace_remove('write',self.trace)
    def refresh(self,*args):
        try:label=datetime.strptime(self.variable.get(),self.fmt).strftime('%b %d, %Y')
        except ValueError:label='Choose a date'
        self.chip.config(text='▦  '+label+'  ▾')
    def open(self):
        if self.popup and self.popup.winfo_exists():self.popup.lift();return
        try:current=datetime.strptime(self.variable.get(),self.fmt).date()
        except ValueError:current=date(date.today().year-21,1,1) if self.birth else date.today()
        owner=self.winfo_toplevel();previous=self.grab_current()
        window=tk.Toplevel(owner);self.popup=window;window.title('Choose date');window.configure(bg=WHITE);window.resizable(False,False);window.transient(owner);window.grab_set()
        year=tk.StringVar(value=str(current.year));month=tk.StringVar(value=calendar.month_name[current.month])
        header=tk.Frame(window,bg=WHITE);header.pack(fill='x',padx=16,pady=(16,8))
        now=date.today().year
        def close():
            window.destroy();self.popup=None
            if previous and previous.winfo_exists():previous.grab_set()
        def choose(day):
            chosen=date(int(year.get()),list(calendar.month_name).index(month.get()),day)
            if self.birth and chosen>date.today():return
            self.variable.set(chosen.strftime(self.fmt));close()
        def move(offset):
            y=int(year.get());m=list(calendar.month_name).index(month.get())+offset
            if m==0:y-=1;m=12
            if m==13:y+=1;m=1
            if not 1<=y<=9999:return
            year.set(str(y));month.set(calendar.month_name[m]);draw()
        Button(header,text='‹',command=lambda:move(-1),bg=WHITE,fg=TEXT).pack(side='left')
        m=ttk.Combobox(header,textvariable=month,values=list(calendar.month_name)[1:],state='readonly',width=10);m.pack(side='left',padx=4)
        y=ttk.Combobox(header,textvariable=year,values=list(range(now-120,now+1 if self.birth else now+81)),state='readonly',width=5);y.pack(side='left',padx=4)
        Button(header,text='›',command=lambda:move(1),bg=WHITE,fg=TEXT).pack(side='left')
        days=tk.Frame(window,bg=WHITE);days.pack(padx=18,pady=8)
        def draw(event=None):
            for child in days.winfo_children():child.destroy()
            for col,label in enumerate(('M','T','W','T','F','S','S')):tk.Label(days,text=label,bg=WHITE,fg=MUTED).grid(row=0,column=col,pady=8)
            for row,week in enumerate(calendar.monthcalendar(int(year.get()),list(calendar.month_name).index(month.get())),1):
                for col,day in enumerate(week):
                    if not day:continue
                    selected=date(int(year.get()),list(calendar.month_name).index(month.get()),day)
                    if self.birth and selected>date.today():
                        tk.Label(days,text=day,bg=WHITE,fg='#C2CAD5',width=4).grid(row=row,column=col,pady=5);continue
                    button=Button(days,text=str(day),command=lambda d=day:choose(d),bg=BLUE if selected==current else WHITE,fg=WHITE if selected==current else TEXT)
                    button.config(padx=8,pady=7,width=2);button.grid(row=row,column=col,padx=1,pady=2)
        m.bind('<<ComboboxSelected>>',draw);y.bind('<<ComboboxSelected>>',draw);draw()
        if not self.birth:Button(window,text='Clear date',command=lambda:(self.variable.set(''),close()),bg=WHITE,fg=MUTED).pack(pady=8)
        window.bind('<Escape>',lambda event:close());window.protocol('WM_DELETE_WINDOW',close)
