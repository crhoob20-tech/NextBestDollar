import tkinter as tk
from tkinter import ttk
import threading
import webbrowser
import math
import yfinance as yf
from yfinance import EquityQuery


# ============================================================
# MARKET LEARN
# Baseline v2
#
# Features:
# - Dark custom onboarding cards
# - Onboarding -> Portfolio Lab flow
# - Linked allocation sliders
# - Top 10 portfolio examples
# - Broad Yahoo Finance equity screening
# - Dynamic Yahoo bond-fund screening
# - Treasury-focused fund examples
# - Research search + back button
# - Budget tab linked to portfolio allocation
# ============================================================


# ============================================================
# THEME
# ============================================================

BG = "#070B11"
PANEL = "#0E1520"
CARD_BG = "#131C29"
CARD_HOVER = "#1A2636"
CARD_SELECTED = "#203454"
BORDER = "#33445A"

ACCENT = "#4D8CFF"
ACCENT_LIGHT = "#9ABDFF"

GREEN = "#37D996"
GREEN_BG = "#12382A"
RED = "#FF6377"
RED_BG = "#3B1B24"
YELLOW = "#F6C453"
YELLOW_BG = "#3A3018"

TEXT = "#FFFFFF"
MUTED = "#B0BAC8"
MUTED_2 = "#7F8A99"

FONT_TITLE = ("Helvetica", 25, "bold")
FONT_HEADER = ("Helvetica", 16, "bold")
FONT_SUBHEADER = ("Helvetica", 12, "bold")
FONT_BODY = ("Helvetica", 11)
FONT_SMALL = ("Helvetica", 9)
FONT_NUMBER = ("Helvetica", 22, "bold")


# ============================================================
# APP SETTINGS
# ============================================================

TOP_SUGGESTIONS = 10
SCREENER_PAGE_SIZE = 250

# A profile-aware Yahoo screen is used first, then the app ranks
# those candidates. This keeps the UI responsive instead of
# downloading years of history for every listed security each time.
MAX_STOCK_CANDIDATES = 750

MAIN_US_EXCHANGES = [
    "NMS",  # Nasdaq Global Select
    "NYQ",  # NYSE
    "NGM",  # Nasdaq Global Market
    "NCM",  # Nasdaq Capital Market
    "ASE",  # NYSE American
]


# ============================================================
# SECTOR DATA FOR UNIVERSAL SEARCH
# ============================================================

SECTOR_MAP = {
    "energy": {"etf": "XLE", "stocks": ["XOM", "CVX", "COP", "SLB", "EOG"]},
    "technology": {"etf": "XLK", "stocks": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL"]},
    "tech": {"etf": "XLK", "stocks": ["AAPL", "MSFT", "NVDA", "AVGO", "ORCL"]},
    "healthcare": {"etf": "XLV", "stocks": ["UNH", "JNJ", "LLY", "ABBV", "MRK"]},
    "financial": {"etf": "XLF", "stocks": ["JPM", "BAC", "WFC", "GS", "MS"]},
    "finance": {"etf": "XLF", "stocks": ["JPM", "BAC", "WFC", "GS", "MS"]},
    "consumer": {"etf": "XLY", "stocks": ["AMZN", "TSLA", "HD", "MCD", "LOW"]},
    "industrial": {"etf": "XLI", "stocks": ["CAT", "GE", "HON", "UPS", "RTX"]},
    "utilities": {"etf": "XLU", "stocks": ["NEE", "DUK", "SO", "D", "AEP"]},
    "real estate": {"etf": "XLRE", "stocks": ["PLD", "AMT", "EQIX", "PSA", "O"]},
    "materials": {"etf": "XLB", "stocks": ["LIN", "SHW", "FCX", "APD", "NEM"]},
    "communication": {"etf": "XLC", "stocks": ["META", "GOOGL", "NFLX", "DIS", "TMUS"]},
}


# ============================================================
# CASH / HYSA EXAMPLES
#
# Rates are deliberately not hard-coded because they change.
# ============================================================

HYSA_OPTIONS = [
    {
        "name": "Marcus by Goldman Sachs",
        "description": "Online high-yield savings account",
        "url": "https://www.marcus.com",
    },
    {
        "name": "Ally Bank",
        "description": "Online savings and banking platform",
        "url": "https://www.ally.com",
    },
    {
        "name": "Capital One 360",
        "description": "Online savings account from Capital One",
        "url": "https://www.capitalone.com",
    },
    {
        "name": "Discover Bank",
        "description": "Online savings and banking products",
        "url": "https://www.discover.com/online-banking/",
    },
    {
        "name": "SoFi",
        "description": "Online banking and savings platform",
        "url": "https://www.sofi.com",
    },
    {
        "name": "American Express High Yield Savings",
        "description": "Online high-yield savings account",
        "url": "https://www.americanexpress.com/en-us/banking/online-savings/high-yield-savings/",
    },
    {
        "name": "Synchrony Bank",
        "description": "Online high-yield savings account",
        "url": "https://www.synchrony.com/banking",
    },
    {
        "name": "Barclays Online Savings",
        "description": "Online savings account",
        "url": "https://www.banking.barclaysus.com/",
    },
    {
        "name": "Citizens Access",
        "description": "Online savings from Citizens",
        "url": "https://www.citizensaccess.com/",
    },
    {
        "name": "Bread Savings",
        "description": "Online high-yield savings products",
        "url": "https://savings.breadfinancial.com/",
    },
]


# ============================================================
# METRIC HELP
# ============================================================

METRIC_HELP = {
    "P/E Ratio": (
        "P/E compares a company's stock price with its earnings.\n\n"
        "A P/E of 25 means investors are paying roughly $25 for every "
        "$1 of annual earnings. Higher is not automatically bad and "
        "lower is not automatically good."
    ),
    "Beta": (
        "Beta estimates how strongly an investment has historically "
        "moved relative to the broad stock market.\n\n"
        "Around 1.0 means market-like sensitivity. Above 1.0 generally "
        "means more sensitivity; below 1.0 generally means less."
    ),
    "Market Cap": (
        "Market capitalization is the estimated total market value of "
        "a company's outstanding shares."
    ),
    "Revenue Growth": (
        "Revenue growth measures how quickly a company's sales are "
        "increasing or decreasing."
    ),
    "Analyst Ratings": (
        "These values summarize published analyst opinions. They are "
        "not probabilities and do not guarantee future performance."
    ),
    "Price Targets": (
        "Analyst price targets estimate where analysts believe a stock "
        "may trade in the future. Targets change and analysts can be wrong."
    ),
}


# ============================================================
# GLOBAL STATE
# ============================================================

portfolio_weights = {
    "Stocks": 60.0,
    "Bonds": 25.0,
    "Treasuries": 10.0,
    "Cash": 5.0,
}

allocation_sliders = {}
portfolio_rebalancing = False

latest_stock_matches = []
latest_bond_matches = []
latest_treasury_matches = []

stock_scan_running = False
fund_scan_running = False
match_refresh_job = None

search_history = []
current_search_query = None
navigating_back = False


# ============================================================
# HELPERS
# ============================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def safe_number(value):
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def format_currency(value):
    if value is None:
        return "N/A"
    try:
        return f"${float(value):,.2f}"
    except Exception:
        return "N/A"


def format_large_number(value):
    if value is None:
        return "N/A"

    try:
        value = float(value)
        if value >= 1_000_000_000_000:
            return f"${value / 1_000_000_000_000:.2f}T"
        if value >= 1_000_000_000:
            return f"${value / 1_000_000_000:.2f}B"
        if value >= 1_000_000:
            return f"${value / 1_000_000:.2f}M"
        return f"${value:,.0f}"
    except Exception:
        return "N/A"


def clear_frame(frame):
    for widget in frame.winfo_children():
        widget.destroy()


def section_header(parent, text):
    tk.Label(
        parent,
        text=text,
        font=FONT_HEADER,
        fg=TEXT,
        bg=BG,
        anchor="w",
    ).pack(fill="x", padx=26, pady=(24, 9))


def make_card(parent, background=CARD_BG):
    frame = tk.Frame(
        parent,
        bg=background,
        highlightbackground=BORDER,
        highlightthickness=1,
    )
    frame.pack(fill="x", padx=26, pady=6)
    return frame


def show_message(parent, text):
    tk.Label(
        parent,
        text=text,
        font=FONT_BODY,
        fg=MUTED,
        bg=BG,
        wraplength=760,
        justify="left",
    ).pack(padx=26, pady=26, anchor="w")


# ============================================================
# SCROLLABLE FRAME
# ============================================================

class ScrollableFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=BG)

        self.canvas = tk.Canvas(
            self,
            bg=BG,
            highlightthickness=0,
        )
        self.scrollbar = tk.Scrollbar(
            self,
            orient="vertical",
            command=self.canvas.yview,
        )
        self.frame = tk.Frame(self.canvas, bg=BG)

        self.window_id = self.canvas.create_window(
            (0, 0),
            window=self.frame,
            anchor="nw",
        )

        self.frame.bind(
            "<Configure>",
            lambda event: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            ),
        )

        self.canvas.bind(
            "<Configure>",
            lambda event: self.canvas.itemconfig(
                self.window_id,
                width=event.width,
            ),
        )

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

    def scroll_to_top(self):
        self.canvas.yview_moveto(0)


# ============================================================
# CUSTOM DOT SLIDER
# ============================================================

