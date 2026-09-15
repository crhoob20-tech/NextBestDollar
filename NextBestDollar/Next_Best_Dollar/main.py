import tkinter as tk
from onboarding import OnboardingFlow
from storage import load_state

# ============================================================
# NEXT BEST DOLLAR
# Modern Bank / Fintech Main Application Shell
# ============================================================

# ============================================================
# THEME
# ============================================================
SIDEBAR_BG = "#0F1B2D"
SIDEBAR_HOVER = "#17263B"
SIDEBAR_ACTIVE = "#21406A"

MAIN_BG = "#F2F5F9"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#D4DCE7"

PRIMARY = "#2F6BFF"
PRIMARY_HOVER = "#2458D8"

TEXT = "#1A2233"
MUTED = "#596579"
MUTED_2 = "#7F8A9C"

GREEN = "#0F9D6A"
AMBER = "#C78700"
RED = "#D64545"

WHITE = "#FFFFFF"

FONT_TITLE = ("Helvetica", 24, "bold")
FONT_HEADER = ("Helvetica", 15, "bold")
FONT_SUBHEADER = ("Helvetica", 11, "bold")
FONT_BODY = ("Helvetica", 10)
FONT_SMALL = ("Helvetica", 9)
FONT_NUMBER = ("Helvetica", 22, "bold")


# ============================================================
# CUSTOM BUTTON
# Tkinter native buttons on macOS often ignore bg/fg colors and
# render with the system's white button style. This custom button
# uses a Label so the app keeps its intended colors.
# ============================================================
class AppButton(tk.Label):
    def __init__(
        self,
        parent,
        text,
        command,
        bg,
        fg,
        hover_bg,
        hover_fg=None,
        font=FONT_SUBHEADER,
        padx=18,
        pady=10,
        anchor="center"
    ):
        super().__init__(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            font=font,
            padx=padx,
            pady=pady,
            anchor=anchor,
            cursor="arrow"
        )

        self.command = command
        self.default_bg = bg
        self.default_fg = fg
        self.hover_bg = hover_bg
        self.hover_fg = hover_fg or fg

        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)

    def _click(self, event):
        if self.command:
            self.command()

    def _enter(self, event):
        self.config(bg=self.hover_bg, fg=self.hover_fg)

    def _leave(self, event):
        self.config(bg=self.default_bg, fg=self.default_fg)

    def set_colors(self, bg=None, fg=None, hover_bg=None):
        if bg is not None:
            self.default_bg = bg
            self.config(bg=bg)
        if fg is not None:
            self.default_fg = fg
            self.hover_fg = fg
            self.config(fg=fg)
        if hover_bg is not None:
            self.hover_bg = hover_bg


# ============================================================
# APP STATE
# ============================================================
app_state = load_state()


