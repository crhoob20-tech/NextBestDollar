"""Local educational topic search with official source links; not a live chatbot."""
import tkinter as tk
import re
import webbrowser
from ui import Button,BG,WHITE,TEXT,MUTED
TOPICS=[
 dict(title='529 education savings plan',keys={'kid','kids','child','children','college','education','529','school'},
      text='If you mean saving for education, a 529 plan is an option to explore. It is a tax-advantaged plan for certain educational costs. If you mean general support for your child, clarify that goal before choosing an education-specific account. Review eligible uses, fees, investment risk and your state’s rules.',
      url='https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins/introduction-529-plans-investor-bulletin'),
 dict(title='Emergency savings',keys={'emergency','buffer','savings','unexpected','reserve','hysa','house','car','vacation'},
      text='An emergency fund is cash set aside for unexpected expenses or loss of income. Keep this separate in your planning from money for a known purchase. Set a target around your own expenses and circumstances.',
      url='https://www.consumerfinance.gov/an-essential-guide-to-building-an-emergency-fund/'),
 dict(title='Explore investing',keys={'invest','investing','investment','retirement','stocks','brokerage'},
      text='Investing means putting money into assets such as stocks or bonds, hoping for future income or growth. A stock is ownership in a company. A fund holds a collection of investments. An index fund seeks to follow a market index, such as the S&P 500. It can lose value, and fees affect results. Your account (for example an IRA) and the investments inside it are separate choices. After learning, open Plan to explore your own numbers.',
      url='https://www.investor.gov/introduction-investing/general-resources/news-alerts/alerts-bulletins/investor-bulletins-26')]

def match_topics(query):
    words=set(re.findall(r'[a-z0-9]+',query.lower()))
    return [topic for topic in TOPICS if words & topic['keys']]

def build_research(parent,state,open_plan=None):
    frame=tk.Frame(parent,bg=BG);frame.pack(fill='both',expand=True,padx=34,pady=18)
    tk.Label(frame,text='What would you like your money to do?',font=('Helvetica',18,'bold'),bg=BG,fg=TEXT).pack(anchor='w')
    tk.Label(frame,text='Search a small educational topic guide. Example: “I want to invest for my kid”.',bg=BG,fg=MUTED).pack(anchor='w',pady=8)
    query=tk.StringVar()
    entry=tk.Entry(frame,textvariable=query,bg=WHITE,fg=TEXT,insertbackground=TEXT,font=('Helvetica',12));entry.pack(fill='x',ipady=10,pady=8)
    planning=tk.Frame(frame,bg=BG)
    planning.pack(fill="x",pady=5)
    results=tk.Text(frame,wrap='word',bg=WHITE,fg=TEXT,relief='flat',padx=16,pady=16,font=('Helvetica',11))
    def search():
        results.config(state='normal');results.delete('1.0','end')
        for child in planning.winfo_children():child.destroy()
        matches=match_topics(query.get())
        if open_plan:
            for topic in matches:
                kind={'529 education savings plan':'529','Emergency savings':'hysa'}.get(topic['title'],'brokerage')
                Button(planning,text='Plan: '+topic['title'],command=lambda k=kind:open_plan({'account_type':k})).pack(anchor='w',pady=4)
        if not matches:
            results.insert('end','No topic match yet. Try education, emergency savings, or investing. More topics can be added next.')
        for i,topic in enumerate(matches):
            results.insert('end',topic['title']+'\n','heading')
            results.insert('end',topic['text']+'\n\n')
            tag=f'link{i}';results.insert('end','Read the official source ↗\n\n',tag)
            results.tag_configure(tag,foreground='#2F6BFF',underline=True)
            results.tag_bind(tag,'<Button-1>',lambda e,url=topic['url']:webbrowser.open(url))
        results.tag_configure('heading',font=('Helvetica',14,'bold'))
        results.config(state='disabled')
    Button(frame,text='Explore options',command=search).pack(anchor='w',pady=8)
    entry.bind('<Return>',lambda e:search())
    results.pack(fill='both',expand=True,pady=8);results.config(state='disabled')
    tk.Label(frame,text='Educational summaries checked September 11, 2026. Open the official source for current details.',bg=BG,fg=MUTED).pack(anchor='w')