class DotSlider(tk.Frame):
    def __init__(
        self,
        parent,
        title,
        value,
        on_change,
        min_value=0,
        max_value=100,
    ):
        super().__init__(parent, bg=CARD_BG)

        self.title = title
        self.value = float(value)
        self.on_change = on_change
        self.min_value = min_value
        self.max_value = max_value

        top = tk.Frame(self, bg=CARD_BG)
        top.pack(fill="x")

        tk.Label(
            top,
            text=title,
            font=FONT_SUBHEADER,
            fg=TEXT,
            bg=CARD_BG,
        ).pack(side="left")

        self.value_label = tk.Label(
            top,
            text=f"{self.value:.0f}%",
            font=("Helvetica", 12, "bold"),
            fg=ACCENT_LIGHT,
            bg=CARD_BG,
        )
        self.value_label.pack(side="right")

        self.canvas = tk.Canvas(
            self,
            height=42,
            bg=CARD_BG,
            highlightthickness=0,
            cursor="hand2",
        )
        self.canvas.pack(fill="x", pady=(4, 1))

        self.canvas.bind("<Configure>", lambda event: self.draw())
        self.canvas.bind("<Button-1>", self.handle_pointer)
        self.canvas.bind("<B1-Motion>", self.handle_pointer)

    def handle_pointer(self, event):
        width = self.canvas.winfo_width()
        left = 15
        right = max(left + 1, width - 15)

        x = clamp(event.x, left, right)
        fraction = (x - left) / (right - left)

        new_value = self.min_value + fraction * (
            self.max_value - self.min_value
        )
        new_value = round(new_value)

        if new_value != round(self.value):
            self.value = new_value
            self.value_label.config(text=f"{self.value:.0f}%")
            self.draw()
            self.on_change(self.title, self.value)

    def set_value(self, value):
        self.value = float(value)
        self.value_label.config(text=f"{self.value:.0f}%")
        self.draw()

    def draw(self):
        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        if width <= 30:
            return

        left = 15
        right = width - 15
        y = 21

        self.canvas.create_line(
            left,
            y,
            right,
            y,
            fill=BORDER,
            width=7,
            capstyle="round",
        )

        fraction = (
            (self.value - self.min_value)
            / (self.max_value - self.min_value)
        )

        dot_x = left + fraction * (right - left)

        self.canvas.create_line(
            left,
            y,
            dot_x,
            y,
            fill=ACCENT,
            width=7,
            capstyle="round",
        )

        radius = 10

        self.canvas.create_oval(
            dot_x - radius,
            y - radius,
            dot_x + radius,
            y + radius,
            fill=ACCENT_LIGHT,
            outline=TEXT,
            width=2,
        )


# ============================================================
# DARK CLICKABLE ROW
# ============================================================

def create_explore_row(
    parent,
    title,
    subtitle="",
    right_text="",
    right_color=MUTED,
    command=None,
):
    row = tk.Frame(
        parent,
        bg=CARD_HOVER,
        highlightbackground=BORDER,
        highlightthickness=1,
        cursor="hand2",
    )
    row.pack(fill="x", pady=5)

    left = tk.Frame(row, bg=CARD_HOVER, cursor="hand2")
    left.pack(side="left", fill="x", expand=True, padx=15, pady=12)

    title_label = tk.Label(
        left,
        text=title,
        font=FONT_SUBHEADER,
        fg=TEXT,
        bg=CARD_HOVER,
        anchor="w",
        cursor="hand2",
    )
    title_label.pack(fill="x")

    subtitle_label = None
    if subtitle:
        subtitle_label = tk.Label(
            left,
            text=subtitle,
            font=FONT_SMALL,
            fg=MUTED,
            bg=CARD_HOVER,
            anchor="w",
            cursor="hand2",
            wraplength=620,
            justify="left",
        )
        subtitle_label.pack(fill="x", pady=(3, 0))

    right_label = None
    if right_text:
        right_label = tk.Label(
            row,
            text=right_text,
            font=("Helvetica", 10, "bold"),
            fg=right_color,
            bg=CARD_HOVER,
            cursor="hand2",
        )
        right_label.pack(side="right", padx=15)

    if command:
        widgets = [row, left, title_label]
        if subtitle_label:
            widgets.append(subtitle_label)
        if right_label:
            widgets.append(right_label)

        for widget in widgets:
            widget.bind(
                "<Button-1>",
                lambda event, cmd=command: cmd(),
            )


# ============================================================
# PORTFOLIO ENGINE
# ============================================================

def calculate_portfolio_model(
    stock_weight,
    bond_weight,
    treasury_weight,
    cash_weight,
    growth_tilt,
    concentration,
    sector_concentration,
):
    total = (
        stock_weight
        + bond_weight
        + treasury_weight
        + cash_weight
    )

    if total <= 0:
        total = 100

    stocks = stock_weight / total
    bonds = bond_weight / total
    treasuries = treasury_weight / total
    cash = cash_weight / total

    estimated_beta = (
        stocks * (0.80 + growth_tilt / 250)
        + bonds * 0.15
        + treasuries * 0.05
    )

    volatility_score = (
        stocks * 82
        + bonds * 28
        + treasuries * 10
        + cash * 2
    )

    drawdown_score = (
        stocks * 78
        + bonds * 22
        + treasuries * 8
        + cash * 1
    )

    concentration_penalty = concentration * 0.18
    sector_penalty = sector_concentration * 0.12
    growth_penalty = growth_tilt * 0.12

    diversification_bonus = (
        min(bonds + treasuries + cash, 0.65) * 24
    )

    risk_score = (
        estimated_beta * 25
        + volatility_score * 0.32
        + drawdown_score * 0.25
        + concentration_penalty
        + sector_penalty
        + growth_penalty
        - diversification_bonus
    )

    risk_score = clamp(risk_score, 0, 100)

    if risk_score < 30:
        label = "Lower Risk"
        description = (
            "This model emphasizes stability and lower market sensitivity."
        )
    elif risk_score < 50:
        label = "Moderate-Low Risk"
        description = (
            "This model emphasizes stability while maintaining "
            "meaningful growth exposure."
        )
    elif risk_score < 68:
        label = "Moderate Risk"
        description = (
            "This model balances growth potential with defensive assets."
        )
    elif risk_score < 82:
        label = "Higher Risk"
        description = (
            "This model has substantial exposure to equities and "
            "market volatility."
        )
    else:
        label = "Very High Risk"
        description = (
            "This model has high sensitivity to market movements "
            "and concentration."
        )

    return {
        "stocks": stocks * 100,
        "bonds": bonds * 100,
        "treasuries": treasuries * 100,
        "cash": cash * 100,
        "beta": estimated_beta,
        "volatility": volatility_score,
        "drawdown": drawdown_score,
        "risk_score": risk_score,
        "label": label,
        "description": description,
    }


def rebalance_portfolio(changed_asset, new_value):
    global portfolio_rebalancing

    if portfolio_rebalancing:
        return

    portfolio_rebalancing = True

    new_value = clamp(float(new_value), 0, 100)

    other_assets = [
        asset
        for asset in portfolio_weights
        if asset != changed_asset
    ]

    remaining = 100 - new_value

    previous_other_total = sum(
        portfolio_weights[asset]
        for asset in other_assets
    )

    portfolio_weights[changed_asset] = new_value

    if previous_other_total <= 0:
        equal_share = remaining / len(other_assets)
        for asset in other_assets:
            portfolio_weights[asset] = equal_share
    else:
        for asset in other_assets:
            proportion = (
                portfolio_weights[asset]
                / previous_other_total
            )
            portfolio_weights[asset] = (
                remaining * proportion
            )

    difference = 100 - sum(portfolio_weights.values())
    if abs(difference) > 0.00001:
        portfolio_weights[other_assets[-1]] += difference

    for asset, slider in allocation_sliders.items():
        slider.set_value(portfolio_weights[asset])

    portfolio_rebalancing = False

    update_portfolio_lab()
    update_budget_summary()


def get_target_stock_risk():
    growth = growth_var.get()
    concentration = concentration_var.get()

    target = 30 + growth * 0.45 + concentration * 0.15
    return clamp(target, 20, 90)


def update_portfolio_lab():
    results = calculate_portfolio_model(
        portfolio_weights["Stocks"],
        portfolio_weights["Bonds"],
        portfolio_weights["Treasuries"],
        portfolio_weights["Cash"],
        growth_var.get(),
        concentration_var.get(),
        sector_var.get(),
    )

    risk_name_label.config(text=results["label"])
    risk_score_label.config(text=f'{results["risk_score"]:.0f} / 100')
    risk_description_label.config(text=results["description"])

    beta_value.config(text=f'{results["beta"]:.2f}')
    volatility_value.config(text=f'{results["volatility"]:.0f}/100')
    drawdown_value.config(text=f'{results["drawdown"]:.0f}/100')

    allocation_total_label.config(text="Total: 100%")

    if results["risk_score"] < 45:
        risk_color = GREEN
    elif results["risk_score"] < 68:
        risk_color = YELLOW
    else:
        risk_color = RED

    risk_name_label.config(fg=risk_color)

    risk_canvas.delete("all")
    width = max(risk_canvas.winfo_width(), 400)
    score_width = width * results["risk_score"] / 100

    risk_canvas.create_rectangle(
        0,
        0,
        width,
        14,
        fill=BORDER,
        outline="",
    )

    risk_canvas.create_rectangle(
        0,
        0,
        score_width,
        14,
        fill=risk_color,
        outline="",
    )

    schedule_stock_match_refresh()
    update_budget_summary()


# ============================================================
# YAHOO MARKET-WIDE STOCK SCREENING
# ============================================================

def get_beta_range(target_risk):
    if target_risk < 35:
        return 0.0, 0.85

    if target_risk < 55:
        return 0.35, 1.15

    if target_risk < 75:
        return 0.70, 1.60

    return 1.0, 4.0


