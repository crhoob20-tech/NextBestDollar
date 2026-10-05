from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

DATA_URL = "https://raw.githubusercontent.com/getdata-finance/nas100-1m-ohlcv-index-historical-data/main/NAS100_1m.csv"
ET = "America/New_York"
POINT_VALUE_MNQ = 2.0
ESTIMATED_RT_COST_USD = 4.0
DATA_START = "2026-03-26"
DATA_END = "2026-09-25"

OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)

NEWS_EVENTS = {
    "2026-04-03": "NFP",
    "2026-04-09": "PCE/GDP",
    "2026-04-10": "CPI",
    "2026-04-14": "PPI",
    "2026-04-29": "FOMC",
    "2026-04-30": "PCE/GDP",
    "2026-05-08": "NFP",
    "2026-05-12": "CPI",
    "2026-05-13": "PPI",
    "2026-05-28": "PCE/GDP",
    "2026-06-05": "NFP",
    "2026-06-10": "CPI",
    "2026-06-11": "PPI",
    "2026-06-17": "FOMC",
    "2026-06-25": "PCE/GDP",
    "2026-07-02": "NFP",
    "2026-07-14": "CPI",
    "2026-07-15": "PPI",
    "2026-07-29": "FOMC",
    "2026-07-30": "PCE/GDP",
    "2026-08-07": "NFP",
    "2026-08-12": "CPI",
    "2026-08-13": "PPI",
    "2026-08-26": "PCE/GDP",
    "2026-09-04": "NFP",
    "2026-09-10": "PPI",
    "2026-09-11": "CPI",
    "2026-09-16": "FOMC",
}

@dataclass
class Trade:
    strategy: str
    date: str
    side: str
    entry_time: pd.Timestamp
    exit_time: pd.Timestamp
    entry: float
    exit: float
    stop: float
    target: float | None
    risk_points: float
    points: float
    r: float
    result: str
    news: str

    @property
    def net_usd_mnq(self) -> float:
        return self.points * POINT_VALUE_MNQ - ESTIMATED_RT_COST_USD


def sign(x: float, eps: float = 1e-9) -> int:
    return 1 if x > eps else (-1 if x < -eps else 0)


