import tkinter as tk
from tkinter import messagebox
from copy import deepcopy
import math
from storage import save_state

# ============================================================
# NEXT BEST DOLLAR
# FINANCIAL FACTS MODULE
#
# Step 3A: Income
# Step 3B: Monthly Spending
# Step 3C: Accounts & Savings
# Step 3D: Debt & Investments
#
# This file owns:
# 1. Financial questions
# 2. Validation
# 3. Derived financial metrics
# 4. Saving financial data into app_state
# ============================================================

CASH_TYPES = {"checking": "Checking", "savings": "Traditional savings", "hysa": "HYSA / money market", "other_cash": "Other liquid cash"}
INVESTMENT_TYPES = {"retirement_employer": "401(k) / 403(b)", "ira": "Traditional / Roth IRA", "brokerage": "Brokerage", "hsa": "HSA", "other_investments": "Other investments"}

def normalize_financial(saved):
    data = deepcopy(saved)
    for key in ("income", "spending", "accounts", "investments", "benefits"):
        data.setdefault(key, {})
    debts = data.get("debt", [])
    if isinstance(debts, dict):
        labels = {"credit_card": "Credit card", "student_loan": "Student loan", "auto_loan": "Auto loan", "personal_loan": "Personal loan", "mortgage": "Mortgage", "other_debt": "Other debt"}
        data["debt"] = [dict(item, type=labels.get(key, key), name=labels.get(key, key), provider="")
                        for key, item in debts.items() if isinstance(item, dict) and (item.get("balance", 0) or item.get("minimum_payment", 0))]
    else:
        data["debt"] = deepcopy(debts)
    if "account_entries" not in data:
        data["account_entries"] = []
        for group, types in (("accounts", CASH_TYPES), ("investments", INVESTMENT_TYPES)):
            for key, label in types.items():
                balance = data[group].get(key, 0)
                if balance:
                    data["account_entries"].append(dict(type=key, name=label, provider="", balance=balance))
    return data


def calculate_metrics(financial_data):
    income = financial_data["income"]
    spending = financial_data["spending"]
    accounts = financial_data["accounts"]
    debt = financial_data["debt"]
    investments = financial_data["investments"]
    benefits = financial_data["benefits"]

    monthly_income = (
        income.get("primary_take_home", 0)
        + income.get("other_recurring_income", 0)
        + income.get("variable_income", 0)
    )

    monthly_living_spending = sum(spending.values())

    monthly_debt_minimums = sum(
        item["minimum_payment"]
        for item in debt
    )

    monthly_total_outflow = (
        monthly_living_spending
        + monthly_debt_minimums
    )

    monthly_free_cash_flow = (
        monthly_income
        - monthly_total_outflow
    )

    liquid_cash = (
        accounts["checking"]
        + accounts["savings"]
        + accounts["hysa"]
        + accounts["other_cash"]
    )

    total_debt = sum(
        item["balance"]
        for item in debt
    )

    total_investments = sum(investments.values())

    net_financial_position = (
        liquid_cash
        + total_investments
        - total_debt
    )

    if monthly_total_outflow > 0:
        cash_months = liquid_cash / monthly_total_outflow
    else:
        cash_months = 0.0

    if monthly_total_outflow > 0:
        emergency_months = (
            accounts["emergency_fund"]
            / monthly_total_outflow
        )
    else:
        emergency_months = 0.0

    match_gap = max(
        0.0,
        benefits.get("employer_match", 0)
        - benefits.get("current_retirement_contribution", 0),
    )

    metrics = {
        "monthly_income": round(monthly_income, 2),
        "monthly_living_spending": round(monthly_living_spending, 2),
        "monthly_debt_minimums": round(monthly_debt_minimums, 2),
        "monthly_total_outflow": round(monthly_total_outflow, 2),
        "monthly_free_cash_flow": round(monthly_free_cash_flow, 2),
        "liquid_cash": round(liquid_cash, 2),
        "emergency_fund": round(accounts["emergency_fund"], 2),
        "cash_months": round(cash_months, 2),
        "emergency_fund_months": round(emergency_months, 2),
        "total_debt": round(total_debt, 2),
        "total_investments": round(total_investments, 2),
        "net_financial_position": round(net_financial_position, 2),
        "employer_match_gap_percent": round(match_gap, 2),
    }

    return metrics


# ============================================================
# THEME
# ============================================================
MAIN_BG = "#F2F5F9"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#D4DCE7"

PRIMARY = "#2F6BFF"
PRIMARY_HOVER = "#2458D8"

TEXT = "#1A2233"
MUTED = "#596579"
MUTED_2 = "#7F8A9C"

GREEN = "#0F9D6A"
RED = "#D64545"

WHITE = "#FFFFFF"

FONT_TITLE = ("Helvetica", 22, "bold")
FONT_HEADER = ("Helvetica", 14, "bold")
FONT_SUBHEADER = ("Helvetica", 11, "bold")
FONT_BODY = ("Helvetica", 10)
FONT_SMALL = ("Helvetica", 9)
FONT_BUTTON = ("Helvetica", 11, "bold")