def get_market_stock_candidates(
    target_risk,
    max_candidates=MAX_STOCK_CANDIDATES,
):
    """
    Pulls a broad, profile-aware set of U.S. equities from Yahoo's
    screener. It pages across results rather than using a hard-coded
    ticker list.

    This does NOT mean yfinance downloads every exchange security's
    full history every time. Yahoo is first used to narrow the market
    to relevant, liquid equities, then this app ranks the results.
    """

    beta_low, beta_high = get_beta_range(target_risk)

    query = EquityQuery(
        "and",
        [
            EquityQuery("eq", ["region", "us"]),
            EquityQuery("is-in", ["exchange", *MAIN_US_EXCHANGES]),
            EquityQuery("gte", ["intradaymarketcap", 300_000_000]),
            EquityQuery("gte", ["avgdailyvol3m", 100_000]),
            EquityQuery("gte", ["intradayprice", 2]),
            EquityQuery("gte", ["beta", beta_low]),
            EquityQuery("lte", ["beta", beta_high]),
        ],
    )

    candidates = []
    seen = set()

    offset = 0

    while len(candidates) < max_candidates:
        page_size = min(
            SCREENER_PAGE_SIZE,
            max_candidates - len(candidates),
        )

        try:
            response = yf.screen(
                query,
                offset=offset,
                size=page_size,
                sortField="intradaymarketcap",
                sortAsc=False,
            )
        except Exception as exc:
            print("Yahoo stock screener error:", exc)
            break

        quotes = response.get("quotes", [])

        if not quotes:
            break

        added = 0

        for quote in quotes:
            symbol = quote.get("symbol")

            if not symbol or symbol in seen:
                continue

            # Keep ordinary equities and skip obvious fund-like results.
            quote_type = (
                quote.get("quoteType")
                or quote.get("typeDisp")
                or ""
            ).upper()

            if quote_type and "ETF" in quote_type:
                continue

            seen.add(symbol)
            added += 1

            candidates.append(
                {
                    "symbol": symbol,
                    "name": (
                        quote.get("longName")
                        or quote.get("shortName")
                        or symbol
                    ),
                    "beta": safe_number(quote.get("beta")) or 1.0,
                    "market_cap": safe_number(
                        quote.get("intradaymarketcap")
                        or quote.get("marketCap")
                    ),
                    "sector": (
                        quote.get("sector")
                        or quote.get("sectorDisp")
                        or "Unknown"
                    ),
                }
            )

            if len(candidates) >= max_candidates:
                break

        if len(quotes) < page_size or added == 0:
            break

        offset += page_size

    return candidates


def calculate_history_metrics_from_download(
    history,
    symbol,
    beta,
    sector,
    market_cap,
):
    """
    Reads one symbol from a batched yfinance download and calculates
    volatility + drawdown without making a separate .info call.
    """

    try:
        if history is None or history.empty:
            return None

        if hasattr(history.columns, "levels"):
            if "Close" not in history.columns.get_level_values(0):
                return None

            close_block = history["Close"]

            if symbol not in close_block.columns:
                return None

            close = close_block[symbol].dropna()

        else:
            close = history["Close"].dropna()

        if len(close) < 30:
            return None

        returns = close.pct_change().dropna()

        if returns.empty:
            return None

        annual_volatility = (
            returns.std()
            * math.sqrt(252)
            * 100
        )

        rolling_high = close.cummax()

        drawdowns = close / rolling_high - 1

        max_drawdown = (
            abs(drawdowns.min())
            * 100
        )

        beta_component = clamp(
            beta / 2.0 * 100,
            0,
            100,
        )

        volatility_component = clamp(
            annual_volatility / 60 * 100,
            0,
            100,
        )

        drawdown_component = clamp(
            max_drawdown / 60 * 100,
            0,
            100,
        )

        risk_score = (
            beta_component * 0.35
            + volatility_component * 0.35
            + drawdown_component * 0.30
        )

        return {
            "beta": beta,
            "volatility": annual_volatility,
            "drawdown": max_drawdown,
            "risk_score": clamp(risk_score, 0, 100),
            "sector": sector,
            "market_cap": market_cap,
        }

    except Exception as exc:
        print(f"History metric error for {symbol}:", exc)
        return None


def schedule_stock_match_refresh():
    global match_refresh_job

    if "root" not in globals():
        return

    if match_refresh_job:
        try:
            root.after_cancel(match_refresh_job)
        except Exception:
            pass

    match_refresh_job = root.after(
        1000,
        refresh_matching_stocks,
    )


def refresh_matching_stocks():
    global stock_scan_running

    if stock_scan_running:
        return

    stock_scan_running = True

    if (
        "explore_category" in globals()
        and explore_category.get() == "Stocks"
    ):
        show_explore_loading(
            "Scanning a broad U.S. stock universe..."
        )

    target_risk = get_target_stock_risk()

    def worker():
        global stock_scan_running

        try:
            candidates = get_market_stock_candidates(
                target_risk,
                max_candidates=MAX_STOCK_CANDIDATES,
            )

            if not candidates:
                root.after(
                    0,
                    display_stock_scan_error,
                    "Yahoo returned no stock candidates. "
                    "Try upgrading yfinance: pip install --upgrade yfinance",
                )
                return

            symbols = [
                item["symbol"]
                for item in candidates
            ]

            try:
                history = yf.download(
                    tickers=" ".join(symbols),
                    period="1y",
                    interval="1d",
                    auto_adjust=True,
                    progress=False,
                    group_by="column",
                    threads=True,
                )
            except Exception as exc:
                print("Batch stock history error:", exc)
                history = None

            matches = []

            for candidate in candidates:
                metrics = calculate_history_metrics_from_download(
                    history,
                    candidate["symbol"],
                    candidate["beta"],
                    candidate["sector"],
                    candidate["market_cap"],
                )

                if not metrics:
                    continue

                risk_distance = abs(
                    metrics["risk_score"]
                    - target_risk
                )

                # Small sector diversification preference.
                matches.append(
                    (
                        risk_distance,
                        candidate["symbol"],
                        candidate["name"],
                        metrics,
                    )
                )

            matches.sort(key=lambda item: item[0])

            # Keep top results diversified by sector where possible.
            best = []
            sector_counts = {}

            for item in matches:
                sector = item[3]["sector"]
                count = sector_counts.get(sector, 0)

                if count >= 3:
                    continue

                best.append(item)
                sector_counts[sector] = count + 1

                if len(best) >= TOP_SUGGESTIONS:
                    break

            # Fill if sector rule left us short.
            if len(best) < TOP_SUGGESTIONS:
                chosen = {item[1] for item in best}

                for item in matches:
                    if item[1] in chosen:
                        continue

                    best.append(item)

                    if len(best) >= TOP_SUGGESTIONS:
                        break

            root.after(
                0,
                display_matching_stocks,
                best,
            )

        except Exception as exc:
            print("Stock matching error:", exc)

            root.after(
                0,
                display_stock_scan_error,
                f"Stock scan failed: {exc}",
            )

        finally:
            stock_scan_running = False

    threading.Thread(
        target=worker,
        daemon=True,
    ).start()


def display_stock_scan_error(message):
    global stock_scan_running
    stock_scan_running = False

    if explore_category.get() != "Stocks":
        return

    clear_frame(explore_results_frame)

    tk.Label(
        explore_results_frame,
        text=message,
        font=FONT_BODY,
        fg=RED,
        bg=CARD_BG,
        wraplength=700,
        justify="left",
    ).pack(
        fill="x",
        padx=5,
        pady=15,
        anchor="w",
    )


def display_matching_stocks(matches):
    global latest_stock_matches

    latest_stock_matches = matches

    if explore_category.get() == "Stocks":
        display_stock_explore_results()


# ============================================================
# BOND / TREASURY FUND SCREENING
# ============================================================

def get_bond_fund_candidates():
    """
    Uses Yahoo's built-in bond-fund screener.

    Yahoo Finance/yfinance does not expose the complete U.S. individual
    corporate/municipal bond market. This function therefore discovers
    bond funds/ETFs from Yahoo. The app is structured so an individual
    bond provider can replace this function later.
    """

    try:
        response = yf.screen(
            "bond_etfs",
            count=250,
        )
    except TypeError:
        # Some yfinance versions use size instead of count for this path.
        response = yf.screen(
            "bond_etfs",
            size=250,
        )
    except Exception as exc:
        print("Bond screener error:", exc)
        return []

    quotes = response.get("quotes", [])

    candidates = []

    for quote in quotes:
        symbol = quote.get("symbol")

        if not symbol:
            continue

        name = (
            quote.get("longName")
            or quote.get("shortName")
            or symbol
        )

        category = (
            quote.get("categoryName")
            or quote.get("categoryname")
            or quote.get("category")
            or "Bond Fund"
        )

        candidates.append(
            {
                "symbol": symbol,
                "name": name,
                "category": category,
                "expense_ratio": safe_number(
                    quote.get("annualReportNetExpenseRatio")
                    or quote.get("annualreportnetexpenseratio")
                ),
            }
        )

    return candidates


def bond_fit_score(candidate):
    """
    Educational ranking heuristic based on the user's model.
    Lower is a closer fit.
    """

    category = candidate["category"].lower()

    stock_weight = portfolio_weights["Stocks"]
    bond_weight = portfolio_weights["Bonds"]
    treasury_weight = portfolio_weights["Treasuries"]

    score = 50.0

    # More defensive portfolios prefer high-quality / short duration.
    defensive = 100 - stock_weight

    if "short" in category or "ultrashort" in category:
        score -= defensive * 0.22

    if "intermediate" in category:
        score -= 10

    if "corporate" in category:
        score -= bond_weight * 0.10

    if "high yield" in category:
        score += defensive * 0.20
        score -= stock_weight * 0.08

    if "inflation" in category:
        score -= treasury_weight * 0.08

    expense = candidate.get("expense_ratio")

    if expense is not None:
        score += expense * 10

    return score


def is_treasury_like(candidate):
    combined = (
        candidate["name"]
        + " "
        + candidate["category"]
    ).lower()

    treasury_terms = [
        "treasury",
        "government",
        "t-bill",
        "t bill",
        "tips",
        "inflation-protected",
    ]

    return any(
        term in combined
        for term in treasury_terms
    )


