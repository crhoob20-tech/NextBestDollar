"""Dated references and deliberately labeled planning examples, not forecasts."""
import tkinter as tk
import webbrowser
from ui import Button,copy_label,MUTED,BG,BLUE
STOCK_SOURCE='https://www.fidelity.com/learning-center/trading-investing/sp-500-average-return'
CASH_SOURCE='https://www.fdic.gov/national-rates-and-rate-caps/national-rates-and-rate-caps-january-2026'
def build_return_guidance(parent,kind,annual,note):
    cash=kind in ('savings','hysa')
    summary=('Cash: use your account APY when available. The FDIC national savings average was 0.39% in January 2026; this is a dated benchmark, not a current high-yield quote.' if cash else 'S&P 500 reference: Fidelity reports 10.4% average annual return for January 1996–December 2025. That index history does not describe every stock, fund, IRA or 529.')
    box=tk.Frame(parent,bg=BG);box.pack(fill='x',pady=6)
    copy_label(box,summary,color=MUTED)
    buttons=tk.Frame(box,bg=BG);buttons.pack(fill='x',pady=5)
    examples=[(0,'0%'),(.39,'0.39% benchmark'),(3,'3% example')] if cash else [(0,'0%'),(6,'6% example'),(8,'8% example'),(10.4,'10.4% history')]
    def use(rate,label):
        annual.set(str(rate));note.set(label+' | '+summary+' | '+(CASH_SOURCE if cash else STOCK_SOURCE))
    for rate,label in examples:
        btn=Button(buttons,text=label,command=lambda r=rate,l=label:use(r,l),bg='#E7EFFF',fg=BLUE)
        btn.config(padx=10,pady=7);btn.pack(side='left',padx=(0,6))
    copy_label(box,'These are constant-rate illustrations before taxes, fees and inflation. Cash rates change; stocks can lose money. Historical averages do not predict future returns.',color=MUTED)
    Button(box,text='Read source',command=lambda:webbrowser.open(CASH_SOURCE if cash else STOCK_SOURCE),bg=BG,fg=BLUE).pack(anchor='w')