def load_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    print(f"Downloading 1m proxy data: {DATA_URL}", flush=True)
    df = pd.read_csv(DATA_URL)
    df["datetime"] = pd.to_datetime(df["datetime"], utc=True).dt.tz_convert(ET)
    for c in ["open", "high", "low", "close", "volume"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna(subset=["datetime", "open", "high", "low", "close"]).sort_values("datetime")
    df = df[(df["datetime"].dt.date >= pd.Timestamp(DATA_START).date()) &
            (df["datetime"].dt.date <= pd.Timestamp(DATA_END).date())]
    df = df.set_index("datetime")
    df5 = (
        df.resample("5min", label="left", closed="left")
        .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
        .dropna(subset=["open", "high", "low", "close"])
    )
    return df, df5


def between(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return df[(df.index >= start) & (df.index < end)]


def ts(d, hhmm: str) -> pd.Timestamp:
    return pd.Timestamp(f"{d} {hhmm}", tz=ET)


def trading_days(df1: pd.DataFrame) -> list:
    idx = df1.index
    mask = (idx.time >= pd.Timestamp("09:30").time()) & (idx.time < pd.Timestamp("16:00").time())
    return sorted(set(idx[mask].date))


def build_day_stats(df1: pd.DataFrame) -> pd.DataFrame:
    days = trading_days(df1)
    rows = []
    for i, d in enumerate(days):
        rth = between(df1, ts(d, "09:30"), ts(d, "16:00"))
        if len(rth) < 300:
            continue
        or15 = between(df1, ts(d, "09:30"), ts(d, "09:45"))
        if len(or15) < 12:
            continue
        prev_d = days[i - 1] if i else None
        if prev_d is None:
            continue
        prev = between(df1, ts(prev_d, "09:30"), ts(prev_d, "16:00"))
        if len(prev) < 300:
            continue

        overnight_start_date = (pd.Timestamp(d) - pd.Timedelta(days=1)).date()
        overnight = between(df1, ts(overnight_start_date, "18:00"), ts(d, "09:30"))
        if len(overnight) < 30:
            continue

        prior_open = float(prev.iloc[0].open)
        prior_close = float(prev.iloc[-1].close)
        cur_open = float(rth.iloc[0].open)
        overnight_open = float(overnight.iloc[0].open)
        overnight_close = float(overnight.iloc[-1].close)
        or_open = float(or15.iloc[0].open)
        or_close = float(or15.iloc[-1].close)
        or_high = float(or15.high.max())
        or_low = float(or15.low.min())

        factors = [
            sign(overnight_close - overnight_open),
            sign(cur_open - prior_close),
            sign(prior_close - prior_open),
            sign(or_close - or_open),
        ]
        aligned = factors[0] if len(set(factors)) == 1 and factors[0] != 0 else 0

        rows.append({
            "date": d,
            "prev_date": prev_d,
            "prior_open": prior_open,
            "prior_close": prior_close,
            "prior_high": float(prev.high.max()),
            "prior_low": float(prev.low.min()),
            "overnight_open": overnight_open,
            "overnight_close": overnight_close,
            "overnight_high": float(overnight.high.max()),
            "overnight_low": float(overnight.low.min()),
            "rth_open": cur_open,
            "or_open": or_open,
            "or_close": or_close,
            "or_high": or_high,
            "or_low": or_low,
            "or_width": or_high - or_low,
            "overnight_dir": factors[0],
            "gap_dir": factors[1],
            "prior_body_dir": factors[2],
            "or_dir": factors[3],
            "aligned_4of4": aligned,
            "news": NEWS_EVENTS.get(str(d), "NORMAL"),
        })
    stats = pd.DataFrame(rows).set_index("date")
    stats["or_median_20"] = stats["or_width"].shift(1).rolling(20, min_periods=10).median()
    return stats


def simulate(
    df1: pd.DataFrame,
    strategy: str,
    d,
    side: int,
    entry_time: pd.Timestamp,
    entry: float,
    stop: float,
    target: float | None,
    end_hhmm: str,
    news: str,
) -> Trade | None:
    risk = (entry - stop) if side == 1 else (stop - entry)
    if risk <= 0 or not np.isfinite(risk):
        return None
    bars = between(df1, entry_time + pd.Timedelta(minutes=1), ts(d, end_hhmm) + pd.Timedelta(minutes=1))
    if bars.empty:
        return None

    exit_price = float(bars.iloc[-1].close)
    exit_time = bars.index[-1]
    result = "EOD"

    for t, b in bars.iterrows():
        if side == 1:
            stop_hit = b.low <= stop
            target_hit = target is not None and b.high >= target
            if stop_hit:
                exit_price, exit_time, result = stop, t, "LOSS"
                break
            if target_hit:
                exit_price, exit_time, result = float(target), t, "WIN"
                break
        else:
            stop_hit = b.high >= stop
            target_hit = target is not None and b.low <= target
            if stop_hit:
                exit_price, exit_time, result = stop, t, "LOSS"
                break
            if target_hit:
                exit_price, exit_time, result = float(target), t, "WIN"
                break

    points = (exit_price - entry) if side == 1 else (entry - exit_price)
    r = points / risk
    if result == "EOD":
        result = "WIN" if points > 0 else ("LOSS" if points < 0 else "FLAT")

    return Trade(
        strategy=strategy,
        date=str(d),
        side="LONG" if side == 1 else "SHORT",
        entry_time=entry_time,
        exit_time=exit_time,
        entry=entry,
        exit=float(exit_price),
        stop=float(stop),
        target=float(target) if target is not None else None,
        risk_points=float(risk),
        points=float(points),
        r=float(r),
        result=result,
        news=news,
    )


def strategy_4of4(df1: pd.DataFrame, df5: pd.DataFrame, stats: pd.DataFrame) -> list[Trade]:
    trades = []
    for d, s in stats.iterrows():
        side = int(s.aligned_4of4)
        if side == 0 or not (20 <= s.or_width <= 220):
            continue
        bars = between(df5, ts(d, "09:45"), ts(d, "11:30"))
        if bars.empty:
            continue
        boundary = s.or_high if side == 1 else s.or_low

        breakout_idx = None
        for j, (t, b) in enumerate(bars.iterrows()):
            if (side == 1 and b.close > s.or_high) or (side == -1 and b.close < s.or_low):
                breakout_idx = j
                break
        if breakout_idx is None:
            continue

        arr = list(bars.iterrows())
        pull_idx = None
        for j in range(breakout_idx + 1, min(len(arr), breakout_idx + 7)):
            _, b = arr[j]
            if side == 1:
                if boundary <= b.low <= boundary + 0.25 * s.or_width and b.close >= boundary:
                    pull_idx = j
                    break
            else:
                if boundary - 0.25 * s.or_width <= b.high <= boundary and b.close <= boundary:
                    pull_idx = j
                    break
        if pull_idx is None:
            continue

        pull_t, pull_b = arr[pull_idx]
        reclaim = None
        for j in range(pull_idx + 1, min(len(arr), pull_idx + 4)):
            t, b = arr[j]
            if (side == 1 and b.close > pull_b.high) or (side == -1 and b.close < pull_b.low):
                reclaim = (t, b)
                break
        if reclaim is None:
            continue

        et, eb = reclaim
        entry = float(eb.close)
        risk = 0.5 * float(s.or_width)
        stop = entry - side * risk
        target = entry + side * 1.5 * risk
        tr = simulate(df1, "4of4_regime_pullback", d, side, et + pd.Timedelta(minutes=4),
                      entry, stop, target, "15:45", s.news)
        if tr:
            trades.append(tr)
    return trades


def strategy_open_drive(df1: pd.DataFrame, stats: pd.DataFrame) -> list[Trade]:
    trades = []
    for d, s in stats.iterrows():
        med = s.or_median_20
        side = int(s.or_dir)
        if side == 0 or pd.isna(med) or med <= 0:
            continue
        if not (0.80 * med <= s.or_width <= 2.50 * med):
            continue
        if int(s.gap_dir) != side:
            continue

        loc = (s.or_close - s.or_low) / s.or_width if s.or_width else 0.5
        if side == 1 and loc < 0.75:
            continue
        if side == -1 and loc > 0.25:
            continue

        entry_bar = between(df1, ts(d, "09:45"), ts(d, "09:46"))
        if entry_bar.empty:
            continue
        entry = float(entry_bar.iloc[0].open)
        risk = 0.60 * float(s.or_width)
        if not (12 <= risk <= 150):
            continue
        stop = entry - side * risk
        tr = simulate(df1, "open_drive", d, side, ts(d, "09:45"), entry, stop, None, "15:45", s.news)
        if tr:
            trades.append(tr)
    return trades


def strategy_major_levels(df1: pd.DataFrame, df5: pd.DataFrame, stats: pd.DataFrame) -> list[Trade]:
    trades = []
    for d, s in stats.iterrows():
        levels = [
            ("PDL", 1, float(s.prior_low)),
            ("ONL", 1, float(s.overnight_low)),
            ("PDH", -1, float(s.prior_high)),
            ("ONH", -1, float(s.overnight_high)),
        ]
        used = set()
        cursor_time = ts(d, "09:45")
        day_count = 0
        bars = between(df5, ts(d, "09:45"), ts(d, "14:30"))

        for t, b in bars.iterrows():
            if t < cursor_time or day_count >= 2:
                continue
            candidates = []
            for name, side, level in levels:
                if name in used:
                    continue
                if side == 1 and b.low <= level and b.close > level and b.close > b.open:
                    candidates.append((abs(b.close - level), name, side, level))
                if side == -1 and b.high >= level and b.close < level and b.close < b.open:
                    candidates.append((abs(b.close - level), name, side, level))
            if not candidates:
                continue
            _, name, side, level = sorted(candidates)[0]
            entry = float(b.close)
            stop = float(b.low - 2.0) if side == 1 else float(b.high + 2.0)
            risk = (entry - stop) if side == 1 else (stop - entry)
            if not (5 <= risk <= 60):
                used.add(name)
                continue
            target = entry + side * 1.5 * risk
            tr = simulate(df1, "major_level_rejection", d, side, t + pd.Timedelta(minutes=4),
                          entry, stop, target, "15:30", s.news)
            used.add(name)
            if tr:
                trades.append(tr)
                day_count += 1
                cursor_time = tr.exit_time + pd.Timedelta(minutes=5)
    return trades


def strategy_bos_retrace(df1: pd.DataFrame, df5: pd.DataFrame, stats: pd.DataFrame) -> list[Trade]:
    trades = []
    stats_dates = set(stats.index)
    for d in trading_days(df1):
        if d not in stats_dates:
            continue
        s = stats.loc[d]
        bars5 = between(df5, ts(d, "06:00"), ts(d, "14:00"))
        arr = list(bars5.iterrows())
        swing_highs: list[tuple[float, int]] = []
        swing_lows: list[tuple[float, int]] = []
        last_exit = ts(d, "00:00")
        day_count = 0
        seen_bos = set()

        for i in range(2, len(arr)):
            t, bar = arr[i]
            p1_t, p1 = arr[i - 1]
            _, p2 = arr[i - 2]

            if p1.high > p2.high and p1.high > bar.high:
                if not swing_lows or p1.high - swing_lows[-1][0] >= 5:
                    swing_highs.append((float(p1.high), i - 1))
            if p1.low < p2.low and p1.low < bar.low:
                if not swing_highs or swing_highs[-1][0] - p1.low >= 5:
                    swing_lows.append((float(p1.low), i - 1))

            if not (ts(d, "08:30") <= t < ts(d, "13:30")):
                continue
            if day_count >= 3 or len(swing_highs) < 2 or len(swing_lows) < 2:
                continue

            hh = swing_highs[-1][0] > swing_highs[-2][0]
            hl = swing_lows[-1][0] > swing_lows[-2][0]
            ll = swing_lows[-1][0] < swing_lows[-2][0]
            lh = swing_highs[-1][0] < swing_highs[-2][0]

            side = 0
            if hh and hl and bar.close > swing_highs[-1][0] and bar.close > bar.open:
                side = 1
            elif ll and lh and bar.close < swing_lows[-1][0] and bar.close < bar.open:
                side = -1
            if side == 0 or i in seen_bos:
                continue
            seen_bos.add(i)

            created = t + pd.Timedelta(minutes=5)
            if created < last_exit:
                continue

            if side == 1:
                zone_top, zone_bottom = float(bar.close), float(bar.open)
                stop = float(bar.low - 1.0)
            else:
                zone_top, zone_bottom = float(bar.open), float(bar.close)
                stop = float(bar.high + 1.0)

            if zone_top <= zone_bottom + 1:
                continue

            search = between(df1, created, min(created + pd.Timedelta(minutes=60), ts(d, "13:45")))
            entry_t = None
            entry = None
            for mt, mb in search.iterrows():
                if side == 1 and mb.low <= zone_top and mb.close >= zone_bottom and abs(mb.close - zone_top) <= 5:
                    risk = float(mb.close) - stop
                    if 0 < risk <= 30:
                        entry_t, entry = mt, float(mb.close)
                        break
                if side == -1 and mb.high >= zone_bottom and mb.close <= zone_top and abs(mb.close - zone_bottom) <= 5:
                    risk = stop - float(mb.close)
                    if 0 < risk <= 30:
                        entry_t, entry = mt, float(mb.close)
                        break

            if entry_t is None:
                continue
            risk = (entry - stop) if side == 1 else (stop - entry)
            target = entry + side * 1.1 * risk
            tr = simulate(df1, "bos_structural_retrace", d, side, entry_t, entry, stop, target, "15:30", s.news)
            if tr:
                trades.append(tr)
                day_count += 1
                last_exit = tr.exit_time + pd.Timedelta(minutes=2)
    return trades


def max_drawdown_r(rs: Iterable[float]) -> float:
    x = np.cumsum(list(rs))
    if len(x) == 0:
        return 0.0
    peaks = np.maximum.accumulate(np.r_[0.0, x])[:-1]
    dd = peaks - x
    return float(np.max(dd)) if len(dd) else 0.0


def bootstrap_positive_probability(rs: np.ndarray, n_boot: int = 10000, seed: int = 42) -> tuple[float, float, float]:
    if len(rs) < 2:
        return float("nan"), float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = np.empty(n_boot)
    for i in range(n_boot):
        means[i] = rng.choice(rs, size=len(rs), replace=True).mean()
    return float((means > 0).mean()), float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def summarize(trades: list[Trade]) -> dict:
    if not trades:
        return {}
    rs = np.array([t.r for t in trades], dtype=float)
    pnl = np.array([t.net_usd_mnq for t in trades], dtype=float)
    wins = rs > 0
    gross_win = rs[rs > 0].sum()
    gross_loss = -rs[rs < 0].sum()
    pf = gross_win / gross_loss if gross_loss > 0 else float("inf")
    ppos, ci_lo, ci_hi = bootstrap_positive_probability(rs)
    news_mask = np.array([t.news != "NORMAL" for t in trades])
    return {
        "trades": len(trades),
        "win_rate": float(wins.mean()),
        "expectancy_r": float(rs.mean()),
        "profit_factor_r": float(pf),
        "total_r": float(rs.sum()),
        "max_drawdown_r": max_drawdown_r(rs),
        "net_usd_1_mnq": float(pnl.sum()),
        "avg_net_usd_trade": float(pnl.mean()),
        "news_trades": int(news_mask.sum()),
        "news_expectancy_r": float(rs[news_mask].mean()) if news_mask.any() else float("nan"),
        "normal_expectancy_r": float(rs[~news_mask].mean()) if (~news_mask).any() else float("nan"),
        "bootstrap_p_mean_r_gt_0": ppos,
        "bootstrap_mean_r_ci_low": ci_lo,
        "bootstrap_mean_r_ci_high": ci_hi,
    }


def write_report(all_trades: list[Trade], stats: pd.DataFrame) -> None:
    trade_rows = []
    for t in all_trades:
        trade_rows.append({**t.__dict__, "net_usd_1_mnq": t.net_usd_mnq})
    tdf = pd.DataFrame(trade_rows)
    if not tdf.empty:
        tdf.to_csv(OUT / "trades.csv", index=False)

    summaries = []
    for name in sorted(tdf.strategy.unique()) if not tdf.empty else []:
        sub = [t for t in all_trades if t.strategy == name]
        summaries.append({"strategy": name, **summarize(sub)})

    if all_trades:
        summaries.append({"strategy": "portfolio_all_sleeves", **summarize(all_trades)})

    sdf = pd.DataFrame(summaries)
    sdf.to_csv(OUT / "summary.csv", index=False)
    stats.reset_index().to_csv(OUT / "daily_regime_stats.csv", index=False)

    md = []
    md.append("# MNQ Research — Six-Month Proxy Backtest\n")
    md.append(f"Data window: **{DATA_START} through {DATA_END}**. Source is NAS100 cash/CFD-style 1-minute OHLCV, not CME MNQ futures.")
    md.append("Dollar P&L is therefore an **MNQ point-value approximation** ($2/point) with $4 estimated round-trip friction, not a broker-grade futures fill simulation.\n")
    md.append("## Strategy Scorecard\n")
    if sdf.empty:
        md.append("No trades generated.\n")
    else:
        show = sdf.copy()
        for c in ["win_rate", "bootstrap_p_mean_r_gt_0"]:
            show[c] = (show[c] * 100).round(1)
        for c in ["expectancy_r", "profit_factor_r", "total_r", "max_drawdown_r",
                  "news_expectancy_r", "normal_expectancy_r",
                  "bootstrap_mean_r_ci_low", "bootstrap_mean_r_ci_high"]:
            if c in show:
                show[c] = show[c].round(3)
        for c in ["net_usd_1_mnq", "avg_net_usd_trade"]:
            if c in show:
                show[c] = show[c].round(2)
        md.append(show.to_markdown(index=False))
        md.append("\n")

    md.append("## Fixed Rules\n")
    md.append("- **4/4 Regime Pullback:** overnight direction, gap, prior-day RTH body, and first 15-minute direction must all agree; OR breakout; pullback must hold outside the OR; reclaim; 0.5×OR stop; 1.5R target.")
    md.append("- **Open Drive:** first-15-minute range must be 0.8–2.5× its trailing 20-session median, close in outer quartile, and gap agrees; enter 09:45; 0.6×OR stop; hold until 15:45.")
    md.append("- **BOS Structural Retrace:** completed 5-minute HH/HL or LL/LH structure, body-close BOS, retrace into completed BOS body on 1-minute data, structural stop capped at 30 points, 1.1R target.")
    md.append("- **Major-Level Rejection:** rejection of prior-day or overnight high/low after 09:45; structural stop; 1.5R target; maximum two trades/day.")
    md.append("\n## News Tags\n")
    md.append("Trade dates are tagged for NFP, CPI, PPI, PCE/GDP and FOMC decision days. News-day and normal-day expectancy are reported separately.")
    md.append("\n## Guardrails\n")
    md.append("These results are research, not evidence of guaranteed future profitability. The proxy does not reproduce CME futures basis, bid/ask, queue position, exchange volume, contract rolls, or broker-specific commissions. Any live connection should start with paper trading and hard risk limits.\n")

    (OUT / "report.md").write_text("\n\n".join(md), encoding="utf-8")


def main():
    df1, df5 = load_data()
    stats = build_day_stats(df1)
    print(f"Loaded {len(df1):,} 1m bars, {len(df5):,} 5m bars, {len(stats)} scored sessions.", flush=True)

    model_trades = {
        "4of4": strategy_4of4(df1, df5, stats),
        "open_drive": strategy_open_drive(df1, stats),
        "bos": strategy_bos_retrace(df1, df5, stats),
        "levels": strategy_major_levels(df1, df5, stats),
    }
    for k, v in model_trades.items():
        print(k, summarize(v), flush=True)

    all_trades = [t for group in model_trades.values() for t in group]
    all_trades.sort(key=lambda t: t.entry_time)
    write_report(all_trades, stats)
    print(f"Results written to {OUT}", flush=True)


if __name__ == "__main__":
    main()