def refresh_bond_and_treasury_candidates():
    global fund_scan_running

    if fund_scan_running:
        return

    fund_scan_running = True

    if explore_category.get() in ("Bonds", "Treasuries"):
        show_explore_loading(
            "Loading broad bond and Treasury fund examples..."
        )

    def worker():
        global fund_scan_running
        global latest_bond_matches
        global latest_treasury_matches

        try:
            candidates = get_bond_fund_candidates()

            ranked = sorted(
                candidates,
                key=bond_fit_score,
            )

            treasury_ranked = [
                item
                for item in ranked
                if is_treasury_like(item)
            ]

            non_treasury_ranked = [
                item
                for item in ranked
                if not is_treasury_like(item)
            ]

            latest_bond_matches = (
                non_treasury_ranked[:TOP_SUGGESTIONS]
            )

            latest_treasury_matches = (
                treasury_ranked[:TOP_SUGGESTIONS]
            )

            root.after(
                0,
                refresh_explore_category,
            )

        except Exception as exc:
            print("Bond/Treasury refresh error:", exc)

        finally:
            fund_scan_running = False

    threading.Thread(
        target=worker,
        daemon=True,
    ).start()


# ============================================================
# EXPLORE MODEL
# ============================================================

def show_explore_loading(message):
    if "explore_results_frame" not in globals():
        return

    clear_frame(explore_results_frame)

    tk.Label(
        explore_results_frame,
        text=message,
        font=FONT_BODY,
        fg=MUTED,
        bg=CARD_BG,
    ).pack(
        padx=5,
        pady=15,
        anchor="w",
    )


def refresh_explore_category():
    if "explore_results_frame" not in globals():
        return

    category = explore_category.get()

    clear_frame(explore_results_frame)

    if category == "Stocks":
        display_stock_explore_results()

    elif category == "Bonds":
        display_bond_explore_results()

    elif category == "Treasuries":
        display_treasury_explore_results()

    elif category == "Cash / HYSA":
        display_hysa_examples()


def display_stock_explore_results():
    clear_frame(explore_results_frame)

    tk.Label(
        explore_results_frame,
        text=(
            "Top 10 research examples from a broad Yahoo Finance "
            "U.S. stock screen, ranked by historical risk fit. "
            "These are educational examples, not recommendations."
        ),
        font=FONT_SMALL,
        fg=MUTED,
        bg=CARD_BG,
        wraplength=700,
        justify="left",
    ).pack(
        fill="x",
        padx=5,
        pady=(3, 9),
    )

    if not latest_stock_matches:
        tk.Label(
            explore_results_frame,
            text="Finding stock examples...",
            font=FONT_BODY,
            fg=MUTED,
            bg=CARD_BG,
        ).pack(
            padx=5,
            pady=15,
            anchor="w",
        )

        if not stock_scan_running:
            refresh_matching_stocks()

        return

    for (
        distance,
        symbol,
        name,
        metrics,
    ) in latest_stock_matches[:TOP_SUGGESTIONS]:

        risk = metrics["risk_score"]

        if risk < 45:
            risk_color = GREEN
        elif risk < 68:
            risk_color = YELLOW
        else:
            risk_color = RED

        sector = metrics.get("sector") or "Unknown"

        create_explore_row(
            explore_results_frame,
            f"{symbol}   {name}",
            (
                f'{sector}  •  Beta {metrics["beta"]:.2f}'
                f'  •  Volatility {metrics["volatility"]:.0f}%'
                f'  •  Drawdown {metrics["drawdown"]:.0f}%'
            ),
            f"Risk {risk:.0f}",
            risk_color,
            command=lambda s=symbol: open_research_item(s),
        )


def display_bond_explore_results():
    clear_frame(explore_results_frame)

    tk.Label(
        explore_results_frame,
        text=(
            "Top 10 Yahoo-discovered bond fund examples. Yahoo/yfinance "
            "does not provide the complete market of individual corporate "
            "and municipal bonds, so these are bond funds for the current "
            "prototype."
        ),
        font=FONT_SMALL,
        fg=MUTED,
        bg=CARD_BG,
        wraplength=700,
        justify="left",
    ).pack(
        fill="x",
        padx=5,
        pady=(3, 9),
    )

    if not latest_bond_matches:
        tk.Label(
            explore_results_frame,
            text="Loading bond fund examples...",
            font=FONT_BODY,
            fg=MUTED,
            bg=CARD_BG,
        ).pack(
            padx=5,
            pady=15,
            anchor="w",
        )

        if not fund_scan_running:
            refresh_bond_and_treasury_candidates()

        return

    for item in latest_bond_matches[:TOP_SUGGESTIONS]:
        create_explore_row(
            explore_results_frame,
            f'{item["symbol"]}   {item["name"]}',
            item["category"],
            "Research",
            ACCENT_LIGHT,
            command=lambda s=item["symbol"]: open_research_item(s),
        )


def display_treasury_explore_results():
    clear_frame(explore_results_frame)

    tk.Label(
        explore_results_frame,
        text=(
            "Top 10 Treasury/government bond fund examples found through "
            "Yahoo. A later data adapter can replace these with individual "
            "Treasury CUSIPs and current auction offerings."
        ),
        font=FONT_SMALL,
        fg=MUTED,
        bg=CARD_BG,
        wraplength=700,
        justify="left",
    ).pack(
        fill="x",
        padx=5,
        pady=(3, 9),
    )

    if not latest_treasury_matches:
        tk.Label(
            explore_results_frame,
            text="Loading Treasury examples...",
            font=FONT_BODY,
            fg=MUTED,
            bg=CARD_BG,
        ).pack(
            padx=5,
            pady=15,
            anchor="w",
        )

        if not fund_scan_running:
            refresh_bond_and_treasury_candidates()

        return

    for item in latest_treasury_matches[:TOP_SUGGESTIONS]:
        create_explore_row(
            explore_results_frame,
            f'{item["symbol"]}   {item["name"]}',
            item["category"],
            "Research",
            ACCENT_LIGHT,
            command=lambda s=item["symbol"]: open_research_item(s),
        )


def display_hysa_examples():
    clear_frame(explore_results_frame)

    tk.Label(
        explore_results_frame,
        text=(
            "10 established savings providers to research. APYs change "
            "frequently, so the app does not hard-code a rate."
        ),
        font=FONT_SMALL,
        fg=MUTED,
        bg=CARD_BG,
        wraplength=700,
        justify="left",
    ).pack(
        fill="x",
        padx=5,
        pady=(3, 9),
    )

    for account in HYSA_OPTIONS[:TOP_SUGGESTIONS]:
        create_explore_row(
            explore_results_frame,
            account["name"],
            account["description"],
            "Visit",
            GREEN,
            command=lambda url=account["url"]: webbrowser.open(url),
        )


# ============================================================
# RESEARCH
# ============================================================

def detect_sector(query):
    query_lower = query.lower().strip()

    for keyword, data in SECTOR_MAP.items():
        if (
            query_lower == keyword
            or f"{keyword} sector" in query_lower
            or f"{keyword} stocks" in query_lower
        ):
            return keyword, data

    return None, None


def resolve_ticker(query):
    query = query.strip()

    if not query:
        return None

    if " " not in query and len(query) <= 8:
        symbol = query.upper()

        try:
            stock = yf.Ticker(symbol)
            history = stock.history(period="5d")

            if not history.empty:
                return symbol
        except Exception:
            pass

    try:
        search = yf.Search(
            query,
            max_results=10,
            news_count=0,
        )

        for quote in search.quotes:
            symbol = quote.get("symbol")
            quote_type = quote.get("quoteType", "")

            if symbol and quote_type in (
                "EQUITY",
                "ETF",
                "MUTUALFUND",
            ):
                return symbol

    except Exception as exc:
        print("Ticker search error:", exc)

    return None


def get_price_data(stock):
    try:
        history = stock.history(period="5d")

        if history.empty:
            return None, None, None

        price = float(history["Close"].iloc[-1])

        if len(history) >= 2:
            previous = float(history["Close"].iloc[-2])
        else:
            previous = price

        change = price - previous
        pct = change / previous * 100 if previous else 0

        return price, change, pct

    except Exception:
        return None, None, None


def get_analyst_sentiment(stock):
    try:
        recommendations = stock.get_recommendations()

        if recommendations is None or recommendations.empty:
            return None

        # yfinance generally provides recent periods in this table.
        latest = recommendations.iloc[0]

        strong_buy = int(latest.get("strongBuy", 0) or 0)
        buy = int(latest.get("buy", 0) or 0)
        hold = int(latest.get("hold", 0) or 0)
        sell = int(latest.get("sell", 0) or 0)
        strong_sell = int(latest.get("strongSell", 0) or 0)

        total = (
            strong_buy
            + buy
            + hold
            + sell
            + strong_sell
        )

        if total == 0:
            return None

        bullish = strong_buy + buy
        bearish = sell + strong_sell

        return {
            "total": total,
            "buy_pct": bullish / total * 100,
            "hold_pct": hold / total * 100,
            "sell_pct": bearish / total * 100,
        }

    except Exception:
        return None


def get_price_targets(stock):
    try:
        targets = stock.get_analyst_price_targets()

        if not targets:
            return None

        return {
            "current": safe_number(targets.get("current")),
            "low": safe_number(targets.get("low")),
            "high": safe_number(targets.get("high")),
            "mean": safe_number(targets.get("mean")),
            "median": safe_number(targets.get("median")),
        }

    except Exception:
        return None


def get_news(stock, limit=6):
    items = []

    try:
        news = stock.news

        for item in news[:limit]:
            content = item.get("content", {})

            if content:
                title = content.get("title", "No title")
                publisher = (
                    content.get("provider", {})
                    .get("displayName", "Unknown source")
                )
                link = (
                    content.get("canonicalUrl", {})
                    .get("url", "")
                )
            else:
                title = item.get("title", "No title")
                publisher = item.get(
                    "publisher",
                    "Unknown source",
                )
                link = item.get("link", "")

            items.append(
                (title, publisher, link)
            )

    except Exception:
        pass

    return items


