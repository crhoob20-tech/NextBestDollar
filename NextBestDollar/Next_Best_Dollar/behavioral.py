import tkinter as tk
from storage import save_state

# ============================================================
# NEXT BEST DOLLAR
# BEHAVIORAL PROFILE MODULE
#
# This file owns:
# 1. The behavioral questions the user sees
# 2. The hidden scoring rules
# 3. Saving raw answers + hidden behavior scores
#
# Visible scale:
# 1 = Least likely
# 5 = Most likely
#
# IMPORTANT:
# Some questions are reverse-scored internally so the user
# cannot simply choose "5" for every statement to look better.
# ============================================================

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
WHITE = "#FFFFFF"

FONT_TITLE = ("Helvetica", 22, "bold")
FONT_HEADER = ("Helvetica", 14, "bold")
FONT_BODY = ("Helvetica", 10)
FONT_SMALL = ("Helvetica", 9)
FONT_BUTTON = ("Helvetica", 11, "bold")


# ============================================================
# BEHAVIORAL QUESTION BANK
#
# Each dimension has two questions.
# One question in several pairs is reverse-scored.
# ============================================================
BEHAVIORAL_QUESTIONS = [
    {
        "id": "discipline_01",
        "dimension": "discipline",
        "statement": (
            "If I set a financial target for the month, I usually stick to it "
            "even when something more enjoyable comes up."
        ),
        "reverse": False,
    },
    {
        "id": "discipline_02",
        "dimension": "discipline",
        "statement": (
            "I often start financial plans with good intentions but stop "
            "following them after a short period of time."
        ),
        "reverse": True,
    },

    {
        "id": "planning_01",
        "dimension": "planning",
        "statement": (
            "When I know a large expense is coming, I usually start preparing "
            "for it well before the payment is due."
        ),
        "reverse": False,
    },
    {
        "id": "planning_02",
        "dimension": "planning",
        "statement": (
            "I usually deal with financial obligations when they become urgent "
            "rather than planning for them ahead of time."
        ),
        "reverse": True,
    },

    {
        "id": "impulse_01",
        "dimension": "impulse_control",
        "statement": (
            "When I see something I really want, I often buy it first and "
            "figure out how it fits my finances afterward."
        ),
        "reverse": True,
    },
    {
        "id": "impulse_02",
        "dimension": "impulse_control",
        "statement": (
            "Before making an unplanned purchase, I usually give myself time "
            "to decide whether I still want it."
        ),
        "reverse": False,
    },

    {
        "id": "delay_01",
        "dimension": "delayed_gratification",
        "statement": (
            "I am comfortable delaying something I want now if doing so helps "
            "me reach a more important goal later."
        ),
        "reverse": False,
    },
    {
        "id": "delay_02",
        "dimension": "delayed_gratification",
        "statement": (
            "It is difficult for me to give up something enjoyable today for "
            "a financial benefit that may be years away."
        ),
        "reverse": True,
    },

    {
        "id": "loss_01",
        "dimension": "loss_tolerance",
        "statement": (
            "If a long-term investment fell significantly and my reason for "
            "owning it had not changed, I could avoid making a rushed decision."
        ),
        "reverse": False,
    },
    {
        "id": "loss_02",
        "dimension": "loss_tolerance",
        "statement": (
            "Seeing an investment lose money would make me want to reduce risk "
            "quickly, even if the money was intended for the long term."
        ),
        "reverse": True,
    },

    {
        "id": "uncertainty_01",
        "dimension": "uncertainty_tolerance",
        "statement": (
            "I can make an important financial decision without needing to feel "
            "completely certain about what will happen next."
        ),
        "reverse": False,
    },
    {
        "id": "uncertainty_02",
        "dimension": "uncertainty_tolerance",
        "statement": (
            "If a financial outcome is uncertain, I would usually rather avoid "
            "the decision than accept the possibility that it may not work out."
        ),
        "reverse": True,
    },
]


