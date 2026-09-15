"""Consistent controls, including macOS where native button colors vary."""
import tkinter as tk
from tkinter import ttk
BG='#F2F5F9'; WHITE='#FFFFFF'; TEXT='#1A2233'; BLUE='#2F6BFF'; MUTED='#596579'
class Button(tk.Label):
    def __init__(self,parent,text,command,bg=BLUE,fg=WHITE,**kw):
        super().__init__(parent,text=text,bg=bg,fg=fg,font=('Helvetica',11,'bold'),padx=16,pady=10,
                         takefocus=True,highlightthickness=1,highlightbackground=bg,highlightcolor=TEXT,cursor='hand2',**kw)
        self.command=command
        self.bind('<Button-1>',lambda e:self.command())
        self.bind('<Return>',lambda e:self.command())
        self.bind('<space>',lambda e:self.command())

def style_widgets(root):
    style=ttk.Style(root)
    style.theme_use('clam')
    style.configure('TCombobox',fieldbackground=WHITE,background=WHITE,foreground=TEXT,padding=6)
    style.map('TCombobox',fieldbackground=[('readonly',WHITE)],foreground=[('readonly',TEXT)])
    style.configure('TProgressbar',background=BLUE,troughcolor='#E4EAF2',thickness=8)
    style.configure('TNotebook',background=BG,borderwidth=0)
    style.configure('TNotebook.Tab',padding=(18,12),font=('Helvetica',11,'bold'))
    style.map('TNotebook.Tab',background=[('selected',WHITE)],foreground=[('selected',BLUE)])

def wheel_units(delta, system):
    if not delta:
        return 0
    amount=abs(delta) if system == 'aqua' else abs(delta)/120
    return (-1 if delta>0 else 1)*max(1,min(2,round(amount)))

def install_scrolling(root):
    """Route wheel events to the canvas under the pointer; no dead canvas closures."""
    if getattr(root,'_nbd_wheel_installed',False):return
    root._nbd_wheel_installed=True
    def scroll(event):
        try:
            widget=event.widget
            while widget is not None:
                if isinstance(widget,tk.Canvas) and widget.yview() != (0.0,1.0):
                    units=-1 if getattr(event,'num',None)==4 else 1 if getattr(event,'num',None)==5 else wheel_units(event.delta,root.tk.call('tk','windowingsystem'))
                    widget.configure(yscrollincrement=12)
                    widget.yview_scroll(units,'units')
                    break
                widget=widget.master
        except (tk.TclError,AttributeError):
            pass
        return 'break'
    # Intercept before native field handlers: scroll the ancestor page, never
    # cycle a dropdown, spinner, or answer. Native popup lists retain navigation.
    for cls in ('TCombobox','Spinbox','TSpinbox','Scale','TScale','Entry','TEntry','Text'):
        for event in ('<MouseWheel>','<Button-4>','<Button-5>'):
            root.bind_class(cls,event,scroll)
    for event in ('<MouseWheel>','<Button-4>','<Button-5>'):
        root.bind_all(event,scroll,add='+')


def scroll_page(parent, padding=24):
    """Consistent page gutter and a visible scrollbar, shared by summary pages."""
    shell=tk.Frame(parent,bg=BG)
    shell.pack(fill='both',expand=True,padx=padding,pady=16)
    canvas=tk.Canvas(shell,bg=BG,highlightthickness=0)
    bar=ttk.Scrollbar(shell,command=canvas.yview)
    bar.pack(side='right',fill='y')
    canvas.pack(side='left',fill='both',expand=True)
    body=tk.Frame(canvas,bg=BG)
    window=canvas.create_window((0,0),window=body,anchor='nw')
    body.bind('<Configure>',lambda e:canvas.configure(scrollregion=canvas.bbox('all')))
    canvas.bind('<Configure>',lambda e:canvas.itemconfigure(window,width=e.width))
    canvas.configure(yscrollcommand=bar.set,yscrollincrement=12)
    return body


def copy_label(parent,text,size=11,bold=False,color=TEXT,bg=None):
    label=tk.Label(parent,text=text,bg=bg or parent.cget('bg'),fg=color,
                   font=('Helvetica',size,'bold' if bold else 'normal'),justify='left',anchor='w')
    label.pack(fill='x',pady=5)
    label.bind('<Configure>',lambda e:label.config(wraplength=max(120,e.width)))
    return label


def panel(parent):
    card=RoundedCard(parent)
    card.pack(fill='x',pady=6)
    return card.content


class RoundedCard(tk.Canvas):
    """Rounded surface with a real content frame and height driven by content."""
    def __init__(self,parent,**kwargs):
        super().__init__(parent,bg=parent.cget('bg'),highlightthickness=0,**kwargs)
        self.content=tk.Frame(self,bg=WHITE)
        self.window=self.create_window(18,14,window=self.content,anchor='nw')
        self.bind('<Configure>',self.redraw)
        self.content.bind('<Configure>',self.redraw)
    def redraw(self,event=None):
        w=max(80,self.winfo_width());h=self.content.winfo_reqheight()+28;r=18
        self.configure(height=h)
        self.itemconfigure(self.window,width=max(44,w-36))
        self.delete('surface')
        self.create_polygon(r,0,w-r,0,w,0,w,r,w,h-r,w,h,w-r,h,r,h,0,h,0,h-r,0,r,0,0,
                            smooth=True,splinesteps=24,fill=WHITE,outline='',tags='surface')
        self.tag_lower('surface')
