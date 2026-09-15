import tkinter as tk
from tkinter import ttk
from datetime import datetime, date

from storage import save_state

# ============================================================
# NEXT BEST DOLLAR
# PERSONAL FACTS MODULE
# ============================================================

MAIN_BG = "#F2F5F9"
CARD_BG = "#FFFFFF"
CARD_BORDER = "#D4DCE7"

PRIMARY = "#2F6BFF"
PRIMARY_HOVER = "#2458D8"

TEXT = "#1A2233"
MUTED = "#596579"
WHITE = "#FFFFFF"
RED = "#D64545"

FONT_TITLE = ("Helvetica", 22, "bold")
FONT_BODY = ("Helvetica", 10)
FONT_SMALL = ("Helvetica", 9)
FONT_BUTTON = ("Helvetica", 11, "bold")


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
        pady=10
    ):
        super().__init__(
            parent,
            text=text,
            bg=bg,
            fg=fg,
            font=FONT_BUTTON,
            padx=padx,
            pady=pady,
            cursor="arrow"
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


class SmartCombobox(ttk.Combobox):
    def __init__(self, parent, values, textvariable=None, **kwargs):
        self.original_values = [str(value) for value in values]

        super().__init__(
            parent,
            values=self.original_values,
            textvariable=textvariable,
            state="normal",
            **kwargs
        )

        self.bind("<KeyRelease>", self._filter_values)
        self.bind("<Button-1>", self._open_dropdown, add="+")
        self.bind("<FocusIn>", self._restore_values, add="+")

    def _open_dropdown(self, event=None):
        self["values"] = self.original_values
        self.after(1, lambda: self.event_generate("<Down>"))

    def _restore_values(self, event=None):
        if not self.get().strip():
            self["values"] = self.original_values

    def _filter_values(self, event):
        if event.keysym in (
            "Up", "Down", "Left", "Right",
            "Return", "Tab", "Escape"
        ):
            return

        typed = self.get().strip().lower()

        if not typed:
            matches = self.original_values
        else:
            matches = [
                value
                for value in self.original_values
                if value.lower().startswith(typed)
            ]

        self["values"] = matches if matches else self.original_values


def calculate_age(date_of_birth):
    today = date.today()

    years = today.year - date_of_birth.year

    if (today.month, today.day) < (
        date_of_birth.month,
        date_of_birth.day
    ):
        years -= 1

    return years


def calculate_personal_scores(personal):
    age = personal["age"]
    dependents = personal["dependents"]

    if age <= 25:
        time_horizon_capacity = 5.0
    elif age <= 35:
        time_horizon_capacity = 4.5
    elif age <= 45:
        time_horizon_capacity = 4.0
    elif age <= 55:
        time_horizon_capacity = 3.0
    elif age <= 65:
        time_horizon_capacity = 2.0
    else:
        time_horizon_capacity = 1.5

    income_stability_map = {
        "Very stable": 5.0,
        "Mostly stable": 4.0,
        "Somewhat variable": 3.0,
        "Highly variable": 2.0,
        "No current income": 1.0,
    }

    knowledge_map = {
        "Beginner": 1.0,
        "Basic": 2.0,
        "Intermediate": 3.5,
        "Advanced": 5.0,
    }

    if dependents == 0:
        household_flexibility = 5.0
    elif dependents == 1:
        household_flexibility = 4.0
    elif dependents == 2:
        household_flexibility = 3.0
    elif dependents == 3:
        household_flexibility = 2.0
    else:
        household_flexibility = 1.0

    return {
        "time_horizon_capacity": time_horizon_capacity,
        "income_stability": income_stability_map.get(
            personal["income_stability"],
            3.0
        ),
        "household_flexibility": household_flexibility,
        "financial_knowledge": knowledge_map.get(
            personal["financial_experience"],
            2.0
        ),
    }


class OnboardingFlow(tk.Toplevel):
    def __init__(self, parent, app_state, on_complete=None, edit_only=False):
        super().__init__(parent)

        self.parent = parent
        self.app_state = app_state
        self.on_complete = on_complete
        self.edit_only = edit_only

        self.title("Next Best Dollar - Personal Facts")
        self.geometry("780x790")
        self.minsize(700, 650)
        self.configure(bg=MAIN_BG)
        self.transient(parent)
        self.grab_set()

        self.vars = {}

        self.configure_style()
        self.build_screen()

    def configure_style(self):
        style = ttk.Style(self)

        try:
            style.theme_use("clam")
        except Exception:
            pass

        style.configure(
            "NBD.TCombobox",
            fieldbackground=WHITE,
            background=WHITE,
            foreground=TEXT,
            arrowcolor=MUTED,
            bordercolor=CARD_BORDER,
            lightcolor=CARD_BORDER,
            darkcolor=CARD_BORDER,
            padding=8
        )

        style.map(
            "NBD.TCombobox",
            bordercolor=[("focus", PRIMARY)]
        )

    def clear(self):
        for widget in self.winfo_children():
            widget.destroy()

    def field_wrapper(self, parent, label):
        wrapper = tk.Frame(parent, bg=CARD_BG)
        wrapper.pack(fill="x", padx=22, pady=8)

        tk.Label(
            wrapper,
            text=label,
            font=FONT_BODY,
            fg=TEXT,
            bg=CARD_BG
        ).pack(anchor="w", pady=(0, 5))

        return wrapper

    def text_field(self, parent, label, key):
        wrapper = self.field_wrapper(parent, label)

        var = tk.StringVar()

        entry = tk.Entry(
            wrapper,
            textvariable=var,
            font=("Helvetica", 11),
            bg=WHITE,
            fg=TEXT,
            insertbackground=TEXT,
            relief="solid",
            bd=1
        )
        entry.pack(fill="x", ipady=8)

        self.vars[key] = var
        return entry

    def combo_field(self, parent, label, key, options):
        wrapper = self.field_wrapper(parent, label)

        var = tk.StringVar(value="Select")

        combo = SmartCombobox(
            wrapper,
            values=options,
            textvariable=var,
            style="NBD.TCombobox",
            font=("Helvetica", 11)
        )
        combo.pack(fill="x")

        def highlight_placeholder(event):
            if combo.get() == "Select":
                combo.selection_range(0, tk.END)

        combo.bind("<FocusIn>", highlight_placeholder, add="+")

        self.vars[key] = var
        return combo

    def build_screen(self):
        self.clear()

        shell = tk.Frame(self, bg=MAIN_BG)
        shell.pack(fill="both", expand=True)

        header = tk.Frame(shell, bg=MAIN_BG)
        header.pack(fill="x", padx=36, pady=(26, 12))

        tk.Label(
            header,
            text="Step 1 of 3",
            font=FONT_SMALL,
            fg=PRIMARY,
            bg=MAIN_BG
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Personal Facts",
            font=FONT_TITLE,
            fg=TEXT,
            bg=MAIN_BG
        ).pack(anchor="w", pady=(4, 6))

        tk.Label(
            header,
            text=(
                "Tell us about your current situation. "
                "These answers provide context for future financial decisions."
            ),
            font=FONT_BODY,
            fg=MUTED,
            bg=MAIN_BG,
            wraplength=650,
            justify="left"
        ).pack(anchor="w")

        body = tk.Frame(shell, bg=MAIN_BG)
        body.pack(fill="both", expand=True, padx=36)

        canvas = tk.Canvas(
            body,
            bg=MAIN_BG,
            highlightthickness=0
        )

        scrollbar = tk.Scrollbar(
            body,
            orient="vertical",
            command=canvas.yview
        )

        scroll_frame = tk.Frame(canvas, bg=MAIN_BG)

        window_id = canvas.create_window(
            (0, 0),
            window=scroll_frame,
            anchor="nw"
        )

        scroll_frame.bind(
            "<Configure>",
            lambda event: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )

        canvas.bind(
            "<Configure>",
            lambda event: canvas.itemconfigure(
                window_id,
                width=event.width
            )
        )

        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        card = tk.Frame(
            scroll_frame,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1
        )
        card.pack(fill="x", pady=(4, 14))

        self.text_field(
            card,
            "First name",
            "first_name"
        )

        self.text_field(
            card,
            "Last name",
            "last_name"
        )

        from calendar_picker import DatePicker
        from occupation import SECTORS, prompt
        wrapper=self.field_wrapper(card, "Date of birth")
        self.vars['dob_text']=tk.StringVar()
        DatePicker(wrapper,self.vars['dob_text'],fmt='%m/%d/%Y',birth=True).pack(fill='x')
        self.combo_field(card, "What are you doing currently?", "employment_status",
                         ["Full-time","Part-time","Self-employed","Student","Not currently employed","Retired"])
        context=tk.Frame(card,bg=CARD_BG);context.pack(fill='x')
        school=tk.Frame(context,bg=CARD_BG)
        self.text_field(school,"School / university (optional)","school_name")
        self.text_field(school,"Program / field of study (optional)","study_program")
        self.combo_field(school,"Are you also working?","student_work",['No','Yes'])
        work=tk.Frame(context,bg=CARD_BG)
        self.text_field(work,"Employer / business name (optional)","employer_name")
        self.text_field(work,"Occupation / job title (optional)","occupation")
        self.combo_field(work,"Employer / work type","work_sector",SECTORS)
        hint=tk.Label(work,text='',bg=CARD_BG,fg=MUTED,wraplength=580,justify='left');hint.pack(fill='x',padx=20,pady=8)
        self.vars['work_sector'].trace_add('write',lambda *args:hint.config(text=prompt(self.vars['work_sector'].get())))
        self.combo_field(work,"Do you have a workplace or business retirement savings plan?","retirement_access",['Not sure','Yes','No'])
        plan=tk.Frame(work,bg=CARD_BG)
        self.text_field(plan,"Plan name / type, if known (optional)","retirement_plan_name")
        def update_context(*args):
            from profile_context import active_context
            status=self.vars['employment_status'].get()
            active=active_context(status,self.vars['student_work'].get())
            school.pack_forget();work.pack_forget();plan.pack_forget()
            if status=='Student':school.pack(fill='x')
            if 'occupation' in active:
                work.pack(fill='x')
                if self.vars['retirement_access'].get()=='Yes':plan.pack(fill='x')
        for key in ('employment_status','student_work','retirement_access'):
            self.vars[key].trace_add('write',update_context)
        self.vars['student_work'].set('No')
        update_context()

        self.combo_field(
            card,
            "How stable is your income?",
            "income_stability",
            [
                "Very stable",
                "Mostly stable",
                "Somewhat variable",
                "Highly variable",
                "No current income"
            ]
        )

        self.combo_field(
            card,
            "Relationship / marital status",
            "marital_status",
            [
                "Single",
                "In a relationship",
                "Engaged",
                "Married",
                "Separated / divorced",
                "Widowed"
            ]
        )

        self.combo_field(
            card,
            "Number of dependents",
            "dependents",
            [str(number) for number in range(0, 21)]
        )

        self.combo_field(
            card,
            "Current housing situation",
            "housing_status",
            [
                "Living with family",
                "Renting",
                "Own with mortgage",
                "Own without mortgage",
                "Other"
            ]
        )

        self.combo_field(
            card,
            "How do you currently manage your finances?",
            "finance_management",
            [
                "Individually",
                "Jointly with a partner",
                "Mostly individually",
                "Mostly handled by someone else"
            ]
        )

        self.combo_field(
            card,
            "How would you describe your financial knowledge?",
            "financial_experience",
            [
                "Beginner",
                "Basic",
                "Intermediate",
                "Advanced"
            ]
        )

        # Restore existing values if user is editing.
        existing = self.app_state.get("personal", {})

        for key in [
            "first_name",
            "last_name",
            "employment_status",
            "income_stability",
            "marital_status",
            "dependents",
            "housing_status",
            "finance_management",
            "financial_experience"
        ]:
            if key in existing and key in self.vars:
                self.vars[key].set(str(existing[key]))

        for key in ("occupation","work_sector","retirement_access","retirement_plan_name","employer_name","school_name","study_program","student_work"):
            self.vars[key].set(existing.get(key, "Not specified" if key=="work_sector" else "Not sure" if key=="retirement_access" else "No" if key=="student_work" else ""))

        if existing.get("date_of_birth"):
            try:
                dob = datetime.strptime(
                    existing["date_of_birth"],
                    "%Y-%m-%d"
                )

                self.vars["dob_text"].set(dob.strftime("%m/%d/%Y"))
            except Exception:
                pass

        self.error_label = tk.Label(
            shell,
            text="",
            font=FONT_SMALL,
            fg=RED,
            bg=MAIN_BG
        )
        self.error_label.pack(
            anchor="w",
            padx=36,
            pady=(6, 0)
        )

        footer = tk.Frame(
            shell,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1
        )
        footer.pack(fill="x", side="bottom")

        inner = tk.Frame(footer, bg=CARD_BG)
        inner.pack(fill="x", padx=36, pady=14)

        tk.Label(
            inner,
            text="Step 1 of 3",
            font=FONT_SMALL,
            fg=MUTED,
            bg=CARD_BG
        ).pack(side="left")

        AppButton(
            inner,
            text="Save changes" if self.edit_only else "Continue",
            command=self.save_and_continue
        ).pack(side="right")

    def save_and_continue(self):
        first_name = self.vars["first_name"].get().strip()
        last_name = self.vars["last_name"].get().strip()

        if not first_name:
            self.error_label.config(
                text="Please enter your first name."
            )
            return

        if not last_name:
            self.error_label.config(
                text="Please enter your last name."
            )
            return

        try:
            dob = datetime.strptime(self.vars["dob_text"].get().strip(), "%m/%d/%Y").date()
        except ValueError:
            self.error_label.config(text="Enter a valid birth date as MM/DD/YYYY, for example 05/21/2005.")
            return

        age = calculate_age(dob)

        if age < 16 or age > 100:
            self.error_label.config(
                text="Please enter a valid date of birth."
            )
            return

        required_selects = [
            ("employment_status", "Please select your employment status."),
            ("income_stability", "Please select your income stability."),
            ("marital_status", "Please select your relationship / marital status."),
            ("dependents", "Please select your number of dependents."),
            ("housing_status", "Please select your housing situation."),
            ("finance_management", "Please select how you manage your finances."),
            ("financial_experience", "Please select your financial knowledge level."),
        ]

        for key, message in required_selects:
            if self.vars[key].get().strip() in ("", "Select"):
                self.error_label.config(text=message)
                return

        personal = {
            **{k:self.vars[k].get().strip() for k in ("occupation","work_sector","retirement_access","retirement_plan_name","employer_name","school_name","study_program","student_work")},
            "first_name": first_name,
            "last_name": last_name,
            "date_of_birth": dob.isoformat(),
            "age": age,

            "employment_status":
                self.vars["employment_status"].get().strip(),

            "income_stability":
                self.vars["income_stability"].get().strip(),

            "marital_status":
                self.vars["marital_status"].get().strip(),

            "dependents":
                int(self.vars["dependents"].get().strip()),

            "housing_status":
                self.vars["housing_status"].get().strip(),

            "finance_management":
                self.vars["finance_management"].get().strip(),

            "financial_experience":
                self.vars["financial_experience"].get().strip(),
        }

        from profile_context import active_context
        active=active_context(personal['employment_status'],personal.get('student_work','No'))
        for key in ('employer_name','occupation','work_sector','retirement_access','retirement_plan_name','school_name','study_program','student_work'):
            if key not in active:personal[key]=''
        if personal.get('retirement_access')!='Yes':personal['retirement_plan_name']=''

        self.app_state["personal"] = personal
        self.app_state["personal_scores"] = (
            calculate_personal_scores(personal)
        )
        self.app_state["personal_complete"] = True

        save_state(self.app_state)

        if self.edit_only:
            self.destroy()
            if self.on_complete:
                self.on_complete()
            return

        self.destroy()

        # If Behavioral is already completed, skip it.
        if self.app_state.get("behavioral_complete"):
            from financial import FinancialFlow

            FinancialFlow(
                self.parent,
                self.app_state,
                on_complete=self.on_complete
            )
        else:
            from behavioral import BehavioralFlow

            BehavioralFlow(
                self.parent,
                self.app_state,
                on_complete=self.on_complete
            )