# ============================================================
# HIDDEN SCORING
# ============================================================
def calculate_behavior_scores(raw_answers):
    """
    Returns hidden 1.0-5.0 scores for each behavioral dimension.

    Raw answers are always the user's visible 1-5 selections.
    Reverse-scored items are transformed internally:
        1 -> 5
        2 -> 4
        3 -> 3
        4 -> 2
        5 -> 1
    """

    dimension_values = {}

    for question in BEHAVIORAL_QUESTIONS:
        raw_value = raw_answers[question["id"]]

        if question["reverse"]:
            scored_value = 6 - raw_value
        else:
            scored_value = raw_value

        dimension = question["dimension"]

        if dimension not in dimension_values:
            dimension_values[dimension] = []

        dimension_values[dimension].append(scored_value)

    scores = {
        dimension: round(sum(values) / len(values), 2)
        for dimension, values in dimension_values.items()
    }

    return scores


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
# BEHAVIORAL FLOW
# ============================================================
class BehavioralFlow(tk.Toplevel):
    def __init__(self, parent, app_state, on_complete=None, edit_only=False):
        super().__init__(parent)
        self._nbd_scrollbar_only = True

        self.parent = parent
        self.app_state = app_state
        self.on_complete = on_complete
        self.edit_only = edit_only

        self.title("Next Best Dollar - Behavioral Profile")
        self.geometry("780x760")
        self.minsize(700, 650)
        self.configure(bg=MAIN_BG)
        self.transient(parent)
        self.grab_set()

        self.answer_vars = {}

        self.build_screen()

    # ========================================================
    # SCREEN
    # ========================================================
    def build_screen(self):
        shell = tk.Frame(self, bg=MAIN_BG)
        shell.pack(fill="both", expand=True)

        # ---------------- HEADER ----------------
        header = tk.Frame(shell, bg=MAIN_BG)
        header.pack(fill="x", padx=36, pady=(26, 12))

        tk.Label(
            header,
            text="Step 2 of 3",
            font=FONT_SMALL,
            fg=PRIMARY,
            bg=MAIN_BG,
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Behavioral Profile",
            font=FONT_TITLE,
            fg=TEXT,
            bg=MAIN_BG,
        ).pack(anchor="w", pady=(4, 6))

        tk.Label(
            header,
            text=(
                "For each statement, choose how likely it is to describe what "
                "you would realistically do."
            ),
            font=FONT_BODY,
            fg=MUTED,
            bg=MAIN_BG,
            wraplength=670,
            justify="left",
        ).pack(anchor="w")

        # ---------------- SCROLLABLE BODY ----------------
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

        canvas.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        def on_mousewheel(event):
            try:
                canvas.yview_scroll(
                    int(-1 * (event.delta / 120)),
                    "units",
                )
            except Exception:
                pass

        # Wheel routing is installed once by the app.

        # ---------------- SCALE GUIDE ----------------
        guide = tk.Frame(
            scroll_frame,
            bg="#EAF0F8",
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        guide.pack(fill="x", pady=(4, 10))

        tk.Label(
            guide,
            text="1 = Least likely     •     5 = Most likely",
            font=("Helvetica", 10, "bold"),
            fg=TEXT,
            bg="#EAF0F8",
        ).pack(padx=16, pady=12)

        # ---------------- QUESTIONS ----------------
        for index, question in enumerate(BEHAVIORAL_QUESTIONS, start=1):
            self.add_question_card(
                scroll_frame,
                index,
                question,
            )

        # ---------------- ERROR MESSAGE ----------------
        self.error_label = tk.Label(
            shell,
            text="",
            font=FONT_SMALL,
            fg="#D64545",
            bg=MAIN_BG,
        )
        self.error_label.pack(
            anchor="w",
            padx=36,
            pady=(6, 0),
        )

        # ---------------- FIXED FOOTER ----------------
        footer = tk.Frame(
            shell,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        footer.pack(
            fill="x",
            side="bottom",
        )

        footer_inner = tk.Frame(
            footer,
            bg=CARD_BG,
        )
        footer_inner.pack(
            fill="x",
            padx=36,
            pady=14,
        )

        AppButton(
            footer_inner,
            text="Back",
            command=self.go_back,
            bg="#E8EDF4",
            fg=TEXT,
            hover_bg="#DCE3EC",
        ).pack(side="left")

        tk.Label(
            footer_inner,
            text="Step 2 of 3",
            font=FONT_SMALL,
            fg=MUTED,
            bg=CARD_BG,
        ).pack(
            side="left",
            padx=18,
        )

        AppButton(
            footer_inner,
            text="Save changes" if self.edit_only else "Continue",
            command=self.save_and_continue,
        ).pack(side="right")

    # ========================================================
    # QUESTION CARD
    # ========================================================
    def add_question_card(self, parent, index, question):
        card = tk.Frame(
            parent,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        card.pack(fill="x", pady=6)

        tk.Label(
            card,
            text=f"{index}. {question['statement']}",
            font=FONT_BODY,
            fg=TEXT,
            bg=CARD_BG,
            wraplength=650,
            justify="left",
        ).pack(
            anchor="w",
            padx=18,
            pady=(15, 12),
        )

        var = tk.IntVar(value=self.app_state.get("behavioral", {}).get(question["id"], 0))
        self.answer_vars[question["id"]] = var

        scale = tk.Frame(card, bg=CARD_BG)
        scale.pack(
            fill="x",
            padx=18,
            pady=(0, 14),
        )

        tk.Label(
            scale,
            text="Least likely",
            font=FONT_SMALL,
            fg=MUTED,
            bg=CARD_BG,
        ).pack(
            side="left",
            padx=(0, 10),
        )

        number_container = tk.Frame(
            scale,
            bg=CARD_BG,
        )
        number_container.pack(side="left")

        for value in range(1, 6):
            radio = tk.Radiobutton(
                number_container,
                text=str(value),
                variable=var,
                value=value,
                font=("Helvetica", 10, "bold"),
                fg=TEXT,
                bg=CARD_BG,
                selectcolor="#DCE8FF",
                activebackground=CARD_BG,
                activeforeground=TEXT,
                indicatoron=True,
                padx=8,
                cursor="arrow",
            )
            radio.pack(side="left")

        tk.Label(
            scale,
            text="Most likely",
            font=FONT_SMALL,
            fg=MUTED,
            bg=CARD_BG,
        ).pack(
            side="left",
            padx=(10, 0),
        )

    # ========================================================
    # SAVE + HIDDEN SCORING
    # ========================================================
    def save_and_continue(self):
        raw_answers = {
            question_id: variable.get()
            for question_id, variable in self.answer_vars.items()
        }

        unanswered = [
            question_id
            for question_id, value in raw_answers.items()
            if value == 0
        ]

        if unanswered:
            self.error_label.config(
                text="Please answer every statement before continuing."
            )
            return

        # Raw answers remain available for future model updates.
        self.app_state["behavioral"] = raw_answers

        # Hidden interpretation.
        self.app_state["behavior_scores"] = calculate_behavior_scores(
            raw_answers
        )

        self.app_state["behavioral_complete"] = True
        save_state(self.app_state)

        if self.edit_only:
            self.destroy()
            if self.on_complete:
                self.on_complete()
            return

        self.destroy()

        from financial import FinancialFlow

        FinancialFlow(
            self.parent,
            self.app_state,
            on_complete=self.on_complete
        )

    # ========================================================
    # COMPLETION
    # ========================================================
    def show_complete_screen(self):
        for widget in self.winfo_children():
            widget.destroy()

        outer = tk.Frame(
            self,
            bg=MAIN_BG,
        )
        outer.pack(
            fill="both",
            expand=True,
            padx=36,
            pady=30,
        )

        tk.Label(
            outer,
            text="Step 2 complete",
            font=FONT_SMALL,
            fg=PRIMARY,
            bg=MAIN_BG,
        ).pack(anchor="w")

        tk.Label(
            outer,
            text="Behavioral Profile Saved",
            font=FONT_TITLE,
            fg=TEXT,
            bg=MAIN_BG,
        ).pack(
            anchor="w",
            pady=(4, 8),
        )

        tk.Label(
            outer,
            text=(
                "Your responses have been saved. The profile generated from "
                "these answers is used internally and is not displayed."
            ),
            font=FONT_BODY,
            fg=MUTED,
            bg=MAIN_BG,
            wraplength=640,
            justify="left",
        ).pack(
            anchor="w",
            pady=(0, 18),
        )

        notice = tk.Frame(
            outer,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
        )
        notice.pack(fill="x")

        tk.Label(
            notice,
            text="Next: Financial Facts",
            font=FONT_HEADER,
            fg=TEXT,
            bg=CARD_BG,
        ).pack(
            anchor="w",
            padx=18,
            pady=(16, 5),
        )

        tk.Label(
            notice,
            text=(
                "The next module will collect income, cash flow, savings, debt, "
                "accounts, benefits, and other financial information."
            ),
            font=FONT_BODY,
            fg=MUTED,
            bg=CARD_BG,
            wraplength=620,
            justify="left",
        ).pack(
            anchor="w",
            padx=18,
            pady=(0, 16),
        )

        AppButton(
            outer,
            text="Close",
            command=self.finish,
        ).pack(
            anchor="e",
            pady=(18, 0),
        )

    # ========================================================
    # NAVIGATION
    # ========================================================
    def go_back(self):
        """
        Return to Personal Facts.
        Local import avoids a circular import at startup.
        """
        self.destroy()

        from onboarding import OnboardingFlow

        OnboardingFlow(
            self.parent,
            self.app_state,
            on_complete=self.on_complete,
        )

    def finish(self):
        if self.on_complete:
            self.on_complete()

        self.destroy()