# ============================================================
# MAIN APP
# ============================================================
class NextBestDollarApp(tk.Tk):
    def __init__(self):
        super().__init__()

        from ui import install_scrolling
        install_scrolling(self)
        self.title("Next Best Dollar")
        self.geometry("1200x820")
        self.minsize(960, 700)
        self.configure(bg=MAIN_BG)

        self.nav_buttons = {}
        self.current_page = "Dashboard"

        self.build_shell()
        self.show_page("Dashboard")
        self.refresh_after_onboarding()

    # ========================================================
    # SHELL
    # ========================================================
    def build_shell(self):
        self.build_sidebar()

        self.main = tk.Frame(self, bg=MAIN_BG)
        self.main.pack(side="left", fill="both", expand=True)

        self.build_topbar()

        self.page_container = tk.Frame(self.main, bg=MAIN_BG)
        self.page_container.pack(fill="both", expand=True)

    # ========================================================
    # SIDEBAR
    # ========================================================
    def build_sidebar(self):
        sidebar = tk.Frame(self, bg=SIDEBAR_BG, width=225)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        brand = tk.Frame(sidebar, bg=SIDEBAR_BG)
        brand.pack(fill="x", padx=20, pady=(24, 26))

        tk.Label(
            brand,
            text="Next Best Dollar",
            font=("Helvetica", 18, "bold"),
            fg=WHITE,
            bg=SIDEBAR_BG
        ).pack(anchor="w")

        tk.Label(
            brand,
            text="Make the next dollar matter.",
            font=FONT_SMALL,
            fg="#B8C2D1",
            bg=SIDEBAR_BG
        ).pack(anchor="w", pady=(4, 0))

        nav_items = [
            ("Dashboard", "⌂"),
            ("Profile", "◉"),
            ("Goals", "◎"),
            ("Plan", "→"),
            ("Research", "⌕"),
        ]

        for page_name, icon in nav_items:
            button = AppButton(
                sidebar,
                text=f"{icon}   {page_name}",
                command=lambda name=page_name: self.show_page(name),
                bg=SIDEBAR_BG,
                fg="#D8E0EA",
                hover_bg=SIDEBAR_HOVER,
                hover_fg=WHITE,
                font=("Helvetica", 10, "bold"),
                padx=18,
                pady=12,
                anchor="w"
            )
            button.pack(fill="x", padx=10, pady=3)
            self.nav_buttons[page_name] = button

        tk.Frame(sidebar, bg=SIDEBAR_BG).pack(fill="both", expand=True)

        status = tk.Frame(
            sidebar,
            bg=SIDEBAR_HOVER,
            highlightbackground="#263B54",
            highlightthickness=1
        )
        status.pack(fill="x", padx=14, pady=16)

        tk.Label(
            status,
            text="PROFILE STATUS",
            font=("Helvetica", 8, "bold"),
            fg="#9EACBF",
            bg=SIDEBAR_HOVER
        ).pack(anchor="w", padx=12, pady=(10, 3))

        self.sidebar_status = tk.Label(
            status,
            text="Not completed",
            font=FONT_SUBHEADER,
            fg="#FFD166",
            bg=SIDEBAR_HOVER
        )
        self.sidebar_status.pack(anchor="w", padx=12, pady=(0, 10))

    # ========================================================
    # TOP BAR
    # ========================================================
    def build_topbar(self):
        topbar = tk.Frame(self.main, bg=MAIN_BG)
        topbar.pack(fill="x", padx=34, pady=(24, 8))

        left = tk.Frame(topbar, bg=MAIN_BG)
        left.pack(side="left")

        self.page_title = tk.Label(
            left,
            text="Dashboard",
            font=FONT_TITLE,
            fg=TEXT,
            bg=MAIN_BG
        )
        self.page_title.pack(anchor="w")

        self.page_subtitle = tk.Label(
            left,
            text="Your financial life, translated into the next best action.",
            font=FONT_BODY,
            fg=MUTED,
            bg=MAIN_BG
        )
        self.page_subtitle.pack(anchor="w", pady=(5, 0))

        self.profile_button = AppButton(
            topbar,
            text="Complete Profile",
            command=self.start_onboarding_placeholder,
            bg=PRIMARY,
            fg=WHITE,
            hover_bg=PRIMARY_HOVER,
            hover_fg=WHITE,
            font=FONT_SUBHEADER,
            padx=18,
            pady=10
        )
        # Profile editing lives in the Profile page.

    # ========================================================
    # PAGE SWITCHING
    # ========================================================
    def show_page(self, page_name):
        self.current_page = page_name

        for name, button in self.nav_buttons.items():
            if name == page_name:
                button.set_colors(
                    bg=SIDEBAR_ACTIVE,
                    fg=WHITE,
                    hover_bg=SIDEBAR_ACTIVE
                )
            else:
                button.set_colors(
                    bg=SIDEBAR_BG,
                    fg="#D8E0EA",
                    hover_bg=SIDEBAR_HOVER
                )

        info = {
            "Dashboard": (
                "Dashboard",
                "Your financial life, translated into the next best action."
            ),
            "Profile": (
                "Profile",
                "The personal, behavioral, and financial facts behind your plan."
            ),
            "Goals": (
                "Goals",
                "Set targets and track progress toward your major milestones."
            ),
            "Plan": (
                "Next Best Dollar",
                "Explore how contributions and time could change your balance."
            ),
            "Research": (
                "Research",
                "Explore financial concepts, investments, and market information."
            ),
        }

        title, subtitle = info[page_name]
        self.page_title.config(text=title)
        self.page_subtitle.config(text=subtitle)

        self.clear_page()

        if page_name == "Dashboard":
            self.build_dashboard()
        elif page_name == "Profile":
            self.build_profile_page()
        elif page_name == "Goals":
            self.build_goals_page()
        elif page_name == "Plan":
            self.build_plan_page()
        elif page_name == "Research":
            self.build_research_page()

    def clear_page(self):
        for child in self.page_container.winfo_children():
            child.destroy()

    # ========================================================
    # UI HELPERS
    # ========================================================
    def section_title(self, parent, title, subtitle=""):
        block = tk.Frame(parent, bg=MAIN_BG)
        block.pack(fill="x", pady=(22, 8))

        tk.Label(
            block,
            text=title,
            font=FONT_HEADER,
            fg=TEXT,
            bg=MAIN_BG
        ).pack(anchor="w")

        if subtitle:
            tk.Label(
                block,
                text=subtitle,
                font=FONT_SMALL,
                fg=MUTED,
                bg=MAIN_BG
            ).pack(anchor="w", pady=(3, 0))

    def card(self, parent):
        frame = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1
        )
        return frame

    def metric_card(self, parent, label, value, note):
        card = self.card(parent)

        tk.Label(
            card,
            text=label,
            font=FONT_SMALL,
            fg=MUTED,
            bg=CARD_BG
        ).pack(anchor="w", padx=16, pady=(15, 4))

        tk.Label(
            card,
            text=value,
            font=FONT_NUMBER,
            fg=TEXT,
            bg=CARD_BG
        ).pack(anchor="w", padx=16)

        tk.Label(
            card,
            text=note,
            font=FONT_SMALL,
            fg=MUTED_2,
            bg=CARD_BG,
            wraplength=220,
            justify="left"
        ).pack(anchor="w", padx=16, pady=(6, 15))

        return card

    # ========================================================
    # DASHBOARD
    # ========================================================
    def build_dashboard(self):
        page = tk.Frame(self.page_container, bg=MAIN_BG)
        page.pack(fill="both", expand=True, padx=34, pady=(8, 30))

        self.section_title(
            page,
            "Financial snapshot",
            "Updated from your saved financial information."
        )

        metric_grid = tk.Frame(page, bg=MAIN_BG)
        metric_grid.pack(fill="x")

        metrics = app_state.get("financial_metrics", {})

        if metrics:
            monthly_cash_flow = f'${metrics.get("monthly_free_cash_flow", 0):,.0f}'
            cash_reserves = f'${metrics.get("liquid_cash", 0):,.0f}'
            total_debt = f'${metrics.get("total_debt", 0):,.0f}'
            investable_surplus = f'${max(metrics.get("monthly_free_cash_flow", 0), 0):,.0f}'
        else:
            monthly_cash_flow = "—"
            cash_reserves = "—"
            total_debt = "—"
            investable_surplus = "—"

        metric_data = [
            ("Monthly cash flow", monthly_cash_flow, "Income minus monthly spending and debt minimums"),
            ("Cash reserves", cash_reserves, "Available liquid savings"),
            ("Total debt", total_debt, "Outstanding debt balances"),
            ("Investable surplus", investable_surplus, "Estimated monthly money available for allocation"),
        ]

        for i, data in enumerate(metric_data):
            card = self.metric_card(metric_grid, *data)
            card.grid(
                row=0,
                column=i,
                sticky="nsew",
                padx=(0 if i == 0 else 6, 0 if i == 3 else 6)
            )
            metric_grid.grid_columnconfigure(i, weight=1)

        controls = tk.Frame(page, bg=MAIN_BG)
        controls.pack(fill="x", pady=(15, 0))
        for label, section in (("Edit income & budget", "income"), ("Manage accounts", "accounts"), ("Manage debts & investments", "debt")):
            AppButton(controls, text=label, command=lambda k=section: self.edit_section(2, k),
                      bg=PRIMARY, fg=WHITE, hover_bg=PRIMARY_HOVER, padx=12, pady=9).pack(side="left", padx=(0, 10))

        AppButton(page, text="View charts", command=lambda: __import__('dashboard_charts').show_charts(self, app_state),
                  bg=PRIMARY, fg=WHITE, hover_bg=PRIMARY_HOVER, padx=12, pady=9).pack(anchor="e", pady=(10, 0))

        self.section_title(page, "Your monthly picture", "Recorded inflows and outflows")
        from visual_charts import flow_chart
        snapshot_card=self.card(page);snapshot_card.pack(fill='x')
        flow_chart(snapshot_card,app_state)

        self.section_title(
            page,
            "Goals",
            "Track the milestones you want your money to support."
        )

        goals = self.card(page)
        goals.pack(fill="x")

        from goals import goal_status
        saved_goals = app_state.get("goals", [])
        if saved_goals:
            list_frame = tk.Frame(goals, bg=CARD_BG)
            list_frame.pack(fill="x", padx=18, pady=12)
            scrollbar = tk.Scrollbar(list_frame)
            scrollbar.pack(side="right", fill="y")
            listing = tk.Listbox(list_frame, height=min(4, len(saved_goals)), bg=CARD_BG, fg=TEXT,
                                 font=FONT_BODY, relief="flat", yscrollcommand=scrollbar.set)
            listing.pack(fill="x", expand=True)
            scrollbar.config(command=listing.yview)
            for goal in saved_goals:
                listing.insert("end", f"{goal['name']} — ${goal['progress_amount']:,.0f} / ${goal['target_amount']:,.0f} — {goal_status(goal)}")
        else:
            from suggestions import suggested_goals
            prompts = suggested_goals(app_state)
            text = "Suggested starting goals: " + ", ".join(g['name'] for g in prompts) if prompts else "Add your first milestone in Goals."
            tk.Label(goals, text=text, bg=CARD_BG, fg=TEXT, wraplength=760, justify="left").pack(anchor="w", padx=18, pady=12)

        AppButton(goals, text="Manage goals", command=lambda: self.show_page("Goals"),
                  bg=PRIMARY, fg=WHITE, hover_bg=PRIMARY_HOVER).pack(anchor="w", padx=18, pady=(0, 14))

    # ========================================================
    # PROFILE PAGE
    # ========================================================
    def build_profile_page(self):
        from tkinter import ttk
        from profile_overview import build_overview
        tabs=ttk.Notebook(self.page_container);tabs.pack(fill='both',expand=True,padx=20,pady=14)
        overview=tk.Frame(tabs,bg=MAIN_BG);details=tk.Frame(tabs,bg=MAIN_BG)
        tabs.add(overview,text='Financial overview');tabs.add(details,text='Edit your information')
        build_overview(overview,app_state)
        page=tk.Frame(details,bg=MAIN_BG)
        page.pack(fill='both',expand=True,padx=18,pady=12)

        sections = [
            (
                "1. Personal facts",
                "Age, household, employment, dependents, housing, and other objective personal context."
            ),
            (
                "2. Behavioral profile",
                "Situational 1–5 questions that estimate discipline, planning, delayed gratification, risk behavior, and decision style."
            ),
            (
                "3. Financial facts",
                "Income, spending, savings, debts, investments, retirement accounts, and benefits."
            ),
        ]

        for index, (title, description) in enumerate(sections):
            card = self.card(page)
            card.pack(fill="x", pady=7)

            tk.Label(
                card,
                text=title,
                font=FONT_HEADER,
                fg=TEXT,
                bg=CARD_BG
            ).pack(anchor="w", padx=18, pady=(16, 5))

            tk.Label(
                card,
                text=description,
                font=FONT_BODY,
                fg=MUTED,
                bg=CARD_BG,
                wraplength=800,
                justify="left"
            ).pack(anchor="w", padx=18, pady=(0, 16))

            AppButton(card, text=("Edit personal facts", "Edit answers", "Edit finances")[index], command=lambda i=index: self.edit_section(i),
                      bg=PRIMARY, fg=WHITE, hover_bg=PRIMARY_HOVER).pack(anchor="w", padx=18, pady=(0, 14))

        if not app_state.get("onboarding_complete"):
            AppButton(
                page,
                text="Continue onboarding",
                command=self.start_onboarding_placeholder,
                bg=PRIMARY,
                fg=WHITE,
                hover_bg=PRIMARY_HOVER,
                hover_fg=WHITE,
                font=FONT_SUBHEADER,
                padx=20,
                pady=10
            ).pack(anchor="w", pady=(14, 0))

    # ========================================================
    # GOALS PAGE
    # ========================================================
    def build_goals_page(self):
        from goals import build_goals
        build_goals(self.page_container, app_state, lambda: self.show_page("Goals"))

    # ========================================================
    # PLAN PAGE
    # ========================================================
    def open_plan(self, context=None):
        self.plan_context = context or {}
        self.show_page("Plan")

    def build_plan_page(self):
        from forecasting import build_forecast
        from tkinter import ttk
        from allocation import build_allocation
        from life_timeline import build_timeline
        tabs=ttk.Notebook(self.page_container);tabs.pack(fill='both',expand=True,padx=14,pady=8)
        allocation=tk.Frame(tabs,bg=MAIN_BG);forecast=tk.Frame(tabs,bg=MAIN_BG)
        tabs.add(allocation,text='Monthly allocation');tabs.add(forecast,text='Account projection')
        timeline=tk.Frame(tabs,bg=MAIN_BG);tabs.add(timeline,text='Life & debt timeline')
        build_timeline(timeline,app_state)
        build_allocation(allocation,app_state,self.open_plan)
        build_forecast(forecast,app_state,getattr(self,'plan_context',None))
        if getattr(self,'plan_context',None):tabs.select(forecast)

    # ========================================================
    # RESEARCH PAGE
    # ========================================================
    def build_research_page(self):
        from research import build_research
        build_research(self.page_container, app_state, self.open_plan)

    # ========================================================
    # PLACEHOLDER ONBOARDING
    # ========================================================
    def edit_section(self, index, start_section="income"):
        if index == 0:
            OnboardingFlow(self, app_state, on_complete=self.refresh_after_onboarding, edit_only=True)
        elif index == 1:
            from behavioral import BehavioralFlow
            BehavioralFlow(self, app_state, on_complete=self.refresh_after_onboarding, edit_only=True)
        else:
            from financial import FinancialFlow
            FinancialFlow(self, app_state, on_complete=self.refresh_after_onboarding, start_section=start_section)

    def start_onboarding_placeholder(self):
        # Resume at the first unfinished onboarding section.
        if not app_state.get("personal_complete"):
            OnboardingFlow(
                self,
                app_state,
                on_complete=self.refresh_after_onboarding
            )
            return

        if not app_state.get("behavioral_complete"):
            from behavioral import BehavioralFlow

            BehavioralFlow(
                self,
                app_state,
                on_complete=self.refresh_after_onboarding
            )
            return

        if not app_state.get("financial_complete"):
            from financial import FinancialFlow

            FinancialFlow(
                self,
                app_state,
                on_complete=self.refresh_after_onboarding
            )
            return

        # Completed profiles open independent editing controls.
        self.show_page("Profile")


    def refresh_after_onboarding(self):
        if app_state.get("onboarding_complete"):
            self.sidebar_status.config(
                text="Complete",
                fg=GREEN
            )
            self.profile_button.config(
                text="Edit Profile"
            )
        elif app_state.get("personal_complete") or app_state.get("behavioral_complete"):
            self.sidebar_status.config(
                text="In progress",
                fg=AMBER
            )
            self.profile_button.config(
                text="Continue Profile"
            )
        else:
            self.sidebar_status.config(
                text="Not completed",
                fg=AMBER
            )

        self.show_page("Dashboard")



# ============================================================
# START
# ============================================================
if __name__ == "__main__":
    app = NextBestDollarApp()
    app.mainloop()
