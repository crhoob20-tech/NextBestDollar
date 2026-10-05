# Methodology

## Objective

Evaluate several independent intraday Nasdaq strategy sleeves over a recent six-month regime without weakening the user's existing 4/4 directional filter merely to create more trades.

## Primary comparison

All sleeves use the same source dataset and are scored using the same core metrics. Strategy-specific rules are fixed before results are inspected.

## Strategies

### 4/4 Regime Pullback
All four morning directional factors must agree: overnight direction, gap direction, prior-day RTH candle body, and 09:30–09:45 ET opening direction. Entry occurs only after an opening-range breakout, a pullback that remains outside the opening range, and a reclaim.

### Open Drive
A separate trend-day sleeve. It requires the opening range to be neither abnormally small nor extremely large relative to its trailing distribution, the 15-minute close to finish in the outer quartile, and the gap to agree with the drive. This sleeve does not require 4/4 agreement.

### BOS Structural Retracement
A higher-frequency sleeve based on completed 5-minute market structure and 1-minute retracement execution. Entries occur only after a confirmed body-close break of structure and use structural stops.

### Major-Level Rejection
Tests rejection behavior at prior-day and overnight highs/lows. This remains a challenger because prior research suggests regime sensitivity.

## News analysis

Major scheduled macro days are tagged rather than automatically discarded. This allows the backtest to answer whether a sleeve is helped or harmed by high-impact event regimes. The initial event set includes CPI, PPI, Employment Situation/NFP, PCE/major BEA releases, and FOMC decisions.

## Statistical interpretation

No single metric is treated as proof. The scorecard emphasizes trade count, expectancy in R, profit factor, max drawdown, estimated friction-adjusted MNQ dollars, news dependence, and a bootstrap estimate of the probability that mean R is positive.

A high backtest win rate with a small sample is treated as weak evidence. A strategy that remains positive with a larger sample, reasonable costs, and tolerable drawdown is preferred even with a lower win rate.

## Data caveat

The first automated six-month run uses a public NAS100 one-minute proxy spanning March 26 through September 25, 2026. It is useful for comparative signal research but is not suitable for declaring broker-ready MNQ profitability. Before live use, the exact same code should be rerun on CME MNQ/NQ futures data with contract-roll handling and broker-specific transaction costs.
