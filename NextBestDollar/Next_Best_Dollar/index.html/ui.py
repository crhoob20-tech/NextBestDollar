"""Consistent controls, including macOS where native button colors vary."""
import tkinter as tk
from tkinter import ttk
BG='#F2F5F9'; WHITE='#FFFFFF'; TEXT='#1A2233'; BLUE='#2F6BFF'; MUTED='#596579'
class Button(tk.Label):
    def __init__(self,parent,text,command,bg=BLUE,fg=WHITE,**kw):
        super().__init__(parent,text=text,bg=bg,fg=fg,font=('Helvetica',11,'bold'),padx=16,pady=10,
                         takefocus=True,highlightthickness=1,highlightbackground=bg,highlightcolor=TEXT,cursor='hand2',**kw)
        self.command=command
        self.bind('<Button-1>',lambda e:command())
        self.bind('<Return>',lambda e:command())
        self.bind('<space>',lambda e:command())

def style_widgets(root):
    style=ttk.Style(root)
    style.theme_use('clam')
    style.configure('TCombobox',fieldbackground=WHITE,background=WHITE,foreground=TEXT,padding=6)
    style.map('TCombobox',fieldbackground=[('readonly',WHITE)],foreground=[('readonly',TEXT)])
    style.configure('TProgressbar',background=BLUE,troughcolor='#E4EAF2')

def wheel_units(delta, system):
    if not delta:
        return 0
    amount=abs(delta) if system == 'aqua' else abs(delta)/120
    return (-1 if delta>0 else 1)*max(1,min(8,round(amount)))

def install_scrolling(root):
    """Route wheel events to the canvas under the pointer; no dead canvas closures."""
    if getattr(root,'_nbd_wheel_installed',False):return
    root._nbd_wheel_installed=True
    def scroll(event):
        try:
            widget=root.winfo_containing(event.x_root,event.y_root) or event.widget
            if widget.winfo_class() in ('Text','Listbox','Treeview','TCombobox'):
                return
            while widget is not None:
                if isinstance(widget,tk.Canvas):
                    if widget.yview()==(0.0,1.0):return
                    units=-1 if getattr(event,'num',None)==4 else 1 if getattr(event,'num',None)==5 else wheel_units(event.delta,root.tk.call('tk','windowingsystem'))
                    widget.yview_scroll(units,'units')
                    return 'break'
                widget=widget.master
        except tk.TclError:
            return
    for event in ('<MouseWheel>','<Button-4>','<Button-5>'):
        root.bind_all(event,scroll,add='+')
