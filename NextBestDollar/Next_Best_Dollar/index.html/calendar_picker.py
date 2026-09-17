import tkinter as tk
from tkinter import ttk
from datetime import date,datetime
import calendar
from ui import Button,BG,WHITE,TEXT
class DatePicker(tk.Frame):
    def __init__(self,parent,variable,fmt='%Y-%m-%d',birth=False):
        super().__init__(parent,bg=BG)
        self.variable=variable;self.fmt=fmt;self.birth=birth
        tk.Entry(self,textvariable=variable,state='readonly',readonlybackground=WHITE,fg=TEXT).pack(side='left',fill='x',expand=True,ipady=6)
        Button(self,text='Calendar',command=self.open).pack(side='left',padx=8)
    def open(self):
        try:current=datetime.strptime(self.variable.get(),self.fmt).date()
        except ValueError:current=date(date.today().year-21,1,1) if self.birth else date.today()
        window=tk.Toplevel(self);window.title('Choose date');window.configure(bg=BG);window.transient(self.winfo_toplevel());window.grab_set()
        year=tk.StringVar(value=str(current.year));month=tk.StringVar(value=calendar.month_name[current.month])
        header=tk.Frame(window,bg=BG);header.pack(fill='x',padx=14,pady=14)
        now=date.today().year
        y=ttk.Combobox(header,textvariable=year,values=list(range(now-120,now+1 if self.birth else now+81)),state='readonly',width=8);y.pack(side='left',padx=4)
        m=ttk.Combobox(header,textvariable=month,values=list(calendar.month_name)[1:],state='readonly',width=14);m.pack(side='left',padx=4)
        days=tk.Frame(window,bg=BG);days.pack(padx=14,pady=8)
        def close():
            window.destroy()
            owner=self.winfo_toplevel()
            if owner.master is not None:owner.grab_set()
        def choose(day):
            selected=date(int(year.get()),list(calendar.month_name).index(month.get()),day)
            self.variable.set(selected.strftime(self.fmt));close()
        def draw(event=None):
            for w in days.winfo_children():w.destroy()
            for col,label in enumerate(('Mon','Tue','Wed','Thu','Fri','Sat','Sun')):tk.Label(days,text=label,bg=BG,fg=TEXT).grid(row=0,column=col)
            for row,week in enumerate(calendar.monthcalendar(int(year.get()),list(calendar.month_name).index(month.get())),1):
                for col,day in enumerate(week):
                    if day:Button(days,text=str(day),command=lambda d=day:choose(d)).grid(row=row,column=col,padx=2,pady=2)
        y.bind('<<ComboboxSelected>>',draw);m.bind('<<ComboboxSelected>>',draw);draw()
        if not self.birth:Button(window,text='No target date',command=lambda:(self.variable.set(''),close())).pack(pady=8)
        window.protocol('WM_DELETE_WINDOW',close)
