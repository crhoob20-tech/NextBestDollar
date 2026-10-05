# MNQ Research Engine

Standalone quantitative research package for the MNQ/NQ intraday strategy project.

This lives on the `mnq-research` branch so the production NextBestDollar application remains untouched.

## Current strategy sleeves

1. **4/4 Regime Pullback**
   - Overnight direction
   - RTH gap direction
   - Prior-day RTH candle body
   - 09:30–09:45 ET opening-range direction
   - All four must agree before a continuation setup is allowed.
   - Entry requires an OR breakout, pullback that holds outside the range, and reclaim.

2. **Open Drive**
   - First 15-minute drive must be directionally strong relative to its recent range distribution.
   - Gap must agree with the opening drive.
   - Designed to capture trend days that never provide a clean pullback.

3. **BOS Structural Retracement**
   - Completed 5-minute HH/HL or LL/LH trend structure.
   - Body-close break of structure.
   - 1-minute retracement into the completed BOS body.
   - Structural stop capped at 30 index points.

4. **Major-Level Rejection**
   - Prior-day high/low and overnight high/low.
   - Requires a completed 5-minute rejection candle.
   - Maximum two trades per day.

## Backtest window

Current public-data test window: **2026-03-26 through 2026-09-25**.

The source is a public NAS100 1-minute OHLCV proxy. This is intentionally used only for research until we connect a proper CME MNQ/NQ data feed.

### Important limitation

NAS100 proxy data is not the same instrument as CME MNQ futures. It does not reproduce futures basis, contract rolls, CME volume, bid/ask spread, queue position, or broker-specific fills. Dollar P&L is only an approximation using MNQ's $2/index-point multiplier plus a conservative estimated round-trip cost.

## News regime tagging

Trades are tagged for major scheduled macro-event days including:

- CPI
- PPI
- Employment Situation / NFP
- PCE / major BEA income-and-spending releases
- FOMC decisions

The report compares news-day expectancy with normal-day expectancy.

## Metrics

Each sleeve reports:

- Trade count
- Win rate
- Expectancy in R
- Profit factor
- Total R
- Maximum drawdown in R
- Approximate net P&L for 1 MNQ
- Normal-day vs news-day expectancy
- Bootstrap probability that mean R is positive
- Bootstrap 95% interval for mean R

## Run locally

```bash
cd mnq_research
python -m pip install -r requirements.txt
python backtest.py
```

Outputs are written to `mnq_research/results/`:

- `summary.csv`
- `trades.csv`
- `daily_regime_stats.csv`
- `report.md`

## Research rules

- Strategy rules are frozen before inspecting results.
- No strategy is promoted from backtest directly to live trading.
- Changes should be tested one variable at a time.
- Transaction friction is included.
- High-impact-news performance is tracked separately.
- A strategy needs meaningful sample size and out-of-sample/forward evidence before capital is allocated.

## Brokerage roadmap

The future execution stack is intentionally separated from strategy logic:

`market data -> strategies -> signal router -> risk engine -> paper broker -> live broker adapter`

Paper execution comes before any live connection. Live adapters should include hard contract limits, daily-loss limits, stale-data protection, duplicate-order protection, broker-side brackets, full event logging, and a flatten-all kill switch.