def get_stock_research(symbol):
    stock = yf.Ticker(symbol)

    price, change, pct_change = get_price_data(stock)

    try:
        info = stock.info
    except Exception:
        info = {}

    return {
        "symbol": symbol,
        "name": (
            info.get("longName")
            or info.get("shortName")
            or symbol
        ),
        "price": price,
        "change": change,
        "pct_change": pct_change,
        "description": info.get(
            "longBusinessSummary",
            "Description unavailable.",
        ),
        "sector": info.get("sector", "N/A"),
        "industry": info.get("industry", "N/A"),
        "market_cap": info.get("marketCap"),
        "pe_ratio": (
            info.get("trailingPE")
            or info.get("forwardPE")
        ),
        "beta": safe_number(info.get("beta")),
        "revenue_growth": safe_number(
            info.get("revenueGrowth")
        ),
        "sentiment": get_analyst_sentiment(stock),
        "targets": get_price_targets(stock),
        "news": get_news(stock),
    }


def update_back_button():
    if search_history:
        back_button.config(state="normal")
    else:
        back_button.config(state="disabled")


def go_back():
    global current_search_query
    global navigating_back

    if not search_history:
        return

    previous_query = search_history.pop()

    navigating_back = True
    current_search_query = None

    universal_entry.delete(0, tk.END)
    universal_entry.insert(0, previous_query)

    universal_search(previous_query)

    update_back_button()


def universal_search(query_override=None):
    global current_search_query
    global navigating_back

    if query_override is not None:
        query = query_override.strip()
    else:
        query = universal_entry.get().strip()

    if not query or query == PLACEHOLDER:
        return

    if (
        current_search_query
        and current_search_query != query
        and not navigating_back
    ):
        search_history.append(current_search_query)

    current_search_query = query
    navigating_back = False

    update_back_button()

    universal_entry.delete(0, tk.END)
    universal_entry.insert(0, query)

    notebook.select(research_tab)

    clear_frame(research_results.frame)

    show_message(
        research_results.frame,
        "Searching market data...",
    )

    search_button.config(
        state="disabled",
        text="Searching...",
    )

    def worker():
        sector_name, sector_data = detect_sector(query)

        if sector_data:
            rows = []

            symbols = [
                sector_data["etf"]
            ] + sector_data["stocks"]

            for symbol in symbols:
                stock = yf.Ticker(symbol)
                price, change, pct = get_price_data(stock)

                rows.append(
                    (
                        symbol,
                        price,
                        change,
                        pct,
                    )
                )

            root.after(
                0,
                display_sector,
                sector_name,
                rows,
            )
            return

        symbol = resolve_ticker(query)

        if not symbol:
            root.after(
                0,
                search_failed,
                query,
            )
            return

        data = get_stock_research(symbol)

        root.after(
            0,
            display_research,
            data,
        )

    threading.Thread(
        target=worker,
        daemon=True,
    ).start()


def search_failed(query):
    search_button.config(
        state="normal",
        text="Search",
    )

    clear_frame(research_results.frame)

    show_message(
        research_results.frame,
        f'Could not find a security matching "{query}".',
    )


def open_research_item(symbol):
    universal_entry.delete(0, tk.END)
    universal_entry.insert(0, symbol)

    universal_search(symbol)


def display_sector(sector_name, rows):
    search_button.config(
        state="normal",
        text="Search",
    )

    clear_frame(research_results.frame)

    section_header(
        research_results.frame,
        f"{sector_name.title()} Sector",
    )

    for index, (
        symbol,
        price,
        change,
        pct,
    ) in enumerate(rows):

        card = make_card(
            research_results.frame
        )

        label_text = (
            f"Sector ETF • {symbol}"
            if index == 0
            else symbol
        )

        left = tk.Label(
            card,
            text=label_text,
            font=FONT_SUBHEADER,
            fg=ACCENT_LIGHT,
            bg=CARD_BG,
            cursor="hand2",
        )

        left.pack(
            side="left",
            padx=16,
            pady=14,
        )

        left.bind(
            "<Button-1>",
            lambda event, s=symbol: open_research_item(s),
        )

        tk.Label(
            card,
            text=format_currency(price),
            font=FONT_BODY,
            fg=MUTED,
            bg=CARD_BG,
        ).pack(
            side="left",
            padx=6,
        )

        if change is not None:
            positive = change >= 0
            color = GREEN if positive else RED
            sign = "+" if positive else ""

            tk.Label(
                card,
                text=(
                    f"{sign}{change:.2f} "
                    f"({sign}{pct:.2f}%)"
                ),
                font=FONT_BODY,
                fg=color,
                bg=CARD_BG,
            ).pack(
                side="right",
                padx=16,
            )


def add_metric_row(parent, label, value, help_key=None):
    row = tk.Frame(parent, bg=CARD_BG)
    row.pack(fill="x", padx=17, pady=7)

    label_widget = tk.Label(
        row,
        text=(
            f"{label}  ?"
            if help_key
            else label
        ),
        font=(
            ("Helvetica", 11, "underline")
            if help_key
            else FONT_BODY
        ),
        fg=(
            ACCENT_LIGHT
            if help_key
            else MUTED
        ),
        bg=CARD_BG,
        width=18,
        anchor="w",
        cursor=(
            "hand2"
            if help_key
            else ""
        ),
    )

    label_widget.pack(side="left")

    if help_key:
        label_widget.bind(
            "<Button-1>",
            lambda event, key=help_key: show_definition(
                key,
                METRIC_HELP[key],
            ),
        )

    tk.Label(
        row,
        text=value,
        font=FONT_BODY,
        fg=TEXT,
        bg=CARD_BG,
        anchor="w",
    ).pack(side="left")


def show_definition(title, explanation):
    window = tk.Toplevel(root)
    window.title(title)
    window.geometry("520x330")
    window.configure(bg=BG)

    tk.Label(
        window,
        text=title,
        font=FONT_HEADER,
        fg=TEXT,
        bg=BG,
    ).pack(
        padx=25,
        pady=(25, 10),
        anchor="w",
    )

    tk.Label(
        window,
        text=explanation,
        font=FONT_BODY,
        fg=MUTED,
        bg=BG,
        wraplength=465,
        justify="left",
    ).pack(
        padx=25,
        pady=5,
        anchor="w",
    )


def display_research(data):
    search_button.config(
        state="normal",
        text="Search",
    )

    clear_frame(research_results.frame)
    research_results.scroll_to_top()

    header_card = make_card(
        research_results.frame
    )

    tk.Label(
        header_card,
        text=data["name"],
        font=FONT_TITLE,
        fg=TEXT,
        bg=CARD_BG,
        anchor="w",
    ).pack(
        fill="x",
        padx=18,
        pady=(17, 1),
    )

    tk.Label(
        header_card,
        text=data["symbol"],
        font=FONT_SUBHEADER,
        fg=MUTED,
        bg=CARD_BG,
        anchor="w",
    ).pack(
        fill="x",
        padx=18,
    )

    change = data["change"]
    pct = data["pct_change"]

    if change is not None:
        positive = change >= 0
        price_color = (
            GREEN
            if positive
            else RED
        )
        sign = "+" if positive else ""

        price_text = (
            f'{format_currency(data["price"])}   '
            f'{sign}{change:.2f} '
            f'({sign}{pct:.2f}%)'
        )
    else:
        price_color = TEXT
        price_text = format_currency(data["price"])

    tk.Label(
        header_card,
        text=price_text,
        font=FONT_NUMBER,
        fg=price_color,
        bg=CARD_BG,
        anchor="w",
    ).pack(
        fill="x",
        padx=18,
        pady=(8, 15),
    )

    section_header(
        research_results.frame,
        "Overview",
    )

    overview_card = make_card(
        research_results.frame
    )

    tk.Label(
        overview_card,
        text=data["description"],
        font=FONT_BODY,
        fg=TEXT,
        bg=CARD_BG,
        wraplength=740,
        justify="left",
    ).pack(
        fill="x",
        padx=17,
        pady=17,
    )

    section_header(
        research_results.frame,
        "Quick Snapshot",
    )

    snapshot_card = make_card(
        research_results.frame
    )

    add_metric_row(
        snapshot_card,
        "Sector",
        data["sector"],
    )

    add_metric_row(
        snapshot_card,
        "Industry",
        data["industry"],
    )

    add_metric_row(
        snapshot_card,
        "Market Cap",
        format_large_number(data["market_cap"]),
        "Market Cap",
    )

    add_metric_row(
        snapshot_card,
        "P/E Ratio",
        (
            f'{data["pe_ratio"]:.2f}x'
            if data["pe_ratio"]
            else "N/A"
        ),
        "P/E Ratio",
    )

    add_metric_row(
        snapshot_card,
        "Beta",
        (
            f'{data["beta"]:.2f}'
            if data["beta"] is not None
            else "N/A"
        ),
        "Beta",
    )

    if data["revenue_growth"] is not None:
        add_metric_row(
            snapshot_card,
            "Revenue Growth",
            f'{data["revenue_growth"] * 100:.1f}%',
            "Revenue Growth",
        )

    section_header(
        research_results.frame,
        "Wall Street Sentiment",
    )

    sentiment_card = make_card(
        research_results.frame
    )

    sentiment = data["sentiment"]

    if sentiment:
        grid = tk.Frame(
            sentiment_card,
            bg=CARD_BG,
        )

        grid.pack(
            fill="x",
            padx=12,
            pady=15,
        )

        blocks = [
            (
                "BUY",
                sentiment["buy_pct"],
                GREEN,
                GREEN_BG,
            ),
            (
                "HOLD",
                sentiment["hold_pct"],
                YELLOW,
                YELLOW_BG,
            ),
            (
                "SELL",
                sentiment["sell_pct"],
                RED,
                RED_BG,
            ),
        ]

        for name, percentage, color, background in blocks:
            block = tk.Frame(
                grid,
                bg=background,
            )

            block.pack(
                side="left",
                expand=True,
                fill="x",
                padx=4,
            )

            tk.Label(
                block,
                text=f"{percentage:.0f}%",
                font=FONT_NUMBER,
                fg=color,
                bg=background,
            ).pack(
                pady=(12, 1),
            )

            tk.Label(
                block,
                text=name,
                font=FONT_SMALL,
                fg=MUTED,
                bg=background,
            ).pack(
                pady=(0, 12),
            )

        tk.Label(
            sentiment_card,
            text=(
                f'Based on {sentiment["total"]} analyst ratings. '
                "This summarizes analyst opinions and is not a recommendation."
            ),
            font=FONT_SMALL,
            fg=MUTED,
            bg=CARD_BG,
            wraplength=700,
            justify="left",
        ).pack(
            padx=16,
            pady=(0, 15),
            anchor="w",
        )

    else:
        tk.Label(
            sentiment_card,
            text="Analyst sentiment is currently unavailable.",
            font=FONT_BODY,
            fg=MUTED,
            bg=CARD_BG,
        ).pack(
            padx=16,
            pady=16,
            anchor="w",
        )

    section_header(
        research_results.frame,
        "Analyst Price Targets",
    )

    target_card = make_card(
        research_results.frame
    )

    targets = data["targets"]

    if targets:
        for label, key in [
            ("Current", "current"),
            ("Average", "mean"),
            ("Median", "median"),
            ("Low", "low"),
            ("High", "high"),
        ]:
            add_metric_row(
                target_card,
                label,
                format_currency(targets[key]),
            )
    else:
        tk.Label(
            target_card,
            text="Price-target data is currently unavailable.",
            font=FONT_BODY,
            fg=MUTED,
            bg=CARD_BG,
        ).pack(
            padx=16,
            pady=16,
            anchor="w",
        )

    section_header(
        research_results.frame,
        "Recent News",
    )

    if data["news"]:
        for title, publisher, link in data["news"]:
            card = make_card(
                research_results.frame
            )

            headline = tk.Label(
                card,
                text=title,
                font=FONT_SUBHEADER,
                fg=ACCENT_LIGHT,
                bg=CARD_BG,
                cursor="hand2",
                wraplength=720,
                justify="left",
                anchor="w",
            )

            headline.pack(
                fill="x",
                padx=16,
                pady=(13, 4),
            )

            tk.Label(
                card,
                text=publisher,
                font=FONT_SMALL,
                fg=MUTED,
                bg=CARD_BG,
                anchor="w",
            ).pack(
                fill="x",
                padx=16,
                pady=(0, 13),
            )

            if link:
                headline.bind(
                    "<Button-1>",
                    lambda event, url=link: webbrowser.open(url),
                )
    else:
        show_message(
            research_results.frame,
            "No recent news found.",
        )