# ============================================================
# CUSTOM BUTTON
# ============================================================
class AppButton(tk.Label):
    def __init__(
        self,
        parent,
        text,
        command,
        bg=PRIMARY,
        fg=WHITE,
        hover_bg=PRIMARY_HOVER,
        padx=18,
        pady=10,
    ):
        super().__init__(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            font=FONT_BUTTON,
            padx=padx,
            pady=pady,
            cursor="arrow",
        )

        self.command = command
        self.default_bg = bg
        self.hover_bg = hover_bg

        self.bind("<Button-1>", self._click)
        self.bind("<Enter>", self._enter)
        self.bind("<Leave>", self._leave)

    def _click(self, event):
        if self.command:
            self.command()

    def _enter(self, event):
        self.config(bg=self.hover_bg)

    def _leave(self, event):
        self.config(bg=self.default_bg)


# ============================================================
# FINANCIAL FLOW
# ============================================================
class FinancialFlow(tk.Toplevel):
    def __init__(self, parent, app_state, on_complete=None, start_section="income"):
        super().__init__(parent)
        self._nbd_scrollbar_only = True

        self.parent = parent
        self.app_state = app_state
        self.on_complete = on_complete

        self.title("Next Best Dollar - Financial Facts")
        self.geometry("820x780")
        self.minsize(720, 650)
        self.configure(bg=MAIN_BG)
        self.transient(parent)
        self.grab_set()

        self.financial_data = normalize_financial(app_state.get("financial", {}))
        self.debt_entries = deepcopy(self.financial_data["debt"])
        self.account_entries = deepcopy(self.financial_data["account_entries"])
        self.account_areas = {}
        self.field_vars = {}
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        {"income": self.build_income_screen, "spending": self.build_spending_screen,
         "accounts": self.build_accounts_screen, "debt": self.build_debt_investment_screen}[start_section]()

    def cancel(self):
        if messagebox.askyesno("Discard changes?", "Close without saving these financial edits?", parent=self):
            self.destroy()

    # ========================================================
    # GENERAL HELPERS
    # ========================================================
    def clear(self):
        self.account_areas = {}
        for widget in self.winfo_children():
            widget.destroy()

    def money_to_float(self, value):
        value = str(value).strip().replace("$", "").replace(",", "")

        if value == "":
            return 0.0

        try:
            number = float(value)
            if not math.isfinite(number) or number < 0:
                return None
            return number
        except ValueError:
            return None

    def percent_to_float(self, value):
        value = str(value).strip().replace("%", "")

        if value == "":
            return 0.0

        try:
            number = float(value)
            if not math.isfinite(number) or number < 0 or number > 100:
                return None
            return number
        except ValueError:
            return None

    def format_money(self, value):
        return f"${value:,.0f}"

    def build_shell(self, step_text, title, subtitle):
        shell = tk.Frame(self, bg=MAIN_BG)
        shell.pack(fill="both", expand=True)

        header = tk.Frame(shell, bg=MAIN_BG)
        header.pack(fill="x", padx=36, pady=(26, 12))

        tk.Label(
            header,
            text=step_text,
            font=FONT_SMALL,
            fg=PRIMARY,
            bg=MAIN_BG,
        ).pack(anchor="w")

        tk.Label(
            header,
            text=title,
            font=FONT_TITLE,
            fg=TEXT,
            bg=MAIN_BG,
        ).pack(anchor="w", pady=(4, 6))

        tk.Label(
            header,
            text=subtitle,
            font=FONT_BODY,
            fg=MUTED,
            bg=MAIN_BG,
            wraplength=720,
            justify="left",
        ).pack(anchor="w")

        body = tk.Frame(shell, bg=MAIN_BG)
        body.pack(fill="both", expand=True, padx=36)

        canvas = tk.Canvas(
            body,
            bg=MAIN_BG,
            highlightthickness=0,
        )

        scrollbar = tk.Scrollbar(
            body,
            orient="vertical",
            command=canvas.yview,
        )

        scroll_frame = tk.Frame(canvas, bg=MAIN_BG)

        window_id = canvas.create_window(
            (0, 0),
            window=scroll_frame,
            anchor="nw",
        )

        def update_scroll_region(event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def resize_inner(event):
            canvas.itemconfigure(window_id, width=event.width)

        scroll_frame.bind("<Configure>", update_scroll_region)
        canvas.bind("<Configure>", resize_inner)

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def on_mousewheel(event):
            try:
                canvas.yview_scroll(
                    int(-1 * (event.delta / 120)),
                    "units",
                )
            except Exception:
                pass

        # Wheel routing is installed once by the app.

        error_label = tk.Label(
            shell,
            text="",
            font=FONT_SMALL,
            fg=RED,
            bg=MAIN_BG,
        )
        error_label.pack(
            anchor="w",
            padx=36,
            pady=(6, 0),
        )

        return shell, scroll_frame, error_label

    def build_footer(
        self,
        shell,
        step_text,
        back_command,
        continue_command,
        continue_text="Continue",
    ):
        footer = tk.Frame(
            shell,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        footer.pack(fill="x", side="bottom")

        inner = tk.Frame(footer, bg=CARD_BG)
        inner.pack(fill="x", padx=36, pady=14)

        if back_command:
            AppButton(
                inner,
                text="Back",
                command=back_command,
                bg="#E8EDF4",
                fg=TEXT,
                hover_bg="#DCE3EC",
            ).pack(side="left")

        tk.Label(
            inner,
            text=step_text,
            font=FONT_SMALL,
            fg=MUTED,
            bg=CARD_BG,
        ).pack(side="left", padx=18)

        AppButton(
            inner,
            text=continue_text,
            command=continue_command,
        ).pack(side="right")

    def section_card(self, parent, title, subtitle=""):
        card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        card.pack(fill="x", pady=7)

        tk.Label(
            card,
            text=title,
            font=FONT_HEADER,
            fg=TEXT,
            bg=CARD_BG,
        ).pack(
            anchor="w",
            padx=20,
            pady=(16, 4),
        )

        if subtitle:
            tk.Label(
                card,
                text=subtitle,
                font=FONT_SMALL,
                fg=MUTED,
                bg=CARD_BG,
                wraplength=650,
                justify="left",
            ).pack(
                anchor="w",
                padx=20,
                pady=(0, 8),
            )

        return card

    def money_field(self, parent, label, key, helper=""):
        wrapper = tk.Frame(parent, bg=CARD_BG)
        wrapper.pack(fill="x", padx=20, pady=8)

        tk.Label(
            wrapper,
            text=label,
            font=FONT_BODY,
            fg=TEXT,
            bg=CARD_BG,
        ).pack(anchor="w", pady=(0, 4))

        if helper:
            tk.Label(
                wrapper,
                text=helper,
                font=FONT_SMALL,
                fg=MUTED_2,
                bg=CARD_BG,
                wraplength=650,
                justify="left",
            ).pack(anchor="w", pady=(0, 5))

        row = tk.Frame(wrapper, bg=CARD_BG)
        row.pack(fill="x")

        tk.Label(
            row,
            text="$",
            font=("Helvetica", 11, "bold"),
            fg=MUTED,
            bg=WHITE,
            width=2,
        ).pack(side="left", ipady=9)

        var = tk.StringVar()
        entry = tk.Entry(
            row,
            textvariable=var,
            font=("Helvetica", 11),
            bg=WHITE,
            fg=TEXT,
            insertbackground=TEXT,
            relief="solid",
            bd=1,
        )
        entry.pack(side="left", fill="x", expand=True, ipady=8)

        self.field_vars[key] = var
        return entry

    def percent_field(self, parent, label, key, helper=""):
        wrapper = tk.Frame(parent, bg=CARD_BG)
        wrapper.pack(fill="x", padx=20, pady=8)

        tk.Label(
            wrapper,
            text=label,
            font=FONT_BODY,
            fg=TEXT,
            bg=CARD_BG,
        ).pack(anchor="w", pady=(0, 4))

        if helper:
            tk.Label(
                wrapper,
                text=helper,
                font=FONT_SMALL,
                fg=MUTED_2,
                bg=CARD_BG,
                wraplength=650,
                justify="left",
            ).pack(anchor="w", pady=(0, 5))

        row = tk.Frame(wrapper, bg=CARD_BG)
        row.pack(fill="x")

        var = tk.StringVar()
        entry = tk.Entry(
            row,
            textvariable=var,
            font=("Helvetica", 11),
            bg=WHITE,
            fg=TEXT,
            insertbackground=TEXT,
            relief="solid",
            bd=1,
        )
        entry.pack(side="left", fill="x", expand=True, ipady=8)

        tk.Label(
            row,
            text="%",
            font=("Helvetica", 11, "bold"),
            fg=MUTED,
            bg=WHITE,
            width=3,
        ).pack(side="left", ipady=9)

        self.field_vars[key] = var
        return entry

    def restore_values(self, mapping):
        for key, value in mapping.items():
            if key in self.field_vars and value not in (None, 0, 0.0):
                self.field_vars[key].set(str(value))

    # ========================================================
    # STEP 3A - INCOME
    # ========================================================
    def build_income_screen(self):
        self.clear()
        self.field_vars = {}

        shell, body, self.error_label = self.build_shell(
            "Step 3A of 3D",
            "Income",
            (
                "Start with the money that regularly comes in. Rough estimates are okay. "
                "Use monthly take-home amounts so we can understand what is actually available."
            ),
        )

        card = self.section_card(
            body,
            "Monthly Income",
            "Enter what typically reaches your household after taxes and payroll deductions.",
        )

        self.money_field(
            card,
            "Primary monthly take-home income",
            "primary_take_home",
            "Your typical monthly paycheck income after taxes.",
        )

        self.money_field(
            card,
            "Other recurring monthly income",
            "other_recurring_income",
            "Side work, rental income, support, or other predictable recurring income.",
        )

        self.money_field(
            card,
            "Average monthly variable income",
            "variable_income",
            "Average bonuses, commissions, tips, or irregular income across a normal year.",
        )

        self.restore_values(self.financial_data["income"])

        self.build_footer(
            shell,
            "Step 3A of 3D",
            back_command=self.cancel,
            continue_command=self.save_income,
        )

    def save_income(self):
        primary = self.money_to_float(
            self.field_vars["primary_take_home"].get()
        )
        other = self.money_to_float(
            self.field_vars["other_recurring_income"].get()
        )
        variable = self.money_to_float(
            self.field_vars["variable_income"].get()
        )

        if None in (primary, other, variable):
            self.error_label.config(
                text="Please enter valid positive amounts. Leave unknown optional fields blank."
            )
            return

        self.financial_data["income"] = {
            "primary_take_home": primary,
            "other_recurring_income": other,
            "variable_income": variable,
        }

        self.build_spending_screen()

    # ========================================================
    # STEP 3B - MONTHLY SPENDING
    # ========================================================
    def build_spending_screen(self):
        self.clear()
        self.field_vars = {}

        shell, body, self.error_label = self.build_shell(
            "Step 3B of 3D",
            "Monthly Spending",
            (
                "Estimate what a normal month looks like. This does not need to be perfect. "
                "Later, linked accounts can replace estimates with actual spending data."
            ),
        )

        card = self.section_card(
            body,
            "Core Monthly Expenses",
            "Use average monthly amounts. Debt minimum payments are entered separately in Step 3D.",
        )

        spending_fields = [
            ("Housing", "housing", "Rent or housing contribution. Enter mortgage principal/interest in Debt; count taxes and insurance only once."),
            ("Utilities", "utilities", "Electricity, gas, water, internet, and phone."),
            ("Groceries", "groceries", "Food purchased for home."),
            ("Dining & coffee", "dining", "Restaurants, takeout, coffee, and similar spending."),
            ("Transportation", "transportation", "Gas, transit, parking, maintenance, rideshare, excluding loan payments."),
            ("Insurance", "insurance", "Health, auto, renters/home, life, or other insurance paid personally."),
            ("Subscriptions", "subscriptions", "Streaming, software, memberships, and recurring services."),
            ("Entertainment & personal", "entertainment", "Shopping, hobbies, events, personal care, and discretionary spending."),
            ("Childcare / dependents", "dependents_spending", "Childcare, dependent support, or recurring family obligations."),
            ("Other recurring spending", "other_spending", "Any recurring monthly spending not captured above."),
        ]

        for label, key, helper in spending_fields:
            self.money_field(card, label, key, helper)

        self.restore_values(self.financial_data["spending"])

        self.build_footer(
            shell,
            "Step 3B of 3D",
            back_command=lambda: self.save_spending(back=True),
            continue_command=self.save_spending,
        )

    def save_spending(self, back=False):
        spending = {}

        for key, var in self.field_vars.items():
            value = self.money_to_float(var.get())

            if value is None:
                self.error_label.config(
                    text="Please enter valid positive amounts. Leave categories at 0 or blank if they do not apply."
                )
                return

            spending[key] = value

        self.financial_data["spending"] = spending
        if back:
            self.build_income_screen()
        else:
            self.build_accounts_screen()

    # ========================================================
    # STEP 3C - ACCOUNTS & SAVINGS
    # ========================================================
    def build_accounts_screen(self):
        self.clear()
        self.field_vars = {}
        shell, body, self.error_label = self.build_shell(
            "Step 3C of 3D", "Accounts & Savings",
            "Select only the account types you have, then add each account separately. Zero-balance accounts are welcome.")
        self.build_account_picker(body, CASH_TYPES)
        card = self.section_card(body, "Emergency savings", "This is part of your cash balances above, not extra money.")
        self.money_field(card, "Cash reserved for emergencies", "emergency_fund")
        self.restore_values(self.financial_data["accounts"])
        self.build_footer(shell, "Step 3C of 3D", self.back_from_accounts, self.save_accounts)
        if self.app_state.get("financial_complete"):
            AppButton(card, "Save changes & return", lambda: self.save_accounts(finish=True)).pack(padx=20, pady=12)

    def capture_accounts(self):
        amount = self.money_to_float(self.field_vars["emergency_fund"].get())
        cash = sum(x["balance"] for x in self.account_entries if x["type"] in CASH_TYPES)
        if amount is None or amount > cash:
            self.error_label.config(text="Emergency savings must be a valid amount no greater than total cash.")
            return False
        self.financial_data["accounts"]["emergency_fund"] = amount
        return True

    def back_from_accounts(self):
        if self.capture_accounts():
            self.build_spending_screen()

    def save_accounts(self, finish=False):
        if self.capture_accounts():
            if finish:
                self.finish_financial_profile()
            else:
                self.build_debt_investment_screen()

    def build_account_picker(self, parent, types):
        card = self.section_card(parent, "Which accounts do you have?", "Check a type to add accounts. You can add several from the same bank or provider.")
        for key, label in types.items():
            block = tk.Frame(card, bg=CARD_BG)
            block.pack(fill="x", padx=20, pady=4)
            enabled = tk.BooleanVar(value=any(x["type"] == key for x in self.account_entries))
            details = tk.Frame(block, bg=CARD_BG)
            self.account_areas[key] = details
            def renderer(k=key, area=details):
                self.render_accounts(k, area)
            def toggle(k=key, var=enabled, area=details, r=renderer):
                if var.get():
                    area.pack(fill="x", padx=12)
                    r()
                else:
                    matching = [x for x in self.account_entries if x["type"] == k]
                    if matching and not messagebox.askyesno("Remove accounts?", "Remove all accounts of this type from this draft?", parent=self):
                        var.set(True)
                        return
                    self.account_entries[:] = [x for x in self.account_entries if x["type"] != k]
                    area.pack_forget()
                    self.refresh_all_accounts()
            tk.Checkbutton(block, text=label, variable=enabled, command=toggle,
                           bg=CARD_BG, fg=TEXT, selectcolor=WHITE, activeforeground=TEXT,
                           activebackground=CARD_BG).pack(anchor="w")
            if enabled.get():
                details.pack(fill="x", padx=12)
                renderer()

    def refresh_all_accounts(self):
        for key, area in self.account_areas.items():
            self.render_accounts(key, area)

    def render_accounts(self, key, area):
        for widget in area.winfo_children():
            widget.destroy()
        refresh = self.refresh_all_accounts
        for index, item in enumerate(self.account_entries):
            if item["type"] != key:
                continue
            row = tk.Frame(area, bg=CARD_BG)
            row.pack(fill="x", pady=4)
            text = f'{item["name"]} | {item.get("provider", "")} | ${item["balance"]:,.2f}'
            tk.Label(row, text=text, bg=CARD_BG, fg=TEXT, wraplength=380, justify="left").pack(side="left")
            AppButton(row, "Edit", lambda i=index: self.open_account_entry(key, refresh, i), padx=8, pady=5).pack(side="right")
            AppButton(row, "Remove", lambda i=index: self.remove_account(i, refresh), padx=8, pady=5).pack(side="right", padx=5)
        AppButton(area, "Add account", lambda: self.open_account_entry(key, refresh), padx=12, pady=6).pack(anchor="w", pady=5)

    def remove_account(self, index, refresh):
        if messagebox.askyesno("Remove account?", "Remove this account from the draft?", parent=self):
            self.account_entries.pop(index)
            refresh()

    def open_account_entry(self, key, refresh, index=None):
        item = self.account_entries[index] if index is not None else {}
        popup = tk.Toplevel(self)
        popup.title("Edit account" if item else "Add account")
        popup.geometry("520x410")
        popup.configure(bg=MAIN_BG)
        popup.transient(self)
        popup.grab_set()
        values = {}
        for field, label in (("name", "Account nickname (e.g., Everyday checking)"),
                             ("provider", "Bank / provider (optional)"), ("balance", "Current balance ($)")):
            tk.Label(popup, text=label, bg=MAIN_BG, fg=TEXT).pack(anchor="w", padx=24, pady=(14, 4))
            var = tk.StringVar(value=item.get(field, ""))
            tk.Entry(popup, textvariable=var, bg=WHITE, fg=TEXT, insertbackground=TEXT).pack(fill="x", padx=24, ipady=7)
            values[field] = var
        error = tk.Label(popup, text="", bg=MAIN_BG, fg=RED)
        error.pack(pady=10)
        def close():
            popup.destroy()
            self.grab_set()
        def save():
            balance = self.money_to_float(values["balance"].get())
            if not values["name"].get().strip() or not values["balance"].get().strip() or balance is None:
                error.config(text="Enter an account name and a valid balance (0 is allowed).")
                return
            updated = dict(type=key, name=values["name"].get().strip(), provider=values["provider"].get().strip(), balance=balance)
            if index is None:
                self.account_entries.append(updated)
            else:
                self.account_entries[index] = updated
            close()
            refresh()
        AppButton(popup, "Save account", save).pack(pady=8)
        popup.protocol("WM_DELETE_WINDOW", close)

    # ========================================================
    # STEP 3D - DEBT & INVESTMENTS
    # ========================================================
    def build_debt_investment_screen(self):
        self.clear()
        self.field_vars = {}

        shell, body, self.error_label = self.build_shell(
            "Step 3D of 3D",
            "Debt & Investments",
            (
                "Finish with what you owe, what you already have invested, and any employer benefits. "
                "Only add the debts you actually have."
            ),
        )

        debt_card = self.section_card(
            body,
            "Debt",
            (
                "Add each debt separately. This is especially important for student loans, "
                "because different loans can have different interest rates."
            ),
        )

        tk.Label(
            debt_card,
            text="Do you currently have debt?",
            font=FONT_BODY,
            fg=TEXT,
            bg=CARD_BG,
        ).pack(anchor="w", padx=20, pady=(8, 6))

        debt_choice_row = tk.Frame(debt_card, bg=CARD_BG)
        debt_choice_row.pack(fill="x", padx=20, pady=(0, 10))

        self.has_debt_var = tk.StringVar(
            value="Yes" if self.debt_entries else "No"
        )

        for label in ["No", "Yes"]:
            tk.Radiobutton(
                debt_choice_row,
                text=label,
                variable=self.has_debt_var,
                value=label,
                font=FONT_BODY,
                fg=TEXT,
                bg=CARD_BG,
                selectcolor="#DCE8FF",
                activebackground=CARD_BG,
                activeforeground=TEXT,
                cursor="arrow",
                command=self.toggle_debt_area,
            ).pack(side="left", padx=(0, 18))

        self.debt_area = tk.Frame(debt_card, bg=CARD_BG)
        self.debt_area.pack(fill="x", padx=20, pady=(0, 14))

        self.render_debt_area()

        self.build_account_picker(body, INVESTMENT_TYPES)

        benefits_card = self.section_card(
            body,
            "Employer Retirement Benefits",
            "These fields help identify whether employer match is being left unused.",
        )

        self.percent_field(
            benefits_card,
            "Your current retirement contribution",
            "current_retirement_contribution",
            "Enter the percent of pay you currently contribute.",
        )

        self.percent_field(
            benefits_card,
            "Employer match available",
            "employer_match",
            "Enter the maximum employer match as a percent of pay, if known.",
        )

        self.restore_debt_and_investment_values()

        self.build_footer(
            shell,
            "Step 3D of 3D",
            back_command=lambda: self.save_debt_and_investments(back=True),
            continue_command=self.save_debt_and_investments,
            continue_text="Save financial profile",
        )

    def toggle_debt_area(self):
        self.render_debt_area()

    def render_debt_area(self):
        for child in self.debt_area.winfo_children():
            child.destroy()

        if self.has_debt_var.get() != "Yes":
            tk.Label(
                self.debt_area,
                text="No debt selected.",
                font=FONT_SMALL,
                fg=MUTED,
                bg=CARD_BG,
            ).pack(anchor="w")
            return

        tk.Label(
            self.debt_area,
            text="Add each account or loan separately.",
            font=FONT_SMALL,
            fg=MUTED,
            bg=CARD_BG,
        ).pack(anchor="w", pady=(0, 8))

        controls = tk.Frame(self.debt_area, bg=CARD_BG)
        controls.pack(fill="x", pady=(0, 10))

        self.debt_type_var = tk.StringVar(value="Select debt type")
        debt_type_menu = tk.OptionMenu(
            controls,
            self.debt_type_var,
            "Credit card",
            "Student loan",
            "Auto loan",
            "Personal loan",
            "Mortgage",
            "Medical debt",
            "Other debt",
        )
        debt_type_menu.config(
            font=FONT_BODY,
            bg="#F8FAFC",
            fg=TEXT,
            activebackground="#EAF0F8",
            relief="solid",
            bd=1,
            cursor="arrow",
        )
        debt_type_menu["menu"].config(
            font=FONT_BODY,
            bg=WHITE,
            fg=TEXT,
        )
        debt_type_menu.pack(side="left", fill="x", expand=True)

        AppButton(
            controls,
            text="Add Debt",
            command=self.open_debt_entry,
            padx=14,
            pady=8,
        ).pack(side="right", padx=(10, 0))

        if self.debt_entries:
            tk.Label(
                self.debt_area,
                text="Added debts",
                font=FONT_SUBHEADER,
                fg=TEXT,
                bg=CARD_BG,
            ).pack(anchor="w", pady=(6, 4))

        for index, item in enumerate(self.debt_entries):
            row = tk.Frame(
                self.debt_area,
                bg="#F8FAFC",
                highlightbackground=CARD_BORDER,
                highlightthickness=1,
            )
            row.pack(fill="x", pady=4)

            left = tk.Frame(row, bg="#F8FAFC")
            left.pack(side="left", fill="x", expand=True, padx=12, pady=10)

            tk.Label(
                left,
                text=item["name"] + (" • " + item["provider"] if item.get("provider") else ""),
                font=FONT_SUBHEADER,
                fg=TEXT,
                bg="#F8FAFC",
            ).pack(anchor="w")

            detail = (
                f'{self.format_money(item["balance"])} balance'
                f'  •  {item["apr"]:.2f}% APR'
                f'  •  {self.format_money(item["minimum_payment"])} minimum'
            )

            tk.Label(
                left,
                text=detail,
                font=FONT_SMALL,
                fg=MUTED,
                bg="#F8FAFC",
            ).pack(anchor="w", pady=(2, 0))

            AppButton(row, text="Edit", command=lambda i=index: self.open_debt_entry(i), padx=10, pady=6).pack(side="right", padx=5)
            AppButton(
                row,
                text="Remove",
                command=lambda i=index: self.remove_debt(i),
                bg="#E8EDF4",
                fg=TEXT,
                hover_bg="#DCE3EC",
                padx=10,
                pady=6,
            ).pack(side="right", padx=10)

    def open_debt_entry(self, index=None):
        existing = self.debt_entries[index] if index is not None else {}
        debt_type = existing.get("type", self.debt_type_var.get().strip())

        if debt_type == "Select debt type":
            self.error_label.config(
                text="Please select a debt type before adding it."
            )
            return

        popup = tk.Toplevel(self)
        popup.title(f"Add {debt_type}")
        popup.geometry("560x660")
        popup.configure(bg=MAIN_BG)
        popup.transient(self)
        popup.grab_set()

        def close_popup():
            popup.destroy()
            self.grab_set()
        popup.protocol("WM_DELETE_WINDOW", close_popup)

        container = tk.Frame(popup, bg=MAIN_BG)
        container.pack(fill="both", expand=True, padx=28, pady=26)

        tk.Label(
            container,
            text=f"Add {debt_type}",
            font=FONT_TITLE,
            fg=TEXT,
            bg=MAIN_BG,
        ).pack(anchor="w")

        tk.Label(
            container,
            text=(
                "Enter this account separately so its balance and interest rate "
                "can be evaluated correctly."
            ),
            font=FONT_BODY,
            fg=MUTED,
            bg=MAIN_BG,
            wraplength=440,
            justify="left",
        ).pack(anchor="w", pady=(5, 14))

        card = tk.Frame(
            container,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        card.pack(fill="x")

        name_var = tk.StringVar()
        balance_var = tk.StringVar()
        apr_var = tk.StringVar()
        minimum_var = tk.StringVar()
        provider_var = tk.StringVar(value=existing.get("provider", ""))

        def popup_entry(label, variable, helper=""):
            wrapper = tk.Frame(card, bg=CARD_BG)
            wrapper.pack(fill="x", padx=18, pady=8)

            tk.Label(
                wrapper,
                text=label,
                font=FONT_BODY,
                fg=TEXT,
                bg=CARD_BG,
            ).pack(anchor="w", pady=(0, 4))

            if helper:
                tk.Label(
                    wrapper,
                    text=helper,
                    font=FONT_SMALL,
                    fg=MUTED_2,
                    bg=CARD_BG,
                ).pack(anchor="w", pady=(0, 4))

            entry = tk.Entry(
                wrapper,
                textvariable=variable,
                font=("Helvetica", 11),
                bg=WHITE,
                fg=TEXT,
                insertbackground=TEXT,
                relief="solid",
                bd=1,
            )
            entry.pack(fill="x", ipady=8)

        default_name = debt_type
        if debt_type == "Student loan":
            default_name = f"Student loan {len([d for d in self.debt_entries if d['type'] == 'Student loan']) + 1}"
        elif debt_type == "Credit card":
            default_name = f"Credit card {len([d for d in self.debt_entries if d['type'] == 'Credit card']) + 1}"

        name_var.set(existing.get("name", default_name))
        balance_var.set(existing.get("balance", ""))
        apr_var.set(existing.get("apr", ""))
        minimum_var.set(existing.get("minimum_payment", ""))

        popup_entry(
            "Account / loan name",
            name_var,
            "Example: Federal Loan 2025, Discover Card, Auto Loan.",
        )
        popup_entry("Lender / card issuer (optional)", provider_var)
        popup_entry("Current balance", balance_var)
        popup_entry("APR / interest rate (%)", apr_var)
        popup_entry("Required monthly payment", minimum_var)

        popup_error = tk.Label(
            container,
            text="",
            font=FONT_SMALL,
            fg=RED,
            bg=MAIN_BG,
        )
        popup_error.pack(anchor="w", pady=(8, 0))

        def save_debt():
            name = name_var.get().strip()
            balance = self.money_to_float(balance_var.get())
            apr = self.percent_to_float(apr_var.get())
            minimum = self.money_to_float(minimum_var.get())

            if not name:
                popup_error.config(text="Please enter a name for this debt.")
                return

            if any(not v.get().strip() for v in (balance_var, apr_var, minimum_var)) or None in (balance, apr, minimum):
                popup_error.config(
                    text="Please enter valid balance, APR, and payment values."
                )
                return

            if balance < 0:
                popup_error.config(
                    text="Debt balance cannot be negative."
                )
                return

            updated = {
                "provider": provider_var.get().strip(),
                "type": debt_type,
                "name": name,
                "balance": balance,
                "apr": apr,
                "minimum_payment": minimum,
            }
            if index is None:
                self.debt_entries.append(updated)
            else:
                self.debt_entries[index] = updated
            popup.destroy()
            self.grab_set()
            self.render_debt_area()

        AppButton(
            container,
            text="Save Debt",
            command=save_debt,
        ).pack(anchor="e", pady=(14, 0))

    def remove_debt(self, index):
        if 0 <= index < len(self.debt_entries) and messagebox.askyesno("Remove debt?", "Remove this debt from the draft?", parent=self):
            self.debt_entries.pop(index)

        self.render_debt_area()

    def restore_debt_and_investment_values(self):
        flat = {}
        flat.update(self.financial_data["investments"])
        flat.update(self.financial_data["benefits"])

        for key, value in flat.items():
            if key in self.field_vars and value not in (None, 0, 0.0):
                self.field_vars[key].set(str(value))

    def save_debt_and_investments(self, back=False):
        debt = []

        if self.has_debt_var.get() == "Yes":
            debt = self.debt_entries.copy()

            if not debt:
                self.error_label.config(
                    text="You selected Yes for debt. Please add at least one debt account."
                )
                return

        if self.has_debt_var.get() != "Yes" and self.debt_entries:
            if not messagebox.askyesno("Clear debts?", "You selected no debt. Saving will remove the listed debts. Continue?", parent=self):
                return

        current_contribution = self.percent_to_float(
            self.field_vars["current_retirement_contribution"].get()
        )
        employer_match = self.percent_to_float(
            self.field_vars["employer_match"].get()
        )

        if None in (current_contribution, employer_match):
            self.error_label.config(
                text="Please enter valid retirement contribution percentages between 0 and 100."
            )
            return

        benefits = {
            "current_retirement_contribution": current_contribution,
            "employer_match": employer_match,
        }

        self.financial_data["debt"] = debt
        self.debt_entries = deepcopy(debt)
        self.financial_data["benefits"] = benefits

        if back:
            self.build_accounts_screen()
        else:
            self.finish_financial_profile()

    # ========================================================
    # DERIVED FINANCIAL METRICS
    # ========================================================
    def finish_financial_profile(self):
        self.financial_data["account_entries"] = deepcopy(self.account_entries)
        for group, types in (("accounts", CASH_TYPES), ("investments", INVESTMENT_TYPES)):
            for key in types:
                self.financial_data[group][key] = sum(x["balance"] for x in self.account_entries if x["type"] == key)
        self.financial_data["accounts"].setdefault("emergency_fund", 0)
        self.financial_data["debt"] = deepcopy(self.financial_data.get("debt", self.debt_entries))
        cash = sum(self.financial_data["accounts"][key] for key in CASH_TYPES)
        if self.financial_data["accounts"]["emergency_fund"] > cash:
            self.error_label.config(text="Emergency savings exceeds cash. Review Accounts & Savings before saving.")
            return
        metrics = calculate_metrics(self.financial_data)

        self.app_state["financial"] = self.financial_data
        self.app_state["financial_metrics"] = metrics
        self.app_state["financial_complete"] = True
        self.app_state["onboarding_complete"] = bool(self.app_state.get("personal_complete") and self.app_state.get("behavioral_complete"))

        save_state(self.app_state)

        self.finish()

    # ========================================================
    # COMPLETE SCREEN
    # ========================================================
    def show_completion_screen(self):
        self.clear()

        metrics = self.app_state["financial_metrics"]

        outer = tk.Frame(self, bg=MAIN_BG)
        outer.pack(
            fill="both",
            expand=True,
            padx=36,
            pady=30,
        )

        tk.Label(
            outer,
            text="Profile complete",
            font=FONT_SMALL,
            fg=GREEN,
            bg=MAIN_BG,
        ).pack(anchor="w")

        tk.Label(
            outer,
            text="Your Financial Profile Is Ready",
            font=FONT_TITLE,
            fg=TEXT,
            bg=MAIN_BG,
        ).pack(
            anchor="w",
            pady=(4, 6),
        )

        tk.Label(
            outer,
            text=(
                "Next Best Dollar now has the starting information needed to understand "
                "your financial position. Goals and the decision engine will build on this later."
            ),
            font=FONT_BODY,
            fg=MUTED,
            bg=MAIN_BG,
            wraplength=690,
            justify="left",
        ).pack(
            anchor="w",
            pady=(0, 18),
        )

        summary = tk.Frame(
            outer,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        summary.pack(fill="x")

        summary_rows = [
            (
                "Monthly income",
                self.format_money(metrics["monthly_income"]),
            ),
            (
                "Monthly total outflow",
                self.format_money(metrics["monthly_total_outflow"]),
            ),
            (
                "Monthly free cash flow",
                self.format_money(metrics["monthly_free_cash_flow"]),
            ),
            (
                "Liquid cash",
                self.format_money(metrics["liquid_cash"]),
            ),
            (
                "Total debt",
                self.format_money(metrics["total_debt"]),
            ),
            (
                "Total investments",
                self.format_money(metrics["total_investments"]),
            ),
            (
                "Net financial position",
                self.format_money(metrics["net_financial_position"]),
            ),
        ]

        for label, value in summary_rows:
            row = tk.Frame(summary, bg=CARD_BG)
            row.pack(fill="x", padx=18, pady=8)

            tk.Label(
                row,
                text=label,
                font=FONT_BODY,
                fg=MUTED,
                bg=CARD_BG,
                width=25,
                anchor="w",
            ).pack(side="left")

            tk.Label(
                row,
                text=value,
                font=FONT_SUBHEADER,
                fg=TEXT,
                bg=CARD_BG,
            ).pack(side="left")

        AppButton(
            outer,
            text="Return to Dashboard",
            command=self.finish,
        ).pack(
            anchor="e",
            pady=(18, 0),
        )

    # ========================================================
    # NAVIGATION
    # ========================================================
    def go_back_to_behavioral(self):
        self.destroy()

        from behavioral import BehavioralFlow

        BehavioralFlow(
            self.parent,
            self.app_state,
            on_complete=self.on_complete,
        )

    def finish(self):
        if self.on_complete:
            self.on_complete()

        self.destroy()