# ============================================================
# BUDGET ENGINE
# ============================================================

def parse_money(entry):
    value = entry.get().strip()

    if not value:
        return 0.0

    value = value.replace("$", "").replace(",", "")

    try:
        return max(float(value), 0.0)
    except Exception:
        return 0.0


def update_budget_summary(*args):
    if "budget_entries" not in globals():
        return

    income = parse_money(
        budget_entries["Monthly Income"]
    )

    expense_names = [
        name
        for name in budget_entries
        if name != "Monthly Income"
    ]

    expenses = sum(
        parse_money(budget_entries[name])
        for name in expense_names
    )

    remaining = income - expenses

    savings_rate = (
        remaining / income * 100
        if income > 0
        else 0
    )

    budget_income_value.config(
        text=format_currency(income),
    )

    budget_spending_value.config(
        text=format_currency(expenses),
    )

    remaining_color = (
        GREEN
        if remaining >= 0
        else RED
    )

    budget_remaining_value.config(
        text=format_currency(remaining),
        fg=remaining_color,
    )

    budget_savings_rate_value.config(
        text=f"{savings_rate:.1f}%",
        fg=remaining_color,
    )

    investable = max(remaining, 0)

    for asset in [
        "Stocks",
        "Bonds",
        "Treasuries",
        "Cash",
    ]:
        amount = (
            investable
            * portfolio_weights[asset]
            / 100
        )

        budget_allocation_labels[asset].config(
            text=(
                f'{portfolio_weights[asset]:.0f}%  •  '
                f'{format_currency(amount)}'
            )
        )


def clear_budget():
    for entry in budget_entries.values():
        entry.delete(0, tk.END)

    update_budget_summary()


# ============================================================
# DARK CUSTOM ONBOARDING
# ============================================================

def show_onboarding():
    """
    Onboarding is intentionally modal and opens first.
    Native Tk radio buttons are not used because macOS can render
    them with white system backgrounds that are difficult to read.
    """

    window = tk.Toplevel(root)
    window.title("Build Your Learning Profile")
    window.geometry("720x760")
    window.configure(bg=BG)
    window.transient(root)
    window.grab_set()
    window.protocol("WM_DELETE_WINDOW", lambda: None)

    try:
        window.attributes("-topmost", True)
        window.after(
            500,
            lambda: window.attributes("-topmost", False),
        )
    except Exception:
        pass

    tk.Label(
        window,
        text="Build your starting model",
        font=FONT_TITLE,
        fg=TEXT,
        bg=BG,
    ).pack(
        padx=34,
        pady=(28, 4),
        anchor="w",
    )

    tk.Label(
        window,
        text=(
            "Choose one answer for each question. Your answers create "
            "an educational starting portfolio, then the app takes you "
            "directly into Portfolio Lab and loads matching examples."
        ),
        font=FONT_BODY,
        fg=MUTED,
        bg=BG,
        wraplength=645,
        justify="left",
    ).pack(
        padx=34,
        pady=(0, 18),
        anchor="w",
    )

    answers = {
        "objective": 2,
        "loss": 2,
        "horizon": 2,
    }

    answer_cards = {}

    def set_answer(
        group_key,
        value,
    ):
        answers[group_key] = value

        for option_value, widgets in answer_cards[group_key].items():
            selected = option_value == value

            bg = (
                CARD_SELECTED
                if selected
                else CARD_HOVER
            )

            border = (
                ACCENT
                if selected
                else BORDER
            )

            for widget in widgets:
                try:
                    widget.config(bg=bg)
                except Exception:
                    pass

            widgets[0].config(
                highlightbackground=border,
                highlightcolor=border,
            )

    def add_question(
        question_text,
        group_key,
        options,
    ):
        outer = tk.Frame(
            window,
            bg=CARD_BG,
            highlightbackground=BORDER,
            highlightthickness=1,
        )

        outer.pack(
            fill="x",
            padx=34,
            pady=7,
        )

        tk.Label(
            outer,
            text=question_text,
            font=FONT_SUBHEADER,
            fg=TEXT,
            bg=CARD_BG,
            wraplength=620,
            justify="left",
        ).pack(
            fill="x",
            padx=16,
            pady=(14, 8),
        )

        answer_cards[group_key] = {}

        for value, label in options:
            option_frame = tk.Frame(
                outer,
                bg=CARD_HOVER,
                highlightbackground=BORDER,
                highlightthickness=1,
                cursor="hand2",
            )

            option_frame.pack(
                fill="x",
                padx=16,
                pady=4,
            )

            marker = tk.Label(
                option_frame,
                text="●",
                font=("Helvetica", 11, "bold"),
                fg=ACCENT_LIGHT,
                bg=CARD_HOVER,
                cursor="hand2",
            )

            marker.pack(
                side="left",
                padx=(12, 9),
                pady=10,
            )

            label_widget = tk.Label(
                option_frame,
                text=label,
                font=FONT_BODY,
                fg=TEXT,
                bg=CARD_HOVER,
                anchor="w",
                justify="left",
                cursor="hand2",
            )

            label_widget.pack(
                side="left",
                fill="x",
                expand=True,
                padx=(0, 12),
                pady=10,
            )

            widgets = [
                option_frame,
                marker,
                label_widget,
            ]

            answer_cards[group_key][value] = widgets

            for widget in widgets:
                widget.bind(
                    "<Button-1>",
                    lambda event, g=group_key, v=value: set_answer(g, v),
                )

        tk.Frame(
            outer,
            bg=CARD_BG,
            height=8,
        ).pack()

        set_answer(
            group_key,
            answers[group_key],
        )

    add_question(
        "1. What matters most to you in this hypothetical portfolio?",
        "objective",
        [
            (1, "Keeping the value relatively stable"),
            (2, "Balancing stability and long-term growth"),
            (3, "Prioritizing long-term growth"),
        ],
    )

    add_question(
        "2. If the portfolio temporarily fell 20%, which reaction is closest?",
        "loss",
        [
            (1, "I would be very uncomfortable with that decline"),
            (2, "I would dislike it, but I could tolerate it"),
            (3, "Short-term declines would not concern me much"),
        ],
    )

    add_question(
        "3. Which hypothetical time horizon is closest?",
        "horizon",
        [
            (1, "Less than 5 years"),
            (2, "5–15 years"),
            (3, "15+ years"),
        ],
    )

    def finish():
        score = (
            answers["objective"]
            + answers["loss"]
            + answers["horizon"]
        )

        if score <= 4:
            profile = "Stability Focused"

            weights = {
                "Stocks": 35,
                "Bonds": 35,
                "Treasuries": 20,
                "Cash": 10,
            }

            growth = 25
            concentration = 15
            sectors = 20

        elif score <= 7:
            profile = "Balanced"

            weights = {
                "Stocks": 60,
                "Bonds": 25,
                "Treasuries": 10,
                "Cash": 5,
            }

            growth = 50
            concentration = 30
            sectors = 30

        else:
            profile = "Growth Focused"

            weights = {
                "Stocks": 85,
                "Bonds": 10,
                "Treasuries": 3,
                "Cash": 2,
            }

            growth = 80
            concentration = 50
            sectors = 55

        for asset, value in weights.items():
            portfolio_weights[asset] = float(value)

            allocation_sliders[asset].set_value(value)

        growth_var.set(growth)
        concentration_var.set(concentration)
        sector_var.set(sectors)

        profile_name_label.config(text=profile)

        # Clear old examples so the new onboarding result drives a fresh scan.
        latest_stock_matches.clear()
        latest_bond_matches.clear()
        latest_treasury_matches.clear()

        update_portfolio_lab()
        update_budget_summary()

        # Portfolio Lab is the first destination after onboarding.
        notebook.select(portfolio_tab)
        portfolio_scroll.scroll_to_top()

        window.destroy()

        # Force the stock category first and immediately load examples.
        explore_category.set("Stocks")
        dropdown_button.config(text="Stocks  ▼")

        refresh_explore_category()
        refresh_matching_stocks()
        refresh_bond_and_treasury_candidates()

    build_button_container = tk.Frame(
        window,
        bg=BG,
    )

    build_button_container.pack(
        fill="x",
        padx=34,
        pady=(16, 24),
    )

    build_button = tk.Label(
        build_button_container,
        text="Build My Model",
        font=("Helvetica", 12, "bold"),
        fg=TEXT,
        bg=ACCENT,
        padx=24,
        pady=12,
        cursor="hand2",
    )

    build_button.pack(
        side="right",
    )

    build_button.bind(
        "<Button-1>",
        lambda event: finish(),
    )


# ============================================================
# MAIN WINDOW
# ============================================================

root = tk.Tk()
root.title("Market Learn")
root.geometry("980x920")
root.minsize(800, 700)
root.configure(bg=BG)


# ============================================================
# HEADER
# ============================================================

header = tk.Frame(
    root,
    bg=BG,
)

header.pack(
    fill="x",
    padx=30,
    pady=(20, 12),
)

tk.Label(
    header,
    text="Market Learn",
    font=FONT_TITLE,
    fg=TEXT,
    bg=BG,
).pack(anchor="w")

tk.Label(
    header,
    text="Understand your money and the markets in one place.",
    font=FONT_SMALL,
    fg=MUTED,
    bg=BG,
).pack(
    anchor="w",
    pady=(3, 13),
)


# ============================================================
# SEARCH + BACK
# ============================================================

search_container = tk.Frame(
    header,
    bg=PANEL,
    highlightbackground=BORDER,
    highlightthickness=1,
)

search_container.pack(fill="x")

back_button = tk.Button(
    search_container,
    text="←",
    command=go_back,
    bg=PANEL,
    fg=TEXT,
    disabledforeground=MUTED_2,
    activebackground=CARD_HOVER,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    font=("Helvetica", 18, "bold"),
    padx=12,
    pady=5,
    state="disabled",
    cursor="hand2",
)

back_button.pack(
    side="left",
    padx=(5, 0),
    pady=5,
)

universal_entry = tk.Entry(
    search_container,
    font=("Helvetica", 13),
    bg=PANEL,
    fg=TEXT,
    insertbackground=TEXT,
    relief="flat",
    highlightthickness=0,
)

universal_entry.pack(
    side="left",
    fill="x",
    expand=True,
    padx=12,
    ipady=11,
)

PLACEHOLDER = "Search NVDA, Nvidia, BND, technology..."

universal_entry.insert(
    0,
    PLACEHOLDER,
)


def clear_placeholder(event):
    if universal_entry.get() == PLACEHOLDER:
        universal_entry.delete(0, tk.END)


universal_entry.bind(
    "<FocusIn>",
    clear_placeholder,
)

universal_entry.bind(
    "<Return>",
    lambda event: universal_search(),
)

search_button = tk.Button(
    search_container,
    text="Search",
    command=universal_search,
    bg=ACCENT,
    fg=TEXT,
    activebackground=ACCENT_LIGHT,
    activeforeground=TEXT,
    relief="flat",
    borderwidth=0,
    font=("Helvetica", 11, "bold"),
    padx=22,
    pady=10,
    cursor="hand2",
)

search_button.pack(
    side="right",
    padx=5,
    pady=5,
)


# ============================================================
# NOTEBOOK
# ============================================================

style = ttk.Style()

style.theme_use("default")

style.configure(
    "TNotebook",
    background=BG,
    borderwidth=0,
)

style.configure(
    "TNotebook.Tab",
    background=PANEL,
    foreground=MUTED,
    padding=[24, 10],
    font=FONT_BODY,
)

style.map(
    "TNotebook.Tab",
    background=[
        ("selected", CARD_BG)
    ],
    foreground=[
        ("selected", TEXT)
    ],
)

notebook = ttk.Notebook(root)

notebook.pack(
    fill="both",
    expand=True,
)


# ============================================================
# PORTFOLIO TAB FIRST
# ============================================================

portfolio_tab = tk.Frame(
    notebook,
    bg=BG,
)

notebook.add(
    portfolio_tab,
    text="Portfolio Lab",
)

portfolio_scroll = ScrollableFrame(
    portfolio_tab
)

portfolio_scroll.pack(
    fill="both",
    expand=True,
)


# PROFILE

section_header(
    portfolio_scroll.frame,
    "Your Learning Profile",
)

profile_card = make_card(
    portfolio_scroll.frame
)

tk.Label(
    profile_card,
    text="Current profile",
    font=FONT_SMALL,
    fg=MUTED,
    bg=CARD_BG,
).pack(
    padx=17,
    pady=(14, 2),
    anchor="w",
)

profile_name_label = tk.Label(
    profile_card,
    text="Balanced",
    font=FONT_HEADER,
    fg=ACCENT_LIGHT,
    bg=CARD_BG,
)

profile_name_label.pack(
    padx=17,
    pady=(0, 14),
    anchor="w",
)


# BUILD MODEL

section_header(
    portfolio_scroll.frame,
    "Build Your Model",
)

allocation_card = make_card(
    portfolio_scroll.frame
)

tk.Label(
    allocation_card,
    text=(
        "Drag any dot. The other categories automatically rebalance "
        "so the model always stays at 100%."
    ),
    font=FONT_SMALL,
    fg=MUTED,
    bg=CARD_BG,
    wraplength=760,
    justify="left",
).pack(
    fill="x",
    padx=17,
    pady=(14, 7),
)

for asset in [
    "Stocks",
    "Bonds",
    "Treasuries",
    "Cash",
]:
    slider = DotSlider(
        allocation_card,
        asset,
        portfolio_weights[asset],
        rebalance_portfolio,
    )

    slider.pack(
        fill="x",
        padx=17,
        pady=8,
    )

    allocation_sliders[asset] = slider

allocation_total_label = tk.Label(
    allocation_card,
    text="Total: 100%",
    font=("Helvetica", 11, "bold"),
    fg=GREEN,
    bg=CARD_BG,
)

allocation_total_label.pack(
    padx=17,
    pady=(5, 15),
    anchor="e",
)


# RISK CHARACTERISTICS

growth_var = tk.DoubleVar(value=50)
concentration_var = tk.DoubleVar(value=30)
sector_var = tk.DoubleVar(value=30)

section_header(
    portfolio_scroll.frame,
    "Risk Characteristics",
)

risk_input_card = make_card(
    portfolio_scroll.frame
)


def add_risk_slider(
    parent,
    title,
    variable,
    description,
):
    slider = DotSlider(
        parent,
        title,
        variable.get(),
        lambda slider_title, value: (
            variable.set(value),
            update_portfolio_lab(),
        ),
    )

    slider.pack(
        fill="x",
        padx=17,
        pady=(10, 1),
    )

    tk.Label(
        parent,
        text=description,
        font=FONT_SMALL,
        fg=MUTED,
        bg=CARD_BG,
        wraplength=740,
        justify="left",
    ).pack(
        fill="x",
        padx=17,
        pady=(0, 8),
    )

    # Keep Tk variable and visual slider synchronized when onboarding
    # changes the value programmatically.
    def sync(*args):
        slider.set_value(variable.get())

    variable.trace_add(
        "write",
        sync,
    )

    return slider


growth_slider = add_risk_slider(
    risk_input_card,
    "Growth / High-Beta Tilt",
    growth_var,
    "Higher values represent greater exposure to historically "
    "more aggressive market behavior.",
)

concentration_slider = add_risk_slider(
    risk_input_card,
    "Single-Company Concentration",
    concentration_var,
    "Higher values represent greater dependence on fewer companies.",
)

sector_slider = add_risk_slider(
    risk_input_card,
    "Sector Concentration",
    sector_var,
    "Higher values represent greater dependence on one industry or theme.",
)


# RISK METER

section_header(
    portfolio_scroll.frame,
    "Risk Meter",
)

risk_card = make_card(
    portfolio_scroll.frame
)

risk_name_label = tk.Label(
    risk_card,
    text="",
    font=FONT_HEADER,
    fg=GREEN,
    bg=CARD_BG,
)

risk_name_label.pack(
    padx=17,
    pady=(16, 2),
    anchor="w",
)

risk_score_label = tk.Label(
    risk_card,
    text="",
    font=FONT_NUMBER,
    fg=TEXT,
    bg=CARD_BG,
)

risk_score_label.pack(
    padx=17,
    anchor="w",
)

risk_canvas = tk.Canvas(
    risk_card,
    height=14,
    bg=CARD_BG,
    highlightthickness=0,
)

risk_canvas.pack(
    fill="x",
    padx=17,
    pady=(10, 11),
)

risk_description_label = tk.Label(
    risk_card,
    text="",
    font=FONT_BODY,
    fg=MUTED,
    bg=CARD_BG,
    wraplength=740,
    justify="left",
)

risk_description_label.pack(
    fill="x",
    padx=17,
    pady=(0, 15),
)


# RISK DETAILS

section_header(
    portfolio_scroll.frame,
    "Why This Model Has This Risk Level",
)

metrics_card = make_card(
    portfolio_scroll.frame
)

metric_widgets = {}

for title, key in [
    ("Estimated Beta", "beta"),
    ("Volatility Estimate", "volatility"),
    ("Drawdown Sensitivity", "drawdown"),
]:
    row = tk.Frame(
        metrics_card,
        bg=CARD_BG,
    )

    row.pack(
        fill="x",
        padx=17,
        pady=10,
    )

    tk.Label(
        row,
        text=title,
        font=FONT_BODY,
        fg=MUTED,
        bg=CARD_BG,
        width=22,
        anchor="w",
    ).pack(side="left")

    value_widget = tk.Label(
        row,
        text="",
        font=FONT_SUBHEADER,
        fg=TEXT,
        bg=CARD_BG,
    )

    value_widget.pack(side="left")

    metric_widgets[key] = value_widget

beta_value = metric_widgets["beta"]
volatility_value = metric_widgets["volatility"]
drawdown_value = metric_widgets["drawdown"]


# EXPLORE MODEL

section_header(
    portfolio_scroll.frame,
    "Explore This Model",
)

explore_card = make_card(
    portfolio_scroll.frame
)

tk.Label(
    explore_card,
    text=(
        "Choose a category. The app will show up to 10 research "
        "examples tied to the current model."
    ),
    font=FONT_SMALL,
    fg=MUTED,
    bg=CARD_BG,
    wraplength=740,
    justify="left",
).pack(
    fill="x",
    padx=17,
    pady=(14, 8),
)

explore_category = tk.StringVar(
    value="Stocks",
)


def set_explore_category(category):
    explore_category.set(category)

    dropdown_button.config(
        text=f"{category}  ▼",
    )

    refresh_explore_category()


def open_explore_menu():
    menu = tk.Menu(
        root,
        tearoff=0,
        bg=CARD_HOVER,
        fg=TEXT,
        activebackground=ACCENT,
        activeforeground=TEXT,
        bd=0,
        relief="flat",
        font=FONT_BODY,
    )

    for category in [
        "Stocks",
        "Bonds",
        "Treasuries",
        "Cash / HYSA",
    ]:
        menu.add_command(
            label=category,
            command=lambda c=category: set_explore_category(c),
        )

    x = dropdown_button.winfo_rootx()
    y = (
        dropdown_button.winfo_rooty()
        + dropdown_button.winfo_height()
    )

    try:
        menu.tk_popup(x, y)
    finally:
        menu.grab_release()


dropdown_container = tk.Frame(
    explore_card,
    bg=PANEL,
    highlightbackground=BORDER,
    highlightthickness=1,
)

dropdown_container.pack(
    fill="x",
    padx=17,
    pady=(5, 14),
)

# Use a Label instead of a native Button to avoid macOS white-button styling.
dropdown_button = tk.Label(
    dropdown_container,
    text="Stocks  ▼",
    bg=PANEL,
    fg=TEXT,
    font=FONT_BODY,
    anchor="w",
    padx=14,
    pady=11,
    cursor="hand2",
)

dropdown_button.pack(fill="x")

dropdown_button.bind(
    "<Button-1>",
    lambda event: open_explore_menu(),
)

explore_results_frame = tk.Frame(
    explore_card,
    bg=CARD_BG,
)

explore_results_frame.pack(
    fill="x",
    padx=13,
    pady=(0, 13),
)


# DISCLAIMER

disclaimer_card = make_card(
    portfolio_scroll.frame
)

tk.Label(
    disclaimer_card,
    text=(
        "Educational simulation only. Portfolio models, risk scores, "
        "securities, funds, savings providers, analyst opinions, and "
        "other information shown here are presented for research and "
        "education. They are not personalized recommendations or "
        "instructions to buy, sell, or hold an investment."
    ),
    font=FONT_SMALL,
    fg=MUTED,
    bg=CARD_BG,
    wraplength=740,
    justify="left",
).pack(
    padx=17,
    pady=15,
    anchor="w",
)


# ============================================================
# RESEARCH TAB
# ============================================================

research_tab = tk.Frame(
    notebook,
    bg=BG,
)

notebook.add(
    research_tab,
    text="Research",
)

research_results = ScrollableFrame(
    research_tab
)

research_results.pack(
    fill="both",
    expand=True,
)

show_message(
    research_results.frame,
    (
        "Search a company, ticker, ETF, fund, or sector above.\n\n"
        "Examples: NVDA, Nvidia, BND, technology, energy."
    ),
)


# ============================================================
# BUDGET TAB
# ============================================================

budget_tab = tk.Frame(
    notebook,
    bg=BG,
)

notebook.add(
    budget_tab,
    text="Budget",
)

budget_scroll = ScrollableFrame(
    budget_tab
)

budget_scroll.pack(
    fill="both",
    expand=True,
)

section_header(
    budget_scroll.frame,
    "Monthly Budget",
)

budget_intro = make_card(
    budget_scroll.frame
)

tk.Label(
    budget_intro,
    text=(
        "Enter monthly take-home income and expenses. The summary "
        "shows what remains and connects the available amount to "
        "your current educational portfolio model."
    ),
    font=FONT_BODY,
    fg=MUTED,
    bg=CARD_BG,
    wraplength=740,
    justify="left",
).pack(
    fill="x",
    padx=17,
    pady=15,
)

budget_entries = {}

budget_fields = [
    "Monthly Income",
    "Housing",
    "Utilities",
    "Groceries",
    "Transportation",
    "Insurance",
    "Dining",
    "Entertainment",
    "Shopping",
    "Debt Payments",
    "Other Spending",
]

section_header(
    budget_scroll.frame,
    "Income & Spending",
)

budget_input_card = make_card(
    budget_scroll.frame
)

for field in budget_fields:
    row = tk.Frame(
        budget_input_card,
        bg=CARD_BG,
    )

    row.pack(
        fill="x",
        padx=17,
        pady=6,
    )

    tk.Label(
        row,
        text=field,
        font=FONT_BODY,
        fg=(
            TEXT
            if field == "Monthly Income"
            else MUTED
        ),
        bg=CARD_BG,
        width=22,
        anchor="w",
    ).pack(side="left")

    entry = tk.Entry(
        row,
        bg=PANEL,
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        highlightbackground=BORDER,
        highlightthickness=1,
        font=FONT_BODY,
    )

    entry.pack(
        side="right",
        fill="x",
        expand=True,
        ipady=7,
        padx=(12, 0),
    )

    entry.bind(
        "<KeyRelease>",
        update_budget_summary,
    )

    budget_entries[field] = entry

clear_budget_label = tk.Label(
    budget_input_card,
    text="Clear budget",
    font=("Helvetica", 10, "underline"),
    fg=ACCENT_LIGHT,
    bg=CARD_BG,
    cursor="hand2",
)

clear_budget_label.pack(
    padx=17,
    pady=(7, 15),
    anchor="e",
)

clear_budget_label.bind(
    "<Button-1>",
    lambda event: clear_budget(),
)


# BUDGET SUMMARY

section_header(
    budget_scroll.frame,
    "Budget Summary",
)

budget_summary_card = make_card(
    budget_scroll.frame
)

summary_widgets = {}

for label in [
    "Monthly Income",
    "Monthly Spending",
    "Available After Spending",
    "Savings Rate",
]:
    row = tk.Frame(
        budget_summary_card,
        bg=CARD_BG,
    )

    row.pack(
        fill="x",
        padx=17,
        pady=8,
    )

    tk.Label(
        row,
        text=label,
        font=FONT_BODY,
        fg=MUTED,
        bg=CARD_BG,
        width=25,
        anchor="w",
    ).pack(side="left")

    value = tk.Label(
        row,
        text="$0.00",
        font=FONT_SUBHEADER,
        fg=TEXT,
        bg=CARD_BG,
    )

    value.pack(side="left")

    summary_widgets[label] = value

budget_income_value = summary_widgets["Monthly Income"]
budget_spending_value = summary_widgets["Monthly Spending"]
budget_remaining_value = summary_widgets["Available After Spending"]
budget_savings_rate_value = summary_widgets["Savings Rate"]


# MONTHLY PORTFOLIO ALLOCATION

section_header(
    budget_scroll.frame,
    "Illustrative Monthly Allocation",
)

budget_allocation_card = make_card(
    budget_scroll.frame
)

tk.Label(
    budget_allocation_card,
    text=(
        "If the amount remaining after spending were used with the "
        "current educational portfolio model, it would break down like this:"
    ),
    font=FONT_SMALL,
    fg=MUTED,
    bg=CARD_BG,
    wraplength=740,
    justify="left",
).pack(
    fill="x",
    padx=17,
    pady=(14, 8),
)

budget_allocation_labels = {}

for asset in [
    "Stocks",
    "Bonds",
    "Treasuries",
    "Cash",
]:
    row = tk.Frame(
        budget_allocation_card,
        bg=CARD_BG,
    )

    row.pack(
        fill="x",
        padx=17,
        pady=7,
    )

    tk.Label(
        row,
        text=asset,
        font=FONT_BODY,
        fg=TEXT,
        bg=CARD_BG,
        width=18,
        anchor="w",
    ).pack(side="left")

    value = tk.Label(
        row,
        text="$0.00",
        font=FONT_SUBHEADER,
        fg=ACCENT_LIGHT,
        bg=CARD_BG,
    )

    value.pack(side="left")

    budget_allocation_labels[asset] = value

tk.Frame(
    budget_allocation_card,
    height=10,
    bg=CARD_BG,
).pack()


# ============================================================
# FOOTER
# ============================================================

tk.Label(
    root,
    text=(
        "Educational information only • "
        "No personalized investment advice"
    ),
    font=FONT_SMALL,
    fg=MUTED_2,
    bg=BG,
).pack(
    pady=(6, 12),
)


# ============================================================
# INITIALIZATION
# ============================================================

# Portfolio tab is selected under the onboarding modal so finishing
# onboarding lands exactly where expected.
notebook.select(portfolio_tab)

root.after(
    250,
    update_portfolio_lab,
)

root.after(
    350,
    update_budget_summary,
)

# IMPORTANT: onboarding is first.
root.after(
    450,
    show_onboarding,
)


# ============================================================
# START
# ============================================================

root.mainloop()
